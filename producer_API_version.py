from kafka import KafkaProducer
import json
import time
from datetime import datetime
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BitcoinDataProducer:
    def __init__(self, bootstrap_servers=['kafka:29092'], topic='bitcoin_data'):
        # Try to connect to Kafka with retries
        connected = False
        retries = 0
        max_retries = 10

        while not connected and retries < max_retries:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    api_version=(0, 10, 1)
                )
                connected = True
                logger.info("Successfully connected to Kafka")
            except Exception as e:
                retries += 1
                logger.warning(f"Failed to connect to Kafka. Attempt {retries}/{max_retries}")
                time.sleep(5)  # Wait before retrying

        if not connected:
            raise Exception("Failed to connect to Kafka after maximum retries")

        self.topic = topic

    def fetch_bitcoin_data(self):
        """Fetch Bitcoin data from CryptoCompare API"""
        try:
            url = 'https://min-api.cryptocompare.com/data/v2/histoday'
            params = {
                'fsym': 'BTC',
                'tsym': 'USD',
                'limit': 2000  # Maximum limit for free plan
            }
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json()

            # Extract relevant data
            historical_data = data['Data']['Data']

            # Combine data into a list of dictionaries
            combined_data = []
            for entry in historical_data:
                combined_data.append({
                    'Date': datetime.fromtimestamp(entry['time']).isoformat(),
                    'Price': entry['close'],
                    'Open': entry['open'],
                    'High': entry['high'],
                    'Low': entry['low'],
                    'Volume': entry['volumeto']
                })

            logger.info(f"Successfully fetched {len(combined_data)} rows of data from CryptoCompare API")
            return combined_data

        except Exception as e:
            logger.error(f"Error fetching data from CryptoCompare API: {str(e)}")
            raise

    def start_streaming(self, delay=1.0):
        """Start streaming data with better error handling"""
        try:
            data = self.fetch_bitcoin_data()
            logger.info(f"Starting to stream {len(data)} records")

            for entry in data:
                try:
                    data = {
                        'timestamp': datetime.now().isoformat(),
                        'date': entry['Date'],
                        'price': float(entry['Price']),
                        'open': float(entry['Open']),
                        'high': float(entry['High']),
                        'low': float(entry['Low']),
                        'volume': float(entry['Volume'])
                    }

                    self.producer.send(self.topic, value=data)
                    logger.info(f"Sent data: {data['date']} - Price: {data['price']}")
                    time.sleep(delay)

                except Exception as e:
                    logger.error(f"Error sending record: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error in data streaming: {str(e)}")
        finally:
            self.producer.close()

if __name__ == "__main__":
    producer = BitcoinDataProducer()
    producer.start_streaming()
