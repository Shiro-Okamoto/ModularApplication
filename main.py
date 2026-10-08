
import sys
import os


from application import ModularApplication


from configs import VERSION_PATH, PLUGINS_DIR, LOGS_DIR, STORAGE_DIR, CACHE_DIR, UPDATE_DIR, Config

from utils import set_console_title


import logging.config
import colorama
import time


VERSION = VERSION_PATH.read_text('utf-8')


set_console_title(f'Modular Application {VERSION}')


if getattr(sys, 'frozen', False): os.chdir(os.path.dirname(sys.executable))

else: os.chdir(os.path.dirname(__file__))


folders = [PLUGINS_DIR, LOGS_DIR, STORAGE_DIR, CACHE_DIR, UPDATE_DIR]

for folder in folders:
    if not folder.exists(): folder.mkdir(parents=True, exist_ok=True)


Config.init_config()


logger_config: dict = Config().LOGGER.to_dict()

colorama.init()


logging.config.dictConfig(logger_config)

logging.raiseExceptions = False


log = logging.getLogger('main')


log.debug('------------------------------------------------------------------')


try:
    log.info('Starting program...')

    app = ModularApplication('APPLICATION', VERSION)

    app.init().start()


except (KeyboardInterrupt, SystemExit):
    log.info('Exiting program...')

    sys.exit()


except:
    log.critical('An unhandled error occurred when application was running.')

    log.warning('TRACEBACK', exc_info=True)


    log.critical('Exiting program...')


    time.sleep(5)

    sys.exit()