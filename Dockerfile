# Use Python 3.10 slim image without platform specification
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy the entire application first
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables for Streamlit
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_PORT=80
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_MAX_UPLOAD_SIZE=5

# Command to run the application
# ENTRYPOINT ["streamlit", "run", "--server.address=0.0.0.0", "--server.port=80", "app.py"]