FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the internal container port for Products (REST)
EXPOSE 8001

# Run the product server on port 8001 inside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
