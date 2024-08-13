import bmemcached
import os
from dotenv import load_dotenv

load_dotenv()

memcached_client = bmemcached.Client(
    f"{os.getenv('MEMCACHED_HOST')}:{os.getenv('MEMCACHED_PORT')}",
    username=os.getenv('MEMCACHED_USERNAME'),
    password=os.getenv('MEMCACHED_PASSWORD')
)
