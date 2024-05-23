# Build stage
FROM python:3.10-slim AS builder
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Create a virtual environment and activate it
RUN python -m venv .venv
ENV PATH="/app/.venv/bin:${PATH}"

# Install requirements and dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm
RUN playwright install

# Production stage
FROM python:3.10-slim
WORKDIR /app

# Copy the .venv and the rest of the project
COPY --from=builder /app/.venv /app/.venv
COPY . .

# Set environment variable
ARG RATATOSKR_CONFIG=/app/config.yaml
ENV PATH="/app/.venv/bin:${PATH}"

# Expose port and start command
EXPOSE 6666
CMD ["/app/.venv/bin/python", "src/main.py"] 