FROM python:3.11

WORKDIR /app
COPY . /app

ENV STREAMLIT_WATCHER_TYPE=none

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Expose Streamlit default port
EXPOSE 8501

# Launch the app
CMD ["streamlit", "run", "index.py"]