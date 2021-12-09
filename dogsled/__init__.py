import logging
import logging.config
from dogsled import config


logger = logging.getLogger(__name__)
logging.config.dictConfig(config.LOGGING_DEVEL_CONFIG)
