import time
import pytest
from app.utils.rate_limiting import RateLimiter


@pytest.fixture
def limiter():
    return RateLimiter()


def test_first_request_is_not_limited(limiter):
    ip = "192.168.1.1"

    assert limiter.is_rate_limited(ip) is False
    assert limiter.requests[ip]['count'] == 1


def test_multiple_requests_under_limit(limiter):
    ip = "192.168.1.2"
    for _ in range(10):
        assert limiter.is_rate_limited(ip) is False

    assert limiter.requests[ip]['count'] == 10


def test_request_at_limit_is_limited(limiter):
    ip = "192.168.1.3"
    
    # Manually set count to the limit
    limiter.requests[ip] = {'count': limiter.limit, 'time': time.time()}
    assert limiter.is_rate_limited(ip) is True


def test_request_after_reset_time_resets_count(limiter):
    ip = "192.168.1.4"
    past_time = time.time() - (limiter.reset_time + 1)  # simulate 61 seconds ago
    limiter.requests[ip] = {'count': 60, 'time': past_time}

    # Should reset and not be rate limited
    assert limiter.is_rate_limited(ip) is False
    assert limiter.requests[ip]['count'] == 1