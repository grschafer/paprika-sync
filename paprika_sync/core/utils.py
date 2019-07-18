import functools


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
