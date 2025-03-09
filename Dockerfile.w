# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.10-slim

EXPOSE 8001

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY . /app

# Install gcc and python3-dev
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    # Cleaning up
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r full_flow/runtime_server/worker/requirements.txt

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "-k", "uvicorn.workers.UvicornWorker", "full_flow.runtime_server.worker.main:app"]
