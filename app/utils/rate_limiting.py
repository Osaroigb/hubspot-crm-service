from time import time

class RateLimiter:
    def __init__(self):
        self.requests = {}
        self.limit = 60  # 60 requests per minute
        self.reset_time = 60  # 1 minute in seconds

    def is_rate_limited(self, ip):
        current_time = time()
        
        # Check if IP exists and handle the rate limit logic
        if not self.is_ip_exist(ip):
            # IP does not exist, so initialize it
            self.requests[ip] = {'count': 1, 'time': current_time}
            return False  # Not rate-limited because it's the first request

        # If IP exists, retrieve its request info
        requests_info = self.requests[ip]

        # Check if the record is older than reset_time and reset if necessary
        if current_time - requests_info['time'] > self.reset_time:
            # Reset count and time for a new period
            requests_info['count'] = 1
            requests_info['time'] = current_time

            return False  # Not rate-limited because we just reset the counter
        else:
            if requests_info['count'] < self.limit:
                # Increment the request count since it's within the limit
                requests_info['count'] += 1
                return False  # Not rate-limited, under the request limit
            else:
                # The request count is equal to or exceeds the limit
                return True  # Rate-limited

    def is_ip_exist(self, ip):
        # Check if the IP already exists in the requests dictionary
        return ip in self.requests