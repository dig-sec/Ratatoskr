# Use a slimmer base image for reduced size
FROM python:3.10-slim

# Set environment variables for non-interactive installations
ENV DEBIAN_FRONTEND=noninteractive
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Set the working directory in the container to /app
WORKDIR /app

# Copy only necessary files, not the entire project (Improved)
COPY requirements.txt ./

# Install dependencies before copying the rest of the project (Improved)
# This allows for better caching during image builds
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

# Copy the rest of your application code (Improved)
COPY . .

# Set an optional environment variable for configuration (Optional)
ARG RATATOSKR_CONFIG=/app/config.yaml
ENV RATATOSKR_CONFIG=${RATATOSKR_CONFIG}

# Expose the port your application will run on (If applicable)
EXPOSE 6666

# Set the command to run your application (Use a single entrypoint)
CMD ["python", "main.py", "--config", "$RATATOSKR_CONFIG"] 
