from settings.settings_manager import SettingsManager
from utils.log_manager import LoggerManager

# def make_logger_methods_self(fn):
#     def magical_wrapper(self, *args, **kwargs):
#         fn(*args, **kwargs)
#     return magical_wrapper

# def logger(cls):
#     settings_manager = SettingsManager()
#     log_manager = LoggerManager()
#     env = log_manager.get_env()
#     logger = log_manager.logger
#     setattr(cls, 'env', env)
#     setattr(cls, 'logger', logger)
#     setattr(cls, 'module_name', cls.__name__)
#     setattr(cls, 'info', make_logger_methods_self(logger.info))
#     setattr(cls, 'debug', make_logger_methods_self(logger.debug))
#     setattr(cls, 'warn', make_logger_methods_self(logger.warning))
#     setattr(cls, 'error', make_logger_methods_self(logger.error))
#     setattr(cls, 'critical', make_logger_methods_self(logger.critical))
#     return cls

def logger(cls):
    init_method = cls.__init__

    def new_init(self, *args, **kwargs):
        log_manager = LoggerManager()
        env = log_manager.get_env()
        logger = log_manager.logger
        self.env = env
        self.logger = logger
        self.module_name = cls.__name__
        self.info = logger.info
        self.debug = logger.debug
        self.warn = logger.warning
        self.error = logger.error
        self.critical = logger.critical
        init_method(self, *args, **kwargs)

    cls.__init__ = new_init
    return cls