from kafka import KafkaProducer
import json
import pandas as pd
import time
from datetime import datetime
import logging
import os

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

    def process_bitcoin_data(self, filepath):
        """Process Bitcoin data from CSV file with better error handling"""
        try:
            # Check if file exists
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Data file not found at {filepath}")

            logger.info(f"Reading data from {filepath}")
            df = pd.read_csv(filepath)

            # Verify required columns exist
            required_columns = ['Date', 'Price', 'Open', 'High', 'Low', 'Vol.', 'Change %']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")

            # Handle numeric columns
            numeric_columns = ['Price', 'Open', 'High', 'Low']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce')

            # Parse Volume
            def parse_volume(vol):
                if pd.isna(vol):
                    return 0.0
                if isinstance(vol, str):
                    try:
                        vol = vol.strip()
                        if 'K' in vol:
                            return float(vol.replace('K', '')) * 1e3
                        elif 'M' in vol:
                            return float(vol.replace('M', '')) * 1e6
                        elif 'B' in vol:
                            return float(vol.replace('B', '')) * 1e9
                        return float(vol.replace(',', ''))
                    except ValueError:
                        logger.warning(f"Could not parse volume value: {vol}")
                        return 0.0
                return float(vol)

            df['Vol.'] = df['Vol.'].apply(parse_volume)
            df['Change %'] = pd.to_numeric(df['Change %'].str.replace('%', ''), errors='coerce')
            df['Date'] = pd.to_datetime(df['Date'])

            # Remove any rows with NaN values
            df = df.dropna()

            logger.info(f"Successfully processed {len(df)} rows of data")
            return df.sort_values('Date')

        except Exception as e:
            logger.error(f"Error processing data file: {str(e)}")
            raise

    def start_streaming(self, filepath, delay=1.0):
        """Start streaming data with better error handling"""
        try:
            df = self.process_bitcoin_data(filepath)
            logger.info(f"Starting to stream {len(df)} records")

            for _, row in df.iterrows():
                try:
                    data = {
                        'timestamp': datetime.now().isoformat(),
                        'date': row['Date'].isoformat(),
                        'price': float(row['Price']),
                        'open': float(row['Open']),
                        'high': float(row['High']),
                        'low': float(row['Low']),
                        'volume': float(row['Vol.']),
                        'change_percent': float(row['Change %'])
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
    # Use correct path to your data file
    data_file = "./Bitcoin Historical Data.csv"

    if not os.path.exists(data_file):
        logger.error(f"Data file not found at {data_file}")
        logger.info("Please ensure your data file exists and update the path accordingly")
    else:
        producer = BitcoinDataProducer()
        producer.start_streaming(data_file)
