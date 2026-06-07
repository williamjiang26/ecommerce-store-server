FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the internal container port for Chat (GraphQL)
EXPOSE 8001

# Run the chat server on port 8001 inside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]