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
比如log_manager实例, 或者可以直接调用的 info debug error方法等, 简化每个Manager类定义日志配置的流程

原理:
它在一个类在被实例化为对象之前执行(这个类传参进来, 称为cls)
点缀器会篡改传进来的类的 __init__()构造方法, 
在它的构造方法前面添加新的步骤

"""
def logger(cls):
    # 把原有的__init__方法获取到
    init_method = cls.__init__
    print("logger: ", cls.__name__)
    # 定义一个新的构造方法
    def new_init(self, *args, **kwargs):
        # 为传进来的类添加一些类成员

        # 将单例LoggerManager设置为一个成员, 还有logger的实体, 与环境等信息, 主要是可以省去每个Manager需要手动定义或获取logger的重复代码
        # LoggerManager单例的实现请看该文件代码内的注释
        log_manager = LoggerManager()
        env = log_manager.get_env()
        logger = log_manager.logger
        self.env = env
        self.logger = logger
        self.module_name = cls.__name__

        # 将logging库的logger实例的原生方法设置为这个类的方法, 这样在这个类里面可以直接调用 self.info("some log") 而不用 self.logger.info("some log")
        # 但注意! 这偷懒方法有个弊端: 就是所有输出的日志条目的moduleName和lineNo就是以下声明所在的代码位置, 而不是那个调用输出方法的代码所在的位置, 所以如果需要debug的话慎用
        # 甚至我其实现在已经不建议使用了
        self.info = logger.info
        self.debug = logger.debug
        self.warn = logger.warning
        self.error = logger.error
        self.critical = logger.critical
        # 执行原来的__init__方法
        init_method(self, *args, **kwargs)

    # 将新的(包含原来的)构造方法反设回这个类
    cls.__init__ = new_init
    # 返回这个被篡改过的类
    return cls