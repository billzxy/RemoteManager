from functools import wraps
from misc.consts import LOCKS
from misc.enumerators import ThreadLock
from utils.manager_hub import add_members
import random, time
import traceback
# static decorators

# 单例点缀器:
# 这个原理比较简单, 网上拉来的代码, 想要理解它既简单又费脑, 懒得解释了, 反正就是它能实现单例
# make a certain class singleton, as name suggests
def singleton(cls):
    print("singleton: ",cls.__name__)
    instances = {}
    @wraps(cls)
    def _wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return _wrapper

# manager点缀器:
# 它其实跟上面那个singleton点缀器原理一样, 只是在实例化对象以后, 再添加几个步骤
def manager(cls):
    print("manager", cls.__name__)
    instances = {}
    @wraps(cls) # 这个点缀器效果是保留被包裹的类的名称, 否则用了这个@manager点缀器的类, 你获取cls.__name__就会是`_wrapper`而不是原本类名
    def _wrapper(*args, **kwargs):
        if cls not in instances:
            new_obj = cls(*args, **kwargs)  # 这里会将类构造(实例化)为对象
            instances[cls] = new_obj 
            print("__init__(): ", cls.__name__)
            add_members(new_obj)
            try:
                new_obj.post_init()
            except:
                new_obj.logger.debug(f"Post init: {new_obj.module_name}, error: %s", traceback.format_exc())
            else:
                print("post_init(): ", cls.__name__)
                # new_obj.logger.debug(f"{new_obj.module_name} successfully initialized...")
            return new_obj
        return instances[cls]
    return _wrapper

def with_lock(lock, blocking=False, then_execute_callback=None):
    if isinstance(lock, str):
        thread_lock = LOCKS[ThreadLock(lock)]
    else:
        thread_lock = LOCKS[lock]
    def wrapper(fn):
        @wraps(fn)
        def execute_with_lock(self, *args, **kwargs):
            if thread_lock.acquire(blocking):
                try:
                    res = fn(self, *args, **kwargs)
                except Exception:
                    self.logger.error(traceback.format_exc())
                    res = None
                finally:
                    thread_lock.release()
                    if then_execute_callback:
                        then_execute_callback()
                    return res
            else:
                if(self.logger):
                    self.logger.debug("线程占用, 下次一定")
        return execute_with_lock
    return wrapper


""" usage:

@with_countdown
def your_class_method(self, arg_a, arg_b, max_wait=5, randomly=False, timed=False):
    ...

args explained:

max_wait: maximum countdown(wait) time (why does this matter? please read along:
randomly: if True, will randomly pick a number within max_wait and sleep, otherwise
    max_wait will be the sleep time
timed: do you want to sleep or not?

"""
def with_countdown(fn):
    @wraps(fn)
    def timed_execution(*args, max_wait=5, randomly=False, timed=False, **kwargs):
        if(timed):
            countdown = random.randint(1, max_wait+1) if randomly else max_wait
            for i in range(countdown, 0, -1):
                time.sleep(1)
        return fn(*args, **kwargs)
    return timed_execution


""" usage:

@with_countdown2(max_wait=3, randomly=True, timed=True)
def your_class_method(self, arg_a, arg_b):
    ...
"""
def with_countdown2(max_wait=5, randomly=False, timed=False):
    def wrapper(fn):
        @wraps(fn)
        def timed_execution(self, *args, **kwargs):
            if(timed):
                countdown = random.randint(1, max_wait+1) if randomly else max_wait
                time.sleep(countdown)
            return fn(self, *args, **kwargs)
        return timed_execution
    return wrapper


""" usage:

@with_retry(retries=2, interval=1)
def your_class_method(self, arg_a, arg_b):
    ...
"""
def with_retry(retries=3, interval=5):
    def wrapper(fn):
        @wraps(fn)
        def fn_execution(self, *args, **kwargs):
            countdown = retries
            while True:
                try:
                    result = fn(self, *args, **kwargs)
                except Exception:
                    if(countdown>0):
                        countdown-=1
                        self.debug(f"执行失败, {interval}秒后重试第{retries-countdown}/{retries}次, 失败原因:\n%s", traceback.format_exc())
                        time.sleep(interval)
                    else:
                        raise
                else:
                    return result
        return fn_execution
    return wrapper


""" usage:

@with_retry2
def your_class_method(self, arg_a, arg_b, retries=2, interval=1):
    ...

"""
def with_retry2(fn):
    @wraps(fn)
    def fn_execution(self, *args, retries=3, interval=5, **kwargs):
        countdown = retries
        while True:
            try:
                result = fn(self, *args, **kwargs)
            except Exception:
                if(countdown>0):
                    countdown-=1
                    self.debug(f"执行失败, {interval}秒后重试第{retries-countdown}/{retries}次, 失败原因:\n%s", traceback.format_exc())
                    time.sleep(interval)
                else:
                    raise
            else:
                return result
    return fn_execution

# def with_token(fn):
#     @wraps(fn)
#     def fn_execution(self, *args, **kwargs):
#         header 