from misc.decorators import manager
from utils.my_logger import logger
from hashlib import sha1
import traceback, datetime, uuid, hmac, base64, urllib.parse

TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

@manager
@logger
class AuthenticationManager:
    def __init__(self):
        pass

    def post_init(self):
        self.acquire_new_token()

    def get_token(self):
        """
        will compare the current timestamp with expiration timestamp
        if expired, acquire new
        otherwise, use currently saved
        """
        current_timestamp = int(datetime.datetime.now().timestamp())        
        if int(self.__expiration_timestamp) <= current_timestamp:
            self.logger.debug("口令已过期, 重新获取")
            self.acquire_new_token() 

        return self.__token
    
    def acquire_new_token(self):
        try:
            keys = self.config_manager.get_keys()
            signature, params = self.build_signature_and_query_string(keys['accessId'], keys['accessKeySecret'])
            self.__token, expiration_timestamp = self.api_manager.get_user_token(signature, params)
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
                local_timestamp = timestamp_file.read()
                if not len(local_timestamp) == 10:
                    self.logger.debug("本地时间戳长度有误, 重新获取token")
                    self.acquire_new_token()
                else:
                    self.__expiration_timestamp = local_timestamp

        except FileNotFoundError:
            self.logger.error("本地无token时间戳记录, 获取新token")
            self.acquire_new_token()
         
        except Exception as e:
            self.acquire_new_token()
            self.logger.error("本地获取时间戳失败, 已重新请求接口获取, 错误原因: %s",
                traceback.format_exc())

    def build_signature_and_query_string(self, key_id, key_secret):
        # dont ask me why, because im closely following the guideline
        # dont tell me there's a better way, as im running out of time
        # Step 1, required parameters
        params = {}
        time_str = datetime.datetime.utcfromtimestamp(datetime.datetime.now().timestamp()).strftime(TIME_FORMAT)
        params['Timestamp'] = time_str
        params['Format'] = "JSON"
        params['SignatureVersion'] = "1.0"
        params['SignatureMethod'] = "HMAC-SHA1"
        params['AccessKeyId'] = key_id
        params['SignatureNonce'] = str(uuid.uuid4())
        # Step 2, remove parameter 'Signature'
        params.pop('Signature', None)
        # Step 3 & 4, sort params, build query string, and build signature
        sorted_query_string = ""
        for key in sorted(list(params.keys())):
            sorted_query_string += "&" + self.special_url_encode(key) + "=" + self.special_url_encode(params[key])  
        sorted_query_string_sliced = sorted_query_string[1:]
        string_to_sign = "GET&"+ self.special_url_encode("/")+ "&" + self.special_url_encode(sorted_query_string_sliced)
        signature_raw = self.sign(key_secret, string_to_sign)
        return signature_raw, params

    def special_url_encode(self, content):
        return urllib.parse.quote(content).replace("/", "%2F").replace("+", "%20").replace("*", "%2A").replace("%7E","~")

    def sign(self, key_secret, string_to_sign):
        # hashing
        hashed = hmac.new(bytes(key_secret+"&", encoding="utf-8"), bytes(string_to_sign, encoding="utf-8"), sha1)
        # The signature
        return base64.encodebytes(hashed.digest()).decode('utf-8').rstrip('\n')
        # return hashed.digest().encode("base64").rstrip('\n')