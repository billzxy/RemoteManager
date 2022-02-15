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

"""
这个logger点缀器的功能:

为传进来的类, 添加一系列与日志输出相关的class members与methods, 
比如log_manager, 比如可以直接调用的 info debug error方法等, 简化每个Manager类定义日志配置的流程

原理:
它在一个类在被实例化为对象之前执行(这个类传参进来, 称为cls)
点缀器会"劫持"传进来的类的 __init__()构造方法, 
在它的构造方法前面添加新的步骤

"""
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