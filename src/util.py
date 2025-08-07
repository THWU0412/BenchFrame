import configparser
from datetime import datetime
import logging
import os
import pandas as pd
import numpy as np

# CONFIGURATION
config = configparser.ConfigParser()
config.read('host.conf')

# LOGGING
log_file = config['host']['EXEC_PATH'] + 'logs/' + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + '.log'
log_level = 'INFO'

os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    filename=log_file,
    level=log_level,
    format='%(asctime)s [%(levelname)s] %(message)s',
    filemode='a'
)

logger = logging.getLogger(__name__)