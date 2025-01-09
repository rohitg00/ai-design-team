# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy the entire application first
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLE_WEBSOCKET_COMPRESSION=true
ENV STREAMLIT_SERVER_RUN_ON_SAVE=false
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Let Sevalla handle the port
ENV STREAMLIT_SERVER_PORT=$PORT

# Command to run the application
CMD ["streamlit", "run", "app.py"]