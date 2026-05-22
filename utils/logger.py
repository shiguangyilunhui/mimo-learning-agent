import logging, sys
def get_logger(name, level=None):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S'))
        logger.addHandler(handler)
    if level: logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger
