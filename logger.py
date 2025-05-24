import logging

datefmt = '%d-%m %H:%M:%S'

console_format = '[%(levelname)s] : %(message)s'
file_format = '%(asctime)s [%(levelname)s] : %(message)s | %(name)s'


def configure_logging():
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    console_formatter = logging.Formatter(console_format, datefmt=datefmt)
    console_handler.setFormatter(console_formatter)

    file_handler = logging.FileHandler('main-log.log', mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    file_formatter = logging.Formatter(file_format, datefmt=datefmt)
    file_handler.setFormatter(file_formatter)

    logging.basicConfig(level=logging.DEBUG, handlers=[console_handler, file_handler], force=True)

    logging.getLogger('googleapiclient').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
