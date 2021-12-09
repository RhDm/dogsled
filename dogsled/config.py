'''
(currently) logging configuration
'''
# TODO implement enum to hold constants and default parameters such as temp folder name, he_ref etc
from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="DYNACONF",
    settings_files=['settings.toml', '.secrets.toml'],
)

# https://stackoverflow.com/questions/7507825/where-is-a-complete-example-of-logging-config-dictconfig
LOGGING_DEVEL_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '{asctime} {module}.{filename} {levelname}: [ {message} ]',
            'datefmt': '%d/%m/%Y %I:%M:%S %p',
            'style': '{'
        },
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers': {
        '': {  # root logger, set to WARNING to supress imported library logs
            'handlers': ['default'],
            'level': 'WARNING',
            'propagate': False,
        },
        '__main__': {  # if __name__ == '__main__'
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}

LOGGING_RELEASE_CONFIG = LOGGING_DEVEL_CONFIG
LOGGING_RELEASE_CONFIG['formatters']['standard']['format']='{asctime} {module} {levelname}: [ {message} ]'