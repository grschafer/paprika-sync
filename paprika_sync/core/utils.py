import functools
import re


# Logs start and end of the wrapped function
# Used for extra logging verbosity on cronjobs (management commands)
def log_start_end(logger):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.info('Start')
            val = func(*args, **kwargs)
            logger.info('End')
            return val
        return wrapper
    return decorator


def strip_query_params(url):
    return url.partition('?')[0]


PAPRIKA_S3_KEY_REGEX = re.compile(r'http://uploads.paprikaapp.com.s3.amazonaws.com/(?P<key>.*)')


def make_s3_url_https(url):
    match = PAPRIKA_S3_KEY_REGEX.match(url)
    if match:
        key = match.group("key")
        return f'https://s3.amazonaws.com/uploads.paprikaapp.com/{key}'
    return url
