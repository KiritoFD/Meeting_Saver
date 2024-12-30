import time
from functools import wraps
from ..utils.logger import get_logger

logger = get_logger(__name__)

def retry_on_failure(max_retries=3, delay=1):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"重试{max_retries}次后失败: {str(e)}")
                        raise
                    logger.warning(f"操作失败，{delay}秒后重试 ({retries}/{max_retries})")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator 