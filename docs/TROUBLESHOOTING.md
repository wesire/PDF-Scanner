# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with PDF Context Narrator.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Configuration Issues](#configuration-issues)
3. [Runtime Errors](#runtime-errors)
4. [Performance Issues](#performance-issues)
5. [Data Issues](#data-issues)
6. [UI Issues](#ui-issues)
7. [Logging and Debugging](#logging-and-debugging)
8. [Common Error Messages](#common-error-messages)

## Installation Issues

### Problem: `ModuleNotFoundError: No module named 'pdf_context_narrator'`

**Cause**: Package not installed or not in Python path

**Solution**:
```bash
# Install in development mode
pip install -e .

# Or install normally
pip install .

# Verify installation
python -c "import pdf_context_narrator; print('OK')"
```

### Problem: `ImportError: cannot import name 'X' from 'Y'`

**Cause**: Incompatible dependency versions

**Solution**:
```bash
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall

# Check for conflicts
pip check
```

### Problem: `pip install` fails with permission errors

**Cause**: Insufficient permissions or system Python

**Solution**:
```bash
# Use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Or use --user flag
pip install --user -r requirements.txt
```

### Problem: Python version mismatch

**Cause**: Python version < 3.11

**Solution**:
```bash
# Check Python version
python --version

# Install Python 3.11+ and create virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration Issues

### Problem: Configuration file not found

**Cause**: Profile or config file doesn't exist

**Solution**:
```bash
# Check if profile exists
ls configs/

# Use existing profile
python -m pdf_context_narrator --profile local ingest ./pdfs/

# Or create custom config
cp configs/local.yaml configs/myconfig.yaml
# Edit myconfig.yaml
python -m pdf_context_narrator --config configs/myconfig.yaml ingest ./pdfs/
```

### Problem: Environment variables not loaded

**Cause**: `.env` file missing or not in correct location

**Solution**:
```bash
# Copy example file
cp .env.example .env

# Edit .env with your settings
nano .env

# Verify environment variables
python -c "from pdf_context_narrator.config import get_settings; print(get_settings())"
```

### Problem: Invalid configuration values

**Cause**: Configuration validation failed

**Solution**:
```bash
# Check configuration syntax
python -c "from pdf_context_narrator.config import Settings; s = Settings()"

# Enable debug mode to see validation errors
export PDF_CN_DEBUG=true
python -m pdf_context_narrator --verbose ingest ./pdfs/
```

### Problem: Permissions error on data directories

**Cause**: Cannot create or write to data/cache/logs directories

**Solution**:
```bash
# Check directory permissions
ls -la data/ cache/ logs/

# Create directories manually with correct permissions
mkdir -p data cache logs
chmod 755 data cache logs

# Or change directory location
export PDF_CN_DATA_DIR=/path/to/writable/dir
export PDF_CN_CACHE_DIR=/path/to/writable/cache
export PDF_CN_LOGS_DIR=/path/to/writable/logs
```

## Runtime Errors

### Problem: Command hangs or doesn't respond

**Cause**: Long-running operation or deadlock

**Solution**:
```bash
# Enable verbose logging to see progress
python -m pdf_context_narrator --verbose ingest ./pdfs/

# Check system resources
top  # or htop

# Reduce worker count if resource-constrained
export PDF_CN_MAX_WORKERS=2
python -m pdf_context_narrator ingest ./pdfs/
```

### Problem: Out of memory errors

**Cause**: Processing large PDFs or too many workers

**Solution**:
```bash
# Reduce workers
export PDF_CN_MAX_WORKERS=1
export PDF_CN_BATCH_SIZE=5

# Process files one at a time
for pdf in pdfs/*.pdf; do
    python -m pdf_context_narrator ingest "$pdf"
done

# Increase system swap space (Linux)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Problem: Timeout errors

**Cause**: Network timeout or slow operations

**Solution**:
```bash
# Check network connectivity
ping api.example.com

# Use offline profile
python -m pdf_context_narrator --profile offline ingest ./pdfs/

# Increase timeout in configuration
# Edit .env or config file:
# PDF_CN_TIMEOUT=300
```

## Performance Issues

### Problem: Slow ingestion

**Cause**: Large PDFs, low resources, or inefficient processing

**Solution**:
```bash
# Enable caching to avoid reprocessing
export PDF_CN_CACHE_DIR=cache

# Increase workers (if resources available)
export PDF_CN_MAX_WORKERS=8

# Use batch processing
export PDF_CN_BATCH_SIZE=20

# Profile the application
python -m cProfile -o profile.stats -m pdf_context_narrator ingest ./pdfs/
```

### Problem: Slow searches

**Cause**: Large index or unoptimized queries

**Solution**:
```bash
# Rebuild index
python -m pdf_context_narrator ingest ./pdfs/ --force

# Use more specific search queries
python -m pdf_context_narrator search "exact phrase" --limit 10

# Clear old cache
rm -rf cache/*
```

### Problem: High disk usage

**Cause**: Large cache or accumulated data

**Solution**:
```bash
# Check disk usage
du -sh data/ cache/ logs/

# Clear cache
rm -rf cache/*

# Configure cache size limits
export PDF_CN_CACHE_MAX_SIZE=1000  # MB

# Use cloud storage for large datasets
python -m pdf_context_narrator --profile cloud ingest ./pdfs/
```

## Data Issues

### Problem: Documents not found after ingestion

**Cause**: Ingestion failed silently or data corruption

**Solution**:
```bash
# Re-ingest with force flag
python -m pdf_context_narrator ingest ./pdfs/ --force --verbose

# Check logs for errors
tail -f logs/app.log

# Verify data directory
ls -la data/
```

### Problem: Search returns no results

**Cause**: Index not built or query mismatch

**Solution**:
```bash
# Verify documents are ingested
python -m pdf_context_narrator export json output.json
cat output.json

# Use broader search terms
python -m pdf_context_narrator search "term" --limit 100

# Rebuild index
python -m pdf_context_narrator ingest ./pdfs/ --force
```

### Problem: Corrupted data or index

**Cause**: Interrupted processing or disk issues

**Solution**:
```bash
# Backup existing data
cp -r data data.backup

# Clear and rebuild
rm -rf data/* cache/*
python -m pdf_context_narrator ingest ./pdfs/

# Check disk health
sudo smartctl -a /dev/sda  # Linux
# or use Disk Utility on macOS
```

## UI Issues

### Problem: Streamlit UI won't start

**Cause**: Streamlit not installed or port conflict

**Solution**:
```bash
# Install Streamlit dependencies
pip install -r requirements-streamlit.txt

# Try different port
streamlit run streamlit_app/app.py --server.port 8502

# Check for port conflicts
lsof -i :8501  # Linux/macOS
netstat -ano | findstr :8501  # Windows
```

### Problem: UI shows "Connection error"

**Cause**: Backend not running or network issue

**Solution**:
```bash
# Ensure backend is accessible
python -m pdf_context_narrator --help

# Check firewall settings
# Allow connections on port 8501

# Run with different network settings
streamlit run streamlit_app/app.py --server.address localhost
```

### Problem: File upload fails in UI

**Cause**: File size limits or permissions

**Solution**:
```bash
# Increase upload size limit
streamlit run streamlit_app/app.py --server.maxUploadSize 200

# Check file permissions
ls -la /path/to/upload/file.pdf

# Use CLI for large files
python -m pdf_context_narrator ingest /path/to/large/file.pdf
```

## Logging and Debugging

### Enable Debug Logging

```bash
# Method 1: Command line flag
python -m pdf_context_narrator --verbose ingest ./pdfs/

# Method 2: Environment variable
export PDF_CN_LOG_LEVEL=DEBUG
python -m pdf_context_narrator ingest ./pdfs/

# Method 3: Configuration file
# Edit .env:
# PDF_CN_LOG_LEVEL=DEBUG
```

### Enable Structured Logging

```bash
# For easier log parsing and analysis
python -m pdf_context_narrator --structured-logs ingest ./pdfs/

# Pipe to jq for formatting
python -m pdf_context_narrator --structured-logs ingest ./pdfs/ 2>&1 | jq .
```

### Check Log Files

```bash
# View log file
tail -f logs/app.log

# Search for errors
grep ERROR logs/app.log

# View last 100 lines
tail -100 logs/app.log

# Monitor in real-time with filtering
tail -f logs/app.log | grep -i error
```

### Capture Detailed Error Information

```bash
# Run with verbose and save output
python -m pdf_context_narrator --verbose ingest ./pdfs/ 2>&1 | tee debug.log

# Include Python tracebacks
python -m pdf_context_narrator ingest ./pdfs/ 2>&1 | tee -a debug.log

# With structured logs for analysis
python -m pdf_context_narrator --structured-logs ingest ./pdfs/ 2>&1 > structured.log
```

## Common Error Messages

### `FileNotFoundError: [Errno 2] No such file or directory`

**Meaning**: Referenced file or directory doesn't exist

**Solution**: 
- Verify the path is correct
- Use absolute paths
- Check file permissions

### `PermissionError: [Errno 13] Permission denied`

**Meaning**: Insufficient permissions to read/write file

**Solution**:
- Check file/directory permissions
- Run with appropriate user
- Use sudo if necessary (not recommended)

### `TypeError: 'NoneType' object is not subscriptable`

**Meaning**: Accessing None value

**Solution**:
- Enable debug logging
- Check configuration values
- Report bug with debug logs

### `ConnectionError: Unable to connect to service`

**Meaning**: Cannot reach external service

**Solution**:
- Check network connectivity
- Verify API endpoints
- Use offline profile if no internet

### `ValidationError: X validation error(s)`

**Meaning**: Configuration validation failed

**Solution**:
- Check configuration syntax
- Verify all required fields
- Check data types match

## Getting Help

### Collect Debug Information

Before reporting issues, collect:

```bash
# System information
python --version
pip list
uname -a  # Linux/macOS
systeminfo  # Windows

# Application configuration
python -c "from pdf_context_narrator.config import get_settings; print(get_settings())"

# Recent logs
tail -50 logs/app.log

# Disk space
df -h
```

### Report an Issue

Include:
1. **Error message** (full traceback)
2. **Steps to reproduce**
3. **System information**
4. **Configuration** (remove sensitive data)
5. **Log excerpts**

### Community Support

- GitHub Issues: https://github.com/wesire/PDF-Scanner/issues
- Discussions: https://github.com/wesire/PDF-Scanner/discussions
- Documentation: Check README.md and docs/

### Emergency Fixes

If you need to quickly get unblocked:

```bash
# Reset to clean state
rm -rf data/ cache/ logs/
pip uninstall pdf-context-narrator
pip install -e .

# Use defaults
unset $(env | grep PDF_CN_ | cut -d= -f1)
python -m pdf_context_narrator ingest ./pdfs/

# Minimal configuration
python -m pdf_context_narrator --profile local ingest ./pdfs/
```

## Preventive Measures

### Regular Maintenance

```bash
# Clear old cache regularly
find cache/ -mtime +7 -delete

# Rotate logs
logrotate -f /etc/logrotate.conf

# Update dependencies
pip install --upgrade -r requirements.txt
```

### Health Checks

```bash
# Verify installation
python -c "import pdf_context_narrator; print('OK')"

# Check configuration
python -m pdf_context_narrator --help

# Test basic operation
python -m pdf_context_narrator search "test" || echo "Search failed"
```

### Backup Strategy

```bash
# Backup data regularly
tar -czf backup-$(date +%Y%m%d).tar.gz data/ configs/ .env

# Automate with cron (Linux)
# Add to crontab:
# 0 2 * * * tar -czf ~/backups/pdf-cn-$(date +\%Y\%m\%d).tar.gz ~/pdf-scanner/data/
```
