from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import logging
import os
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BitcoinSparkProcessor:
    def __init__(self):
        # Wait for Kafka to be ready
        self._wait_for_kafka()

        logger.info("Initializing Spark session...")
        self.spark = SparkSession.builder \
            .appName("BitcoinAnalytics") \
            .config("spark.jars.packages",
                    "org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0,"
                    "org.apache.kafka:kafka-clients:2.8.1") \
            .config("spark.sql.streaming.checkpointLocation", "/opt/spark_streaming/checkpoint") \
            .config("spark.driver.host", "localhost") \
            .getOrCreate()

        # Set log level
        self.spark.sparkContext.setLogLevel("WARN")
        logger.info("Spark session initialized successfully")

        # Define schema for incoming data
        self.schema = StructType([
            StructField("timestamp", StringType(), True),
            StructField("date", StringType(), True),
            StructField("price", DoubleType(), True),
            StructField("open", DoubleType(), True),
            StructField("high", DoubleType(), True),
            StructField("low", DoubleType(), True),
            StructField("volume", DoubleType(), True),
            StructField("change_percent", DoubleType(), True)
        ])

    def _wait_for_kafka(self, max_retries=30, retry_interval=10):
        """Wait for Kafka to be ready"""
        from kafka import KafkaConsumer
        from kafka.errors import NoBrokersAvailable

        retry_count = 0
        while retry_count < max_retries:
            try:
                logger.info("Attempting to connect to Kafka...")
                consumer = KafkaConsumer(
                    bootstrap_servers=['kafka:29092'],
                    api_version=(0, 10, 1),
                    request_timeout_ms=5000,
                    connections_max_idle_ms=10000
                )
                consumer.close()
                logger.info("Successfully connected to Kafka")
                return
            except Exception as e:
                retry_count += 1
                logger.warning(f"Kafka connection error: {e}. Retry {retry_count}/{max_retries}")
                time.sleep(retry_interval)

        raise Exception("Failed to connect to Kafka after maximum retries")

    def calculate_technical_indicators(self, df):
        """Calculate technical indicators using watermark and time-based windowing"""
        logger.info("Calculating technical indicators...")

        # Ensure timestamp is parsed correctly
        df = df.withColumn("timestamp", to_timestamp(col("timestamp"))) \
               .withWatermark("timestamp", "10 minutes")

        # Define time-based window for aggregations
        window_duration = "5 minutes"
        slide_duration = "1 minute"

        # Calculate Simple Moving Average (SMA)
        sma_df = df.groupBy(
            window(col("timestamp"), window_duration, slide_duration)
        ).agg(
            avg("price").alias("sma_20")
        ).select(
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            "sma_20"
        )

        # Calculate Bollinger Bands
        bb_df = df.groupBy(
            window(col("timestamp"), window_duration, slide_duration)
        ).agg(
            avg("price").alias("bb_middle"),
            stddev("price").alias("bb_std")
        ).select(
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            "bb_middle",
            "bb_std",
            (col("bb_middle") + (2 * col("bb_std"))).alias("bb_upper"),
            (col("bb_middle") - (2 * col("bb_std"))).alias("bb_lower")
        )

        logger.info("Technical indicators calculated successfully")
        return sma_df, bb_df

    def process_stream(self):
        """Process streaming data from Kafka"""
        try:
            logger.info("Starting stream processing...")

            # Read from Kafka
            logger.info("Reading from Kafka topic: bitcoin_data")
            df = self.spark \
                .readStream \
                .format("kafka") \
                .option("kafka.bootstrap.servers", "kafka:29092") \
                .option("subscribe", "bitcoin_data") \
                .option("startingOffsets", "earliest") \
                .option("failOnDataLoss", "false") \
                .option("kafka.group.id", "bitcoin-spark-processor") \
                .load()

            # Parse JSON data with error handling
            logger.info("Parsing JSON data...")
            parsed_df = df.select(
                from_json(
                    col("value").cast("string"),
                    self.schema,
                    options={"mode": "PERMISSIVE"}
                ).alias("data")
            ).select("data.*")

            # Calculate technical indicators
            sma_df, bb_df = self.calculate_technical_indicators(parsed_df)

            # Write processed data back to Kafka with comprehensive error handling
            logger.info("Writing processed data to Kafka...")

            # Write raw processed data
            query_processed = parsed_df \
                .selectExpr("to_json(struct(*)) AS value") \
                .writeStream \
                .outputMode("append") \
                .format("kafka") \
                .option("kafka.bootstrap.servers", "kafka:29092") \
                .option("topic", "bitcoin_processed") \
                .option("checkpointLocation", "/opt/spark_streaming/checkpoint/processed") \
                .option("failOnDataLoss", "false") \
                .start()

            # Write SMA data
            query_sma = sma_df \
                .selectExpr("to_json(struct(*)) AS value") \
                .writeStream \
                .outputMode("append") \
                .format("kafka") \
                .option("kafka.bootstrap.servers", "kafka:29092") \
                .option("topic", "bitcoin_sma") \
                .option("checkpointLocation", "/opt/spark_streaming/checkpoint/sma") \
                .option("failOnDataLoss", "false") \
                .start()

            # Write Bollinger Bands data
            query_bb = bb_df \
                .selectExpr("to_json(struct(*)) AS value") \
                .writeStream \
                .outputMode("append") \
                .format("kafka") \
                .option("kafka.bootstrap.servers", "kafka:29092") \
                .option("topic", "bitcoin_bb") \
                .option("checkpointLocation", "/opt/spark_streaming/checkpoint/bb") \
                .option("failOnDataLoss", "false") \
                .start()

            logger.info("All streams started successfully. Waiting for termination...")

            # Wait for all queries to terminate
            query_processed.awaitTermination()
            query_sma.awaitTermination()
            query_bb.awaitTermination()

        except Exception as e:
            logger.error(f"Error in stream processing: {str(e)}", exc_info=True)
            raise

def main():
    try:
        logger.info("Starting Bitcoin Spark Processor...")
        processor = BitcoinSparkProcessor()
        processor.process_stream()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
