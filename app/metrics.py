import logging

class Metrics:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Metrics, cls).__new__(cls)
            cls._instance.cache_hits = 0
            cls._instance.cache_misses = 0
            cls._instance.api_calls = 0
            cls._instance.successful_responses = 0
            cls._instance.failed_responses = 0
        return cls._instance

    def log_metrics(self):
        logging.info(f"Logging Metrics - Cache Hits: {self.cache_hits}")
        logging.info(f"Logging Metrics - Cache Misses: {self.cache_misses}")
        logging.info(f"Logging Metrics - API Calls: {self.api_calls}")
        logging.info(f"Logging Metrics - Successful Responses: {self.successful_responses}")
        logging.info(f"Logging Metrics - Failed Responses: {self.failed_responses}")

metrics = Metrics()
