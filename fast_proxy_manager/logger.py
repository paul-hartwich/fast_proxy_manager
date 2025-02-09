import logging

# sets the level of the asyncio logger to CRITICAL, necessary to avoid unnecessary logs when testing proxies
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

logger = logging.getLogger("fast_proxy_manager")
logger.propagate = True  # if true uses the root logger when set

if not logger.hasHandlers():
    logger.setLevel(logging.DEBUG)  # default level for the logger in this lib

    # Create a console handler for general messages
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s] %(message)s', datefmt='%m-%d %H:%M')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Create a separate handler for debug messages
    debug_handler = logging.StreamHandler()
    debug_handler.setLevel(logging.DEBUG)
    debug_formatter = logging.Formatter('[%(name)s][DEBUG] %(message)s')  # without time
    debug_handler.setFormatter(debug_formatter)
    logger.addHandler(debug_handler)
