#!/bin/bash

# Submit the Spark streaming job
/opt/bitnami/spark/bin/spark-submit \
  --master spark://spark:7077 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0 \
  /opt/spark_streaming/spark_stream_v2.py
