import sys

from loguru import logger

logger.add("ntscuda_last_debug_log.log", enqueue=True, mode='w')

