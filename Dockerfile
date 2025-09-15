# Base image with Python
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements (if you have one)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
    


# Copy your code and data into container
COPY . .

# Command to run app.py
CMD ["python", "app.py"]
