# Bitcoin Analytics Dashboard

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Table of Contents

- [About](#about)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)
- [Acknowledgements](#acknowledgements)

## About

The Bitcoin Analytics Dashboard is a real-time data visualization tool that processes Bitcoin market data using Apache Kafka, Apache Spark, and Dash. It provides insights into Bitcoin price trends, technical indicators, and market status.

## Features

- Real-time data streaming and processing using Apache Kafka and Apache Spark.
- Visualization of Bitcoin price trends, moving averages, Bollinger Bands, and RSI using Dash.
- Export data to CSV for further analysis.
- Interactive and responsive dashboard design.
- Easy setup and deployment using Docker Compose.

## Getting Started

### Prerequisites

Before you begin, ensure you have met the following requirements:

- Docker and Docker Compose installed on your machine.

### Installation

1. **Clone the repository:**

   ```sh
   git clone https://github.com/MouadAH2003/BitcoinRealTimeDashboard.git
   cd BitcoinRealTimeDashboard
   ```

2. **Build and run the project using Docker Compose:**

   ```sh
   docker-compose up --build
   ```

   This command will build the Docker images and start the containers for Kafka, Spark, and the Dash dashboard.

## Usage

1. **Access the Dashboard:**

   Open your web browser and navigate to `http://localhost:8051/` to view the Bitcoin Analytics Dashboard.

2. **Stopping the Containers:**

   To stop the containers, you can use the following command:

   ```sh
   docker-compose down
   ```

## Architecture

The project follows a pipeline architecture consisting of the following components:

1. **Producer**: Sends Bitcoin data to a Kafka topic.
2. **Consumer**: Consumes data from the Kafka topic.
3. **Spark Streaming**: Processes the data from Kafka, calculates technical indicators, and writes the results to CSV files.
4. **Dashboard**: Fetches data from the processed CSV files and updates the dashboard in real-time.

## Contributing

NO Contribution available - 😒

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Mouad AIT HA------ [linkedin-profile](https://www.linkedin.com/in/mouad-ait-ha-67427521b/) - mouadaitha@gmail.com </br>

Mohamed LAKBAKBI-- [linkedin-profile](https://www.linkedin.com/in/lakbakbi-mohammed) - mohammedlakbakbi@gmail.com

Project Link: [https://github.com/MouadAH2003/BitcoinRealTimeDashboard](https://github.com/MouadAH2003/BitcoinRealTimeDashboard)



### Docker Compose File (docker-compose.yml)

```yaml
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"

  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"

  spark:
    image: bitnami/spark:3.2.0
    environment:
      - SPARK_MODE=master
      - SPARK_RPC_AUTHENTICATION_ENABLED=no
      - SPARK_RPC_ENCRYPTION_ENABLED=no
      - SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED=no
      - SPARK_SSL_ENABLED=no
    ports:
      - "8080:8080"
      - "7077:7077"
    volumes:
      - ./spark_stream_v2.py:/opt/spark_streaming/spark_stream_v2.py
      - ./spark_checkpoint:/opt/spark_streaming/checkpoint

  spark-worker:
    image: bitnami/spark:3.2.0
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark:7077
      - SPARK_WORKER_MEMORY=1G
      - SPARK_WORKER_CORES=1
      - SPARK_RPC_AUTHENTICATION_ENABLED=no
      - SPARK_RPC_ENCRYPTION_ENABLED=no
      - SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED=no
      - SPARK_SSL_ENABLED=no
    depends_on:
      - spark

  spark-submit:
    image: bitnami/spark:3.2.0
    command: >
      bash -c "
      pip install kafka-python pandas numpy &&
      /opt/bitnami/spark/bin/spark-submit 
      --master spark://spark:7077 
      --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0 
      --conf spark.streaming.kafka.maxRatePerPartition=100
      --conf spark.sql.shuffle.partitions=2
      --conf spark.executor.memory=1g
      --conf spark.driver.memory=1g
      /opt/spark_streaming/spark_stream_v2.py"
    volumes:
      - ./spark_stream_v2.py:/opt/spark_streaming/spark_stream_v2.py
      - ./spark_checkpoint:/opt/spark_streaming/checkpoint
    depends_on:
      - spark
      - kafka

  producer:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - .:/app
    command: python producer.py
    depends_on:
      - kafka

  consumer:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - .:/app
    command: python consumer.py
    depends_on:
      - kafka
      - spark-submit

  dashboard:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8051:8051"
    volumes:
      - .:/app
    command: python dashboard_2.py
    depends_on:
      - consumer

volumes:
  spark_checkpoint:
```

### Dockerfile

```Dockerfile
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

```

### Spark Script (run_spark.sh)

```sh
#!/bin/bash

# Start the Spark job
spark-submit --master local[*] /app/spark_streaming.py
```
