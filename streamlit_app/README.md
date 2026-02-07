# Streamlit UI Module

This directory contains an optional web interface for PDF Context Narrator built with Streamlit.

## Features

- **📥 Upload**: Upload and ingest PDF documents
- **🔍 Search**: Search through indexed documents
- **📖 Narrative View**: Generate narrative summaries from multiple documents
- **⚙️ Settings**: Configure application settings

## Installation

Install Streamlit dependencies:

```bash
pip install -r requirements-streamlit.txt
```

## Running the UI

```bash
streamlit run streamlit_app/app.py
```

The application will open in your browser at `http://localhost:8501`

## Usage

1. **Upload PDFs**: Navigate to the Upload view and select PDF files to ingest
2. **Search Documents**: Use the Search view to find relevant content
3. **View Narratives**: Generate comprehensive narratives from your documents
4. **Configure Settings**: Adjust application settings in the Settings view

## Notes

- This is a stub implementation showing the UI structure
- Business logic integration will be added in future releases
- The UI is designed to work with the main PDF Context Narrator CLI tool
