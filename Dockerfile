# Use an official Python runtime as a base image
FROM python:3.11

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file (if you have any dependencies) and install them
# COPY requirements.txt /app/
# RUN pip install --no-cache-dir -r requirements.txt

# Copy your Python script and data files to the container's working directory
COPY demo.py /app/
COPY db.yaml /app/
COPY AP1-Data.json /app/
COPY dummyData.json /app/

# Install necessary libraries
RUN pip install mysql-connector-python pyyaml

# Run your Python script when the container starts
CMD ["python", "demo.py"]
