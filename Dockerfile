# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (for SQLite and other utilities)
RUN apt-get update && apt-get install -y \
    build-essential \
    libsqlite3-dev

# Copy the requirements.txt first to install dependencies
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the required files (including the data cleaning script)
COPY . /app

# Run the data cleaning script first to generate data.db
RUN python DataCleaningSetUp.py

# Expose port 8000 for FastAPI
EXPOSE 8000

# Command to run FastAPI using uvicorn server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]