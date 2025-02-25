import logging
import sys

logger = logging.getLogger('copy-helper')
logger.setLevel(logging.DEBUG)

datefmt = '%d-%m %H:%M:%S'
formatter = logging.Formatter('%(asctime)s [%(levelname)s] : %(message)s',
                              datefmt=datefmt)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

file_handler = logging.FileHandler('main-log.log', mode='a', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

if not logger.hasHandlers():
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

logger.propagate = False

logging.getLogger('googleapiclient').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)


def configure_console_logger(user_log_level):
    user_level_to_logging = {
        'All': logging.DEBUG,
        'Info': logging.INFO
    }

    logging_level = user_level_to_logging.get(user_log_level, logging.DEBUG)
    if not logging_level:
        logger.info('Unknown information level, set to All')

    console_handler.setLevel(logging_level)


logging.root = logger
