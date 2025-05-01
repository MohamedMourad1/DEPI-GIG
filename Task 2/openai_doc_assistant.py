import os
import time
import json
import glob
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("assistant_log.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class DocumentSearchAssistant:
    def __init__(self, api_key=None, assistant_name="Document Search Assistant"):
        """
        Initialize the Document Search Assistant.
        
        Args:
            api_key (str, optional): OpenAI API key. Defaults to None and uses env variable.
            assistant_name (str, optional): Name for the assistant. Defaults to "Document Search Assistant".
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set it in .env file or pass as parameter.")
            
        self.client = OpenAI(api_key=self.api_key)
        self.assistant_name = assistant_name
        self.assistant_id = None
        self.thread_id = None
        self.uploaded_file_ids = []
        
        logger.info(f"DocumentSearchAssistant initialized with name: {assistant_name}")
    
    def upload_files(self, documents_dir, file_pattern="*.docx"):
        """
        Upload all matching files from the specified directory to OpenAI.
        
        Args:
            documents_dir (str): Directory containing documents to upload
            file_pattern (str, optional): File pattern to match. Defaults to "*.docx".
            
        Returns:
            list: List of file IDs that were uploaded
        """
        file_paths = glob.glob(os.path.join(documents_dir, file_pattern))
        
        if not file_paths:
            logger.warning(f"No files matching '{file_pattern}' found in '{documents_dir}'")
            return []
        
        logger.info(f"Found {len(file_paths)} files matching pattern '{file_pattern}'")
        
        # Upload each file to OpenAI
        for file_path in tqdm(file_paths, desc="Uploading files"):
            try:
                with open(file_path, "rb") as file:
                    filename = os.path.basename(file_path)
                    response = self.client.files.create(
                        file=file,
                        purpose="assistants"
                    )
                    self.uploaded_file_ids.append(response.id)
                    logger.info(f"Successfully uploaded file: {filename} (ID: {response.id})")
            except Exception as e:
                logger.error(f"Error uploading file {file_path}: {str(e)}")
        
        logger.info(f"Total files uploaded: {len(self.uploaded_file_ids)}")
        return self.uploaded_file_ids
    
    def create_assistant(self, model="gpt-4-turbo", instructions=None):
        """
        Create an OpenAI assistant with file search capabilities.
        
        Args:
            model (str, optional): OpenAI model to use. Defaults to "gpt-4-turbo".
            instructions (str, optional): Custom instructions for the assistant.
            
        Returns:
            str: Assistant ID
        """
        if not instructions:
            instructions = (
                "You are a document search assistant that answers questions based on the content "
                "of uploaded documents. Respond with detailed answers and cite specific sections "
                "from the documents when possible. If information cannot be found in the documents, "
                "clearly state that fact."
            )
        
        try:
            response = self.client.beta.assistants.create(
                name=self.assistant_name,
                instructions=instructions,
                model=model,
                tools=[{"type": "retrieval"}],
                file_ids=self.uploaded_file_ids
            )
            
            self.assistant_id = response.id
            logger.info(f"Assistant created successfully with ID: {self.assistant_id}")
            return self.assistant_id
            
        except Exception as e:
            logger.error(f"Error creating assistant: {str(e)}")
            raise
    
    def create_thread(self):
        """
        Create a new thread for conversation.
        
        Returns:
            str: Thread ID
        """
        try:
            response = self.client.beta.threads.create()
            self.thread_id = response.id
            logger.info(f"Thread created successfully with ID: {self.thread_id}")
            return self.thread_id
        except Exception as e:
            logger.error(f"Error creating thread: {str(e)}")
            raise
    
    def ask_question(self, question, timeout=300):
        """
        Ask a question to the assistant and get the response.
        
        Args:
            question (str): Question to ask
            timeout (int, optional): Maximum time to wait for response in seconds. Defaults to 300.
            
        Returns:
            str: Assistant's response
        """
        if not self.assistant_id:
            raise ValueError("Assistant not created. Call create_assistant() first.")
        if not self.thread_id:
            raise ValueError("Thread not created. Call create_thread() first.")
        
        try:
            # Add the message to the thread
            message = self.client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content=question
            )
            
            logger.info(f"Message sent: {question}")
            
            # Run the assistant
            run = self.client.beta.threads.runs.create(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id
            )
            
            # Wait for completion
            start_time = time.time()
            while time.time() - start_time < timeout:
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread_id,
                    run_id=run.id
                )
                
                if run_status.status == "completed":
                    break
                elif run_status.status in ["failed", "cancelled", "expired"]:
                    logger.error(f"Run failed with status: {run_status.status}")
                    return f"Error: Run {run_status.status}. Please try again."
                
                time.sleep(1)
            
            if time.time() - start_time >= timeout:
                logger.warning(f"Timeout reached waiting for response")
                return "Error: Request timed out. Please try again with a simpler question."
            
            # Get the assistant's response
            messages = self.client.beta.threads.messages.list(
                thread_id=self.thread_id
            )
            
            # The latest assistant message will be the first one with role='assistant'
            for msg in messages.data:
                if msg.role == "assistant":
                    response_text = msg.content[0].text.value
                    logger.info(f"Response received (length: {len(response_text)})")
                    return response_text
            
            return "No response received from assistant."
            
        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            return f"Error: {str(e)}"
    
    def process_questions(self, questions):
        """
        Process a list of questions sequentially.
        
        Args:
            questions (list): List of questions to ask
            
        Returns:
            dict: Dictionary mapping questions to answers
        """
        if not isinstance(questions, list):
            questions = [questions]
        
        results = {}
        
        for i, question in enumerate(questions, 1):
            logger.info(f"Processing question {i}/{len(questions)}")
            answer = self.ask_question(question)
            results[question] = answer
        
        return results
    
    def cleanup(self):
        """
        Clean up resources by deleting uploaded files.
        
        Returns:
            bool: True if cleanup was successful
        """
        success = True
        
        for file_id in self.uploaded_file_ids:
            try:
                self.client.files.delete(file_id=file_id)
                logger.info(f"Deleted file with ID: {file_id}")
            except Exception as e:
                logger.error(f"Error deleting file {file_id}: {str(e)}")
                success = False
        
        logger.info("Cleanup completed")
        return success


def main():
    """
    Main function to demonstrate the Document Search Assistant.
    """
    # Configuration
    documents_dir = "documents"  # Directory containing the documents
    questions = [
        "What are the key points in the first document?",
        "Summarize the content about project management in the documents.",
        "What recommendations are made in the documents?",
    ]
    
    try:
        # Initialize the assistant
        assistant = DocumentSearchAssistant()
        
        # Upload documents
        logger.info(f"Uploading documents from directory: {documents_dir}")
        file_ids = assistant.upload_files(documents_dir)
        
        if not file_ids:
            logger.error("No files were uploaded. Exiting.")
            return
        
        # Create assistant
        assistant.create_assistant(
            instructions="You are a helpful research assistant that answers questions based on the provided documents. "
                        "Always cite the specific document and section when you provide information. "
                        "If the information is not in the documents, clearly state that fact."
        )
        
        # Create thread
        assistant.create_thread()
        
        # Process questions
        logger.info(f"Processing {len(questions)} questions")
        results = assistant.process_questions(questions)
        
        # Print results
        for question, answer in results.items():
            print(f"\nQ: {question}")
            print(f"A: {answer}")
            print("-" * 80)
        
        # Optional: Save results to file
        with open("results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        # Cleanup
        assistant.cleanup()
        
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")


if __name__ == "__main__":
    main()
