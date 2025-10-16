import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    file_handler = logging.FileHandler("errors.log")
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))

    logging.getLogger().addHandler(file_handler)