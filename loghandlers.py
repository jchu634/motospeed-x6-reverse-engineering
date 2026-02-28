import logging
import sys
from pathlib import Path


def setup_logging(
    log_file: str = "app.log",
    level: int = logging.INFO,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
) -> logging.Logger:
    """
    Sets up a logger that writes to both console and a file.

    Args:
        log_file (str): Path to the log file.
        level (int): Overall logger level.
        console_level (int): Logging level for console output.
        file_level (int): Logging level for file output.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(level)

    # Avoid adding multiple handlers if setup_logging is called again
    if logger.handlers:
        return logger

    # Create log directory if necessary
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_format = logging.Formatter(fmt="%(levelname)s | %(message)s")
    console_handler.setFormatter(console_format)
    console_handler.setLevel(console_level)

    # File handler
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_format = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_format)
    file_handler.setLevel(file_level)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Example usage:
if __name__ == "__main__":
    log = setup_logging("logs/app.log")
    log.info("This is an info message.")
    log.debug("This is a debug message.")
    log.error("This is an error message.")
