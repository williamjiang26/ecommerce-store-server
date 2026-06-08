FROM python:3.11-slim

# 2. Set environment configurations to optimize Python inside Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set the working directory inside the container
WORKDIR /app

# 4. Install system dependencies needed for compiler compilation (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Copy over requirements first to leverage Docker's caching mechanism
COPY requirements.txt .

# 6. Install Python package dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 7. Copy the rest of your application code into the container workspace
COPY . .

# Expose the internal container port for Chat (GraphQL)
EXPOSE 8001

# Run the chat server on port 8001 inside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]