# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV DEBIAN_FRONTEND=noninteractive
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project (with namespace)
COPY ./ratatoskr ./ratatoskr
COPY config.yaml ./

# Set an optional environment variable for configuration
ARG RATATOSKR_CONFIG=/app/config.yaml
ENV RATATOSKR_CONFIG=${RATATOSKR_CONFIG}

# Expose the port your application will run on
EXPOSE 8000

# Start the FastAPI application with Uvicorn (using the namespace)
CMD ["uvicorn", "ratatoskr.main:app", "--host", "0.0.0.0", "--port", "6666"]
