# OpenAI Assistant for Automated Q&A from Word Documents

This document outlines the steps to create an automated Q&A system using OpenAI's API to process Word documents.

## Features
- Extract text from Word documents.
- Generate questions and answers based on the content.
- Provide a user-friendly interface for interaction.

## Requirements
- Python 3.7+
- `openai` Python library
- `python-docx` for Word document processing

## Installation
```bash
pip install openai python-docx
```

## Usage
1. **Extract Text from Word Document**:
    Use `python-docx` to read the content of a `.docx` file.
    ```python
    from docx import Document

    def extract_text(file_path):
         doc = Document(file_path)
         return "\n".join([p.text for p in doc.paragraphs if p.text])
    ```

2. **Generate Q&A with OpenAI**:
    Use OpenAI's API to generate questions and answers.
    ```python
    import openai

    openai.api_key = "your-api-key"

    def generate_qa(text):
         response = openai.Completion.create(
              engine="text-davinci-003",
              prompt=f"Generate questions and answers from the following text:\n{text}",
              max_tokens=500
         )
         return response.choices[0].text.strip()
    ```

3. **Integrate the Workflow**:
    Combine text extraction and Q&A generation.
    ```python
    def process_document(file_path):
         text = extract_text(file_path)
         qa = generate_qa(text)
         return qa
    ```

4. **Run the Script**:
    ```python
    if __name__ == "__main__":
         file_path = "example.docx"
         print(process_document(file_path))
    ```

## Notes
- Ensure your OpenAI API key is securely stored.
- Test with various documents to fine-tune the prompt for better results.

## License
This project is licensed under the MIT License.