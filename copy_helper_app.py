import cli_ui
import logger

if __name__ == "__main__":
    logger.configure_logging()

    cli_ui.CliUI.start()
