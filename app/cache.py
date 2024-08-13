import bmemcached
import os
from dotenv import load_dotenv
from utils import setup_logging
import logging

load_dotenv()

setup_logging


try:
    memcached_client = bmemcached.Client(
        f"{os.getenv('MEMCACHED_HOST')}:{os.getenv('MEMCACHED_PORT')}",
        username=os.getenv('MEMCACHED_USERNAME'),
        password=os.getenv('MEMCACHED_PASSWORD')
    )
    logging.info("Memcached client initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize memcached client: {e}")
    memcached_client = None
