import traceback
import requests
from misc.decorators import manager
from utils.my_logger import logger
from misc.exceptions import FileDownloadError, HttpRequestError, ICBRequestError, NotFoundError, UpdateIsNoGo
from misc.enumerators import GetTasksAPIType, TaskStatusRequestSignal
from requests_toolbelt import MultipartEncoder

"""
管理各种请求的, 业务级层面, 入参出参都封装过了, 程序其他地方的流程可以直接用
不用担心底层请求的handling

"""

@manager
@logger
class RequestManager():
    def __init__(self):
        pass

    def post_init(self):
        self.host_addr = self.config_manager.get_host_address()
        self.api_prefix = self.config_manager.get_api_prefix()
       
    # 获取版本检查接口的返回结果
    def get_version_check(self):
        version_info = self.config_manager.get_version_info()
        content = self.api_manager.get_version_check(version_info['versionNum'])
        self.logger.debug("version check content: %s", content)
        upgrade_mark = content['upgradeMark']
        if not upgrade_mark==0:
            upgrade_list = content['upgradeList']
            self.logger.debug("upgrade mark: %s, upgrade list: %s", upgrade_mark,
                          upgrade_list)
        return content

    # 下载文件
    def get_file_download(self, version_code, local_filename, fn_set_progress):
        return self.api_manager.get_file_download(version_code, local_filename, fn_set_progress)

    # 获取任务的状态
    # 入参是枚举 GetTasksAPIType 的任意值
    def get_task_list(self, req_type):
        try:
            content = self.api_manager.get_tasks(req_type) 
        except NotFoundError:
            self.logger.error("找不到请求%s任务列表的接口", req_type.value)
            raise
        except:
            self.logger.error("请求%s任务列表失败, 原因: %s", req_type.value, traceback.format_exc())
            return []
        else:
            task_list = list(content) if not content==None and not content=="" else []
            self.logger.debug("获取到的%s任务列表: %s", req_type.value, str(task_list))
            return task_list

    # 请求暂停所有外呼任务
    def post_pause_all_tasks(self):
        try:
            task_ids = self.get_task_list(GetTasksAPIType.UNFINISHED)
        except NotFoundError:
            task_ids = self.db_operator.get_all_ongoing_task_ids()
        except:
            task_ids = self.db_operator.get_all_ongoing_task_ids()
        try:
            result = None
            if(len(task_ids)>0):
                result = self.api_manager.post_up_task_status(task_ids, TaskStatusRequestSignal.PAUSE.value)
        except:
            self.logger.error("请求任务暂停失败, 原因: %s", traceback.format_exc())
            raise UpdateIsNoGo("暂停任务失败", traceback.format_exc())
        else:
            self.logger.debug("暂停任务请求结果: %s", str(result))

    # 请求恢复所有外呼任务
    def post_resume_all_tasks(self):
        try:
            task_ids = self.get_task_list(GetTasksAPIType.PAUSED)
            result = None
            if(task_ids and len(task_ids)>0):
                result = self.api_manager.post_up_task_status(task_ids, TaskStatusRequestSignal.RESUME.value)
        except:
            raise
        else:
            self.logger.debug("恢复任务请求结果: %s", str(result))

    # 发送心跳包
    def post_heartbeat_info(self, heartbeat_info):
        self.logger.debug('发送心跳包...')
        try:
            content = self.api_manager.post_heartbeat_info(heartbeat_info)

        except HttpRequestError as err:
            self.logger.error("发送心跳包失败, %s", err)
            return
        except ICBRequestError as err:
            self.logger.error("发送心跳包失败, %s", err)
            return

        self.logger.debug('发送心跳包结果: %s', content)
        return content

    # 发送日志(暂时废弃)
    def post_logs_info(self, path, filename):
        auth = {
            'token': self.auth_manager.get_token(),
            'appkey': self.config_manager.get_keys()['appkey']
        }
        data = MultipartEncoder(
            fields={
                'propertyMessageXml': ('filename', open(path + filename, 'rb'),
                                       'text/xml')
            })
        try:
            content = self.api_manager.post_logs_info(auth, data)

        except HttpRequestError as err:
            self.logger.error("%s", err)
            return
        except ICBRequestError as err:
            self.logger.error("%s", err)
            return
        # TODO: handling stuffs
        return content
