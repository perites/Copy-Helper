import logging

import logger

if __name__ == "__main__":
    logging.root = logger.logger
    import cli_ui

    cli_ui.CliUI.start()
