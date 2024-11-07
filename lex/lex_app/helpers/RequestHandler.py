import requests
from requests.exceptions import RequestException
import time
from typing import Optional, Dict, Any



class RequestHandler:
    def __init__(self, max_retries: int = 3, timeout: int = 10, retry_delay: int = 2):
        self.max_retries = max_retries
        self.timeout = timeout
        self.retry_delay = retry_delay

    def post_with_retry(self, url: str, data: Dict[str, Any]) -> Optional[requests.Response]:
        for attempt in range(self.max_retries):
            try:
                response = requests.post(url, json=data, timeout=self.timeout)
                response.raise_for_status()  # Raises an HTTPError for bad responses (4xx, 5xx)
                return response

            except RequestException as e:
                if attempt == self.max_retries - 1:  # Last attempt
                    print(f"Failed after {self.max_retries} attempts. Error: {str(e)}")
                    raise  # Re-raise the last exception

                print(f"Attempt {attempt + 1} failed. Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
                # Exponential backoff
                self.retry_delay *= 2

        return None
