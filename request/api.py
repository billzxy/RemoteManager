from misc.decorators import manager, with_retry
from utils.my_logger import logger
from misc.enumerators import FilePath, GetTasksAPIType
from misc.exceptions import HttpRequestError, ICBRequestError, FileDownloadError, NoFileError, NotFoundError

import requests, json, shutil, traceback, datetime

@manager
@logger
class APIManager:
    def __init__(self):
        pass

    def post_init(self):
        self.init_addresses()
    
    def init_addresses(self):
        # 云平台网关
        self.host_addr = self.settings_manager.get_host_addr()
        self.api_prefix = self.config_manager.get_api_prefix()
        # 前置服务
        self.local_java_srv_host = "http://127.0.0.1"
        yml_data = self.settings_manager.get_yaml_info(self.settings_manager.get_paths()[FilePath.APP_YML])
        self.local_java_srv_port = yml_data['server']['port']

    def get_user_token(self, signature, params):
        params["Signature"] = signature
        headers = {"AccessKeyId": params['AccessKeyId']}
        url = self.__assemble_url("/getUserToken", "/gateway/token")
        self.logger.debug("GET user token: %s", url)
        self.logger.debug("params: %s", params)
        data = self.__http_get(url, params, headers=headers)
        if not data['code'] == 1:
            raise ICBRequestError(data)
        content = data['content']
        return content['token'], content['expireTime']

    def get_version_check(self, version_num):
        headers = {
            'token': self.auth_manager.get_token(),
            'appkey': self.config_manager.get_keys()['appkey']
        }
        params = {
            'appkey':headers['appkey'], 
            'versionNum':version_num
        }
        url = self.__assemble_url("/version/check")
        self.logger.debug("GET version check: %s", url)
        data = self.__http_get(url, params, headers)
        if not data['code'] == 1:
            raise ICBRequestError(data)
        return json.loads(data['content']) 

    def get_file_download(self, version_code, local_filename, fn_set_progress):
        headers = {
            'token': self.auth_manager.get_token(),
            'appkey': self.config_manager.get_keys()['appkey']
        }
        params = {
            'appkey':headers['appkey'],
            'versionCode':version_code
        }
        url = self.__assemble_url("/version/file")
        self.logger.debug("GET version file: %s", url)
        try:
            fname = self.__download_in_chunks(
                url, params, headers=headers, fn_set_progress=fn_set_progress, local_filename=local_filename)
        except NoFileError as nfe:
            raise nfe 
        
        except ICBRequestError as icbe:
            self.logger.error("下载失败! 原因: %s", icbe.message)
            raise FileDownloadError(icbe.message) 
        
        except Exception as e:
            self.error("File download failed...")
            raise FileDownloadError(traceback.format_exc()) 
        
        return fname  

    def get_tasks(self, req_type):
        apis = {
            GetTasksAPIType.UNFINISHED: "/listUnFinishTaskNos",
            GetTasksAPIType.PAUSED: "/listPauseTaskNos"
        }
        dest = apis[req_type]
        self.logger.debug(f"请求获取{req_type.value}任务接口: {dest}")
        url = "%s:%s/task%s" %(self.local_java_srv_host, self.local_java_srv_port, dest)
        result = self.__http_get(url, None)
        if not result['code'] == 1:
            raise ICBRequestError(result['msg'])
        return result['content']

    @with_retry(retries=3, interval=5)
    def post_up_task_status(self, task_id_list, task_op_flag):
        headers = {
            'token': self.auth_manager.get_token(),
            'appkey': self.config_manager.get_keys()['appkey']
        }
        data = {
            "appkey": self.config_manager.get_keys()['appkey'],
            "taskNos": task_id_list,
            "taskOpFlag": task_op_flag
        }
        url = self.__assemble_url("/version/upTaskStatus")
        result = self.__http_post(url, data, headers)
        if not result['code'] == 1:
            raise ICBRequestError(result['msg'])
        return result

    def post_heartbeat_info(self, heartbeat_info):
        headers = {
            'token': self.auth_manager.get_token(),
            'appkey': self.config_manager.get_keys()['appkey']
        }
        heartbeat_key_val_list = list(map(lambda tup: {'key': tup[0], 'value': tup[1]}, heartbeat_info.items()))
        print(heartbeat_key_val_list)
        data = {
            "appkey": self.config_manager.get_keys()['appkey'],
            "items": list(heartbeat_key_val_list),
            "time": int(datetime.datetime.now().timestamp() * 1000),
            "versionCode": self.config_manager.get_version_info()['versionCode']
        }
        self.logger.debug("心跳包请求体：%s", data)
        url = self.__assemble_url("/heartBeat")
        # add some logging
        result = self.__http_post(url, data, headers)
        if not result['code'] == 1:
            raise ICBRequestError(result['msg'])
        return result
    
    def post_logs_info(self, auth, logs_info):
        headers = auth
        url = self.__assemble_url("/logsdata")
        # add some logging
        data = self.__upload_file(url, logs_info, headers)
        # TODO: response handling
        return data

    def __assemble_url(self, url, api_prefix="default"):
        return self.host_addr + (self.api_prefix if api_prefix=="default" else api_prefix) + url

    def __http_post(self, url, data, headers={}): # header is a dict
        headers["Content-type"] = "application/json;charset=UTF-8"
        self.logger.debug("发送POST请求url: %s, data: %s, headers: %s", url, data, headers)
        r = requests.post(url, json=data, headers=headers, timeout=60)
        self.logger.debug("POST请求结果 状态码: %s, 返回内容: %s", r.status_code, r.text)
        if not r.status_code == 200:
            raise HttpRequestError(r, r.text)
        raw = r.text
        # decrypted = self.encryption_manager.decrypt(raw)
        decrypted = raw
        try:
            parsed_dict = json.loads(decrypted)
        except json.decoder.JSONDecodeError:
            raise
        else:
            return parsed_dict
    
    def __upload_file(self, url, data, headers={}): # header is a dict
        headers["Content-type"] = data.content_type
        r = requests.post(url, data=data, headers=headers)
        if not r.status_code == 200:
            raise HttpRequestError(r, r.text)
        raw = r.text
        decrypted = self.encryption_manager.decrypt(raw)
        try:
            parsed_dict = json.loads(decrypted)
        except json.decoder.JSONDecodeError:
            raise
        else:
            return parsed_dict
    

    def __http_get(self, url, params, headers=""):
        self.logger.debug("GET请求url: %s, params: %s, headers: %s", url, params, headers)
        r = requests.get(url, params=params, headers=headers, timeout=60)
        self.logger.debug("GET请求url: %s", r.url)
        self.logger.debug("GET请求结果 状态码: %s, 返回内容: %s", r.status_code, r.text)
        if not r.status_code == 200:
            if r.status_code == 404:
                raise NotFoundError
            raise HttpRequestError(r, r.text)
        raw = r.text
        # decrypted = self.encryption_manager.decrypt(raw)
        decrypted = raw
        try:
            parsed_dict = json.loads(decrypted)
            if not parsed_dict['code'] == 1:
                try:
                    message = parsed_dict['msg']
                except KeyError:
                    message = parsed_dict['content']
                finally:
                    raise ICBRequestError(message)
            try:
                content_raw = parsed_dict['content']
            except:
                content = None
            else:
                content = content_raw if content_raw else None
            parsed_dict['content'] = content
 
        except json.decoder.JSONDecodeError:
            raise
        else:
            return parsed_dict

    def __download_in_chunks(self, url, params, headers='', **kwargs):
        currentIndex = 0
        totalIndex = 10
        with open(kwargs['local_filename'], 'wb') as f:
            pass
        while not currentIndex == totalIndex:
            params['fileIndex'] = currentIndex
            r = requests.get(url, params=params, headers=headers, timeout=60)
            if not r.status_code == 200:
                raise HttpRequestError(r, r.text)
            raw = r.text
            try:
                parsed_dict = json.loads(raw)
                if not parsed_dict['code'] == 1:
                    raise ICBRequestError(parsed_dict['msg'])
                content = parsed_dict['content']
                totalIndex = content['totalIndex']
            except json.decoder.JSONDecodeError:
                raise

            else:
                with open(kwargs['local_filename'], 'ab') as f:
                    f.write(b''.join([int_byte.to_bytes(1, 'big', signed=True) for int_byte in content['bytes']]))
                currentIndex += 1
                kwargs['fn_set_progress'](currentIndex, totalIndex)
        return 1

    # deprecated download as stream
    def __download_file_stream_in_chunks(self, url, params, headers='', **kwargs):
        file_size_dl = 0
        chunk_sz = 8192
        with requests.get(url, params=params, headers=headers, stream=True) as r:
            try:
                file_size = int(r.headers["Content-Length"])
            except:
                raise NoFileError
            with open(kwargs['local_filename'], 'wb') as f:
            #     shutil.copyfileobj(r.raw, f)
                for chunk in r.iter_content(chunk_size=chunk_sz):
                    # if self.shutdown_flag.is_set():
                    #     break
                    file_size_dl += len(chunk)
                    f.write(chunk)
                    progress = int(file_size_dl * 100. // file_size)
                    if progress % 10 == 0:
                        kwargs['fn_set_progress'](progress)
        return 1
