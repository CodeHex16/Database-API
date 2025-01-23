FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy application files into the container
COPY ./api/db /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (if needed)
EXPOSE 5001

# Start the application
CMD ["python", "app.py"]
