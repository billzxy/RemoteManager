from utils.my_logger import logger
from misc.decorators import manager, with_lock
from misc.enumerators import FS_Status, ThreadLock
from utils.yamlmanager import GetYamlStruct
from processcontroller.systeminfo import getSystemInfo
import traceback


@manager
@logger
class HeartBeatManager():
    def __init__(self):
        pass

    def post_init(self):
        # self.config_manager.load_config()
        pass

    def fill_heartbeat_struct(self):
        CONFIG_PATH = 'model/data.yml'
        struct = GetYamlStruct(CONFIG_PATH)
        auto_info = self.config_manager.get_keys()
        app_key = auto_info['appkey']
        access_id = auto_info['accessId']
        access_secret = auto_info['accessKeySecret']

        freeswitch_status = self.process_manager.is_freeswitch_running()
        java_status = 1 if self.process_manager.is_java_running() else 0
        reg_info = self.process_manager.freeswitch_status()

        system_info = getSystemInfo()
        cpu_rate_info = system_info.cpu_rate()
        mem_rate_info = system_info.mem_rate()
        mac_name_ip_info = system_info.mac_name_ip()

        #TODO:get version info
        struct.content.update
        struct.content['version'] = self.config_manager.get_version_info()['versionNum']
        struct.content['host_ip'] = mac_name_ip_info['addr']
        struct.content['callbox_ip'] = self.config_manager.get_callbox_addr()
        struct.content['app_key'] = app_key
        struct.content['access_id'] = access_id
        struct.content['access_secret'] = access_secret
        struct.content['Freeswitch'] = freeswitch_status
        struct.content['Reg_callbox'] = self.convert_fs_states(reg_info['reg_callbox']) if reg_info else -1
        struct.content['Reg_numconvert'] = self.convert_fs_states(reg_info['reg_numconvert']) if reg_info else -1
        struct.content['Java'] = java_status
        struct.content['cpu'] = cpu_rate_info
        struct.content['mem'] = mem_rate_info
        struct.content['media_storage'] = '2G'
        return struct.content
    
    def convert_fs_states(self, state_str):
        try:
            code = FS_Status[state_str].value
        except:
            code = -1
        finally:
            return code 

    @with_lock(ThreadLock.HEARTBEAT)
    @with_lock(ThreadLock.INSTALL_UPDATE, blocking=True)
    def send_heartbeat(self):
        self.send()

    def send(self):
        self.logger.debug("发送心跳")
        try:
            self.process_manager.keep_fs_alive()
            self.process_manager.check_reg()
            self.process_manager.keep_java_alive()
            hb_info = self.fill_heartbeat_struct()
            self.request_manager.post_heartbeat_info(hb_info)
        except Exception as e:
            self.error(traceback.format_exc())


