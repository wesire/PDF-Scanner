# Configuration Files

This directory is for storing configuration files for the PDF Context Narrator application.

## Purpose

- Store environment-specific configurations
- YAML/JSON configuration files for different deployments
- API key configurations (ensure these are gitignored)

## Usage

Configuration files in this directory can be loaded using the `--config` flag:

```bash
python -m pdf_context_narrator --config configs/production.yaml ingest ./pdfs/
```
