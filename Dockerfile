# Use an official Python base image
FROM python:3.11-slim

# Install ffmpeg and other dependencies
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables if needed (optional here)
ENV PYTHONUNBUFFERED=1

# Run your bot
CMD ["python", "bot.py"]
