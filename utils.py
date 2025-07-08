import time
import random
import logging

logger = logging.getLogger(__name__)

def random_delay(min_seconds=2, max_seconds=15):
    """Wait for a random amount of time to simulate human behavior"""
    delay = random.uniform(min_seconds, max_seconds)
    logger.info(f"Waiting for {delay:.2f} seconds")
    time.sleep(delay)

def get_random_user_agent():
    """Return a random user agent string"""
    user_agents = [
        # Windows Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
        # Windows Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0",
        # Mac Chrome
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
        # Mac Firefox
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 12.1; rv:96.0) Gecko/20100101 Firefox/96.0",
        # Linux Chrome
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        # iPad
        "Mozilla/5.0 (iPad; CPU OS 15_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/96.0.4664.116 Mobile/15E148 Safari/604.1",
        # iPhone
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/96.0.4664.116 Mobile/15E148 Safari/604.1"
    ]
    return random.choice(user_agents)

def handle_rate_limiting(e):
    """Handle rate limiting errors"""
    if "rate limit" in str(e).lower() or "too many requests" in str(e).lower():
        wait_time = 3600  # 1 hour in seconds
        logger.warning(f"Rate limit detected, waiting for {wait_time} seconds")
        time.sleep(wait_time)
        return True
    return False