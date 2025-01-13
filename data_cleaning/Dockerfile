# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Copy the requirements.txt first to install dependencies
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the required files (including the data cleaning script)
COPY . .

# Run the data cleaning script first to generate data.db
CMD ["python", "DataCleaningSetUp.py"]