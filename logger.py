import logging

def setup_custom_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s[%(name)s]: %(message)s',
                                  datefmt ='%d-%m-%Y %H:%M:%S')

    #handler = logging.StreamHandler()
    handler = logging.FileHandler('log.txt')
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger