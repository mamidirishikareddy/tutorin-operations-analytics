# Use a slim Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system-level dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libglib2.0-0 \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Streamlit frontend + models + i18n
COPY ui/ ./ui/
COPY models/ ./models/
COPY ui/i18n_helper.py ./ui/i18n_helper.py

# Optionally include chatbot or langchain folders if used
COPY chatbot/ ./chatbot/

# Copy any shared app modules Streamlit relies on
COPY app/schemas.py ./app/schemas.py
COPY app/db.py ./app/db.py
COPY app/models.py ./app/models.py
COPY app/crud.py ./app/crud.py

# Expose Streamlit port
EXPOSE 8501

# Set Streamlit environment variables
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ENABLECORS=false
ENV STREAMLIT_SERVER_ENABLEXSRFPROTECTION=false

# Launch Streamlit app
CMD ["streamlit", "run", "ui/streamlit_app.py", "--server.port=8501", "--server.enableCORS=false"]

