FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set a working directory inside the container
ENV APP_HOME /app
WORKDIR $APP_HOME

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev gcc && \
    apt-get clean

# Copy only requirements first to leverage Docker cache
COPY requirements.txt /app

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire project code into the container
COPY . /app
EXPOSE 8080

CMD ["python", "run.py"]