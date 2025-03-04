FROM flyio/litefs:0.5 as litefs
FROM python:3.9-slim
# Copy LiteFS binary
COPY --from=litefs /usr/local/bin/litefs /usr/local/bin/litefs
WORKDIR /app
# Install system dependencies including build essentials for tiktoken
RUN apt-get update && apt-get install -y \
    sqlite3 \
    fuse3 \
    ca-certificates \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*
# Create necessary directories
RUN mkdir -p /data /litefs
# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy the static directory first
COPY static /app/static
COPY . .
COPY litefs.yml /etc/litefs.yml
# Default Streamlit configuration
ENV STREAMLIT_SERVER_PORT=8081 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0
# The entrypoint script will be provided by Fly.io
ENTRYPOINT ["litefs", "mount", "--"]
CMD ["streamlit", "run", "app.py"]