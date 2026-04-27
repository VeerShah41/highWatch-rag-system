FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PyMuPDF
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (CPU version to save space)
COPY requirements.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p storage downloads

# Expose port
EXPOSE 8000

# Run the app
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
