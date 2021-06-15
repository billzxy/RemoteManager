from base_manager import BaseManager
from threading import _Timer

class RepeatingTimer(_Timer): 
    def run(self):
        while not self.finished.is_set():
            self.function(*self.args, **self.kwargs)
            self.finished.wait(self.interval)

class JobScheduler(BaseManager):

    def __init__(self, env):
        super().__init__(env)
        r_timer = self.set_update_looper(self.do_sth)
        r_timer.start()

    def set_update_looper(self, operation_fn):
        return RepeatingTimer(10.0, operation_fn)
        

    def do_sth(self):
        self.logger.debug("timer auto logging test")