from kafka import KafkaConsumer
import json
import logging
import pandas as pd
import os
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BitcoinDataConsumer:
    def __init__(self, bootstrap_servers=['kafka:29092']):
        # Initialize DataFrames for different types of data
        self.price_df = pd.DataFrame()
        self.sma_df = pd.DataFrame()
        self.bb_df = pd.DataFrame()

        # Create consumers for different topics
        self.consumers = {
            'processed': self.create_consumer('bitcoin_processed', bootstrap_servers),
            'sma': self.create_consumer('bitcoin_sma', bootstrap_servers),
            'bb': self.create_consumer('bitcoin_bb', bootstrap_servers)
        }

    def create_consumer(self, topic, bootstrap_servers):
        """Create a Kafka consumer with retries"""
        retries = 0
        max_retries = 10

        while retries < max_retries:
            try:
                consumer = KafkaConsumer(
                    topic,
                    bootstrap_servers=bootstrap_servers,
                    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                    auto_offset_reset='earliest',
                    group_id=f'bitcoin_consumers_{topic}',
                    api_version=(0, 10, 1)
                )
                logger.info(f"Successfully connected to Kafka for topic: {topic}")
                return consumer
            except Exception as e:
                retries += 1
                logger.warning(f"Failed to connect to Kafka for topic {topic}. Attempt {retries}/{max_retries}")
                time.sleep(5)

        raise Exception(f"Failed to create consumer for topic {topic} after maximum retries")

    def process_message(self, message, topic):
        """Process individual message and store in appropriate DataFrame"""
        try:
            # Add timestamp for when we received the message
            data = message.value
            if isinstance(data, str):
                data = json.loads(data)

            data['processed_at'] = datetime.now().isoformat()

            # Store in appropriate DataFrame based on topic
            if topic == 'processed':
                self.price_df = pd.concat([self.price_df, pd.DataFrame([data])], ignore_index=True)
                logger.info(f"Processed price data: {data.get('date')} - Price: {data.get('price')}")
            elif topic == 'sma':
                self.sma_df = pd.concat([self.sma_df, pd.DataFrame([data])], ignore_index=True)
                logger.info(f"Processed SMA data: {data.get('window_start')} - SMA: {data.get('sma_20')}")
            elif topic == 'bb':
                self.bb_df = pd.concat([self.bb_df, pd.DataFrame([data])], ignore_index=True)
                logger.info(f"Processed BB data: {data.get('window_start')} - Middle: {data.get('bb_middle')}")

            return True
        except Exception as e:
            logger.error(f"Error processing message for topic {topic}: {str(e)}")
            return False

    def start_consuming(self):
        """Start consuming messages from all Kafka topics"""
        try:
            logger.info("Starting to consume messages from all topics...")

            while True:
                for topic, consumer in self.consumers.items():
                    # Non-blocking poll for messages
                    messages = consumer.poll(timeout_ms=100)
                    for tp, msgs in messages.items():
                        for message in msgs:
                            success = self.process_message(message, topic)
                            if not success:
                                logger.warning(f"Failed to process message from topic {topic}, continuing...")

                # Small sleep to prevent CPU overuse
                time.sleep(0.1)

        except KeyboardInterrupt:
            logger.info("Received shutdown signal, closing consumers...")
        except Exception as e:
            logger.error(f"Error in consumer: {str(e)}")
        finally:
            for consumer in self.consumers.values():
                consumer.close()

    def get_latest_data(self, data_type='price', limit=100):
        """Retrieve latest data from specified DataFrame"""
        try:
            if data_type == 'price':
                return self.price_df.tail(limit)
            elif data_type == 'sma':
                return self.sma_df.tail(limit)
            elif data_type == 'bb':
                return self.bb_df.tail(limit)
            else:
                logger.error(f"Unknown data type: {data_type}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error retrieving {data_type} data: {str(e)}")
            return pd.DataFrame()

if __name__ == "__main__":
    try:
        consumer = BitcoinDataConsumer()
        consumer.start_consuming()
    except KeyboardInterrupt:
        logger.info("Shutting down consumer...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
