# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Copy the requirements.txt first to install dependencies
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the required files (including the data cleaning script)
COPY . .

# Command to run FastAPI using uvicorn server
CMD ["uvicorn", "main:app"]