import logging, configparser, traceback, copy

from PyQt5.QtCore import lowercasebase
from processcontroller.processstatus import FREESWITCH_PROCESS_NAME
from misc.decorators import manager
from conf.consts import CONFIG, REMOTE_CONF_MAPPING, XMLS, FS_CONF, FS_CONF_MAPPING
from misc.enumerators import Envs, FilePath
from utils.my_logger import logger
from lxml import etree

"""
负责管理盒子配置参数(appkey, access_id, access_key_secret, 盒子版本号等参数)的类
初始化时候会读取盒子安装根目录下 ./conf/configuation.ini 文件内的参数

除了类似SettingsManager可以读取配置get_config_item_by_mapping(self, key) #用什么key参考REMOTE_CONF_MAPPING

也有api在安装步骤中更新远程配置项到本地: update_remote_config(self, arg_conf_map, version_num, version_code)

还有可以修改FreeSwitch的配置的功能, 操作方式是在 configuration.ini里改变了FreeSwitch的参数以后, 调用save_fs_conf()去应用保存FS配置
也可以调用update_config(self, new_conf_obj)直接写入, 具体使用方式有兴趣可以研究下源码, 不做赘述了
"""

@manager
@logger
class ConfigManager:
    def __init__(self):
        # self.__host_address = CONFIG[self.env]['host_addr']
        self.tree_dict = {}
        self.__api_prefix = CONFIG[self.env]['api_prefix']
        self.fs_conf = copy.deepcopy(FS_CONF)
        # self.fs_conf_path = self.paths[FilePath.FS_CONF]

    def post_init(self):
        self.__host_address = self.settings_manager.get_host_addr()
        self.paths = self.settings_manager.get_paths()
        self.load_config()

    def load_config(self):
        try:
            self.config = self.settings_manager.read_ini_into_config(self.paths[FilePath.CONFIG])
            self.__version_num = self.config['QTHZ']['version']
            self.__version_code = self.config['QTHZ']['code']
            self.__appkey = self.config['appkey']['key']
            self.__access_id = self.config['accessid']['id']
            self.__access_key_secret = self.config['accesssecret']['secret']
        except Exception as e:
            self.logger.error(traceback.format_exc())
        else:
            self.logger.info("配置加载完成")

    def update_remote_config(self, arg_conf_map, version_num, version_code):
        self.logger.info("更新远程配置到本地")
        ini_file_path = self.paths[FilePath.CONFIG]
        config = self.settings_manager.read_ini_into_config(ini_file_path)
        config['QTHZ']['version'] = version_num
        config['QTHZ']['code'] = version_code
        for key, item in arg_conf_map.items():
            try:
                section, ini_key = REMOTE_CONF_MAPPING[key]
            except KeyError:
                self.logger.error("No mapping binded for key: %s, create in QTHZ category", key)
                config["QTHZ"][key] = item
                continue
            else:
                config[section][ini_key] = item
        self.settings_manager.write_config_to_ini_file(config, ini_file_path)
                    
    def get_host_address(self):
        return self.__host_address
    
    def get_callbox_addr(self):
        return self.get_config_item_by_mapping('callboxRealm')

    def get_api_prefix(self):
        return self.__api_prefix

    def get_keys(self):
        return {
            'appkey': self.__appkey, 
            'accessId': self.__access_id, 
            'accessKeySecret': self.__access_key_secret
        }

    def get_version_info(self):
        return {'versionNum': self.__version_num, 'versionCode': self.__version_code}

    def get_config_item_by_mapping(self, key):
        try:
            section, ini_key = REMOTE_CONF_MAPPING[key]
        except KeyError:
            self.logger.error("No mapping binded for key: %s", key)
            raise
        else:
            return self.config[section][ini_key]

# ---------------- FREESWITCH XML config update logic ------------------
    def save_fs_conf(self):
        self.logger.info("应用FreeSwitch配置")
        # get current fs config from xmls
        self.get_fs_config()
        # walk thru configuration.ini to get the new remote fs conf 
        fs_config_section = self.config['FreeSWITCH']
        for key in fs_config_section:
            gateway, param = FS_CONF_MAPPING[key.lower()]
            new_conf = fs_config_section[key]
            if(new_conf):
                self.fs_conf[gateway][param]['value'] = new_conf
        
        self.update_config(self.fs_conf)
        self.logger.debug("FS配置写入完成")

    def init_tree_dict_procedure(self):
        for filename in XMLS:
            try:
                self.logger.debug("读取FS配置: %s", self.paths[FilePath.FS_CONF] + filename)
                tree = etree.parse(self.paths[FilePath.FS_CONF] + filename)
            except OSError:
                raise
            else:
                self.tree_dict[tree.getroot()[0].get('name')] = tree

    def parse_fs_config(self):
        def operator_func(element, config_item): 
            config_item['value'] = element.get('value')
        
        self.trees_walker(self.tree_dict, operator_func, self.fs_conf)

    def get_new_fs_config(self):
        self.init_tree_dict_procedure()
        self.parse_fs_config()

    def get_fs_config(self):
        try:
            self.get_new_fs_config()      
        except OSError:
            self.logger.error("FS配置读取失败: %s", traceback.format_exc())
        else:
            self.logger.debug("最新FS配置: %s", self.fs_conf)
            return self.fs_conf

    def update_config(self, new_conf_obj):
        self.logger.debug("写入FS配置")
        def operator_func(element, config_item): 
            element.attrib['value'] = config_item['value']

        self.trees_walker(self.tree_dict,
            operator_func,
            new_conf_obj)

        for name, tree in self.tree_dict.items():
            try:
                tree.write(self.paths[FilePath.FS_CONF] + name + ".xml", pretty_print=True)
            except PermissionError:
                self.logger.error("FS配置写入失败, 配置文件没有写入权限")

    def trees_walker(self, trees, operator_func, fs_conf_obj):
        for tree_name, tree in trees.items():
            # sub_category = conf_obj[conf_type]
            gateway = tree.getroot()[0]
            for element in gateway:
                try:
                    config_item = fs_conf_obj[tree_name][element.get('name')]
                except:
                    continue
                else:
                    operator_func(element, config_item)
            