# metrics.py
import logging

cache_hits = 0
cache_misses = 0
api_calls = 0
successful_responses = 0
failed_responses = 0

# Function to log metrics
def log_metrics():
    metrics_logger = logging.getLogger('metrics_logger')
    metrics_logger.info(f"Cache Hits: {cache_hits}")
    metrics_logger.info(f"Cache Misses: {cache_misses}")
    metrics_logger.info(f"API Calls: {api_calls}")
    metrics_logger.info(f"Successful Responses: {successful_responses}")
    metrics_logger.info(f"Failed Responses: {failed_responses}")
