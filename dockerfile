FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create default directories
RUN mkdir -p requirements output

# Environment variables
ENV REQUIREMENTS_DIR=/app/requirements
ENV OUTPUT_DIR=/app/output

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]