# Use official Python image as a base image
FROM python:3.10-slim

# Copy the local requirements.txt to the container
COPY requirements.txt .

# Install the necessary packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port that the Dash app will run on
EXPOSE 8050

# Run the Dash app
CMD ["python", "app.py"]