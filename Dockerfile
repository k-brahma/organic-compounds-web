# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for RDKit and other packages
RUN apt-get update && apt-get install -y \
    libxrender1 \
    libxext6 \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install RDKit from conda-forge (more reliable for RDKit)
RUN pip install --upgrade pip && \
    pip install rdkit streamlit py3Dmol pandas numpy matplotlib plotly

# Copy all application files
COPY . .

# Expose Streamlit default port
EXPOSE 8501

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]