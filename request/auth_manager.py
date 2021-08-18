from misc.decorators import manager
from utils.my_logger import logger
import traceback, datetime

TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

@manager
@logger
class AuthenticationManager:
    def __init__(self):
        pass

    def post_init(self):
        self.read_saved_timestamp()

    def get_token(self):
        """
        will compare the current timestamp with expiration timestamp
        if expired, acquire new
        otherwise, use currently saved
        """
        current_timestamp = int(datetime.datetime.now().timestamp() * 1000)        
        if int(self.__expiration_timestamp) <= current_timestamp:
            self.acquire_new_token() 

        return self.__token
    
    def acquire_new_token(self):
        try:
            keys = self.config_manager.get_keys()
            self.__token, expiration_timestamp = self.api_manager.get_user_token(
                keys['accessId'], keys['accessKeySecret'])
            self.__expiration_timestamp = str(expiration_timestamp)
            # write timestamp to file
            with open("./settings/timestamp", "w") as timestamp_file:
                timestamp_file.write(self.__expiration_timestamp)
            
        except Exception as e:
            self.logger.error(traceback.format_exc())
    
    def read_saved_timestamp(self):
        """
        will attempt to read timestamp locally
        if error encountered such as file not exist or data corruption,
        acquire new
        """
        try:
            with open("./settings/timestamp", "r") as timestamp_file:
                self.__expiration_timestamp = timestamp_file.read()
            
        except Exception as e:
            self.acquire_new_token()
            self.logger.error("本地获取时间戳失败, 已重新请求接口获取, 错误原因: %s",
                traceback.format_exc())

    def build_token_query(self, key_id, key_secret):
        params = {}
        time_str = datetime.datetime.utcfromtimestamp(datetime.datetime.now().timestamp()).strftime(TIME_FORMAT)
        params['Timestamp'] = time_str
        params['Format'] = "XML"
        params['SignatureVersion'] = "1.0"
        params['SignatureMethod'] = "HMAC-SHA1"
        params['AccessKeyId'] = key_id
        params['SignatureNonce'] = ""
        params['']

    def special_url_encode(self, content):
        return content.encode('utf-8').replace("+", "%20").replace("*", "%2A").replace("&7E","~")