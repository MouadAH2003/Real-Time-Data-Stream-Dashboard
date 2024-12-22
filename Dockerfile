FROM python:3.9-slim

WORKDIR /app

# Install required packages for all services
COPY requirements.producer.txt requirements.consumer.txt requirements.dashboard.txt ./

RUN pip install -r requirements.producer.txt \
    && pip install -r requirements.consumer.txt \
    && pip install -r requirements.dashboard.txt

# Copy all Python files and data
COPY *.py ./
COPY *.csv ./

# The specific Python script to run will be specified in docker-compose.yml
CMD ["python"]
