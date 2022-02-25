from enum import Enum
from functools import total_ordering

class Envs(Enum):
    LOCAL = 'local'
    DEV = 'dev'
    SIT = 'sit'
    UAT = 'uat'
    YMT = 'ymt'
    PROD = 'prod'

class FilePath(Enum):
    CONFIG = "config"
    FS = 'fs'
    FS_CONF = 'fs_conf'
    JAVA = 'java'
    JAR = 'jar'
    JAVA_PID = 'java_pid'
    PATH_BAT = 'path_bat'
    APP_YML = "app_yml"
    MANAGER = "manager"
    UPDATER = "updater"
    STARTER = "starter"

class SettingsCategories(Enum):
    GENERAL = 'general'
    PATHS = 'paths'
    TIMER = 'timer'

class SettingsItems(Enum):
    # general
    HOST_ADDR='host_addr'
    ENV = 'env'
    LOGGING = 'logging'
    LOG_EXP = 'log_expiration'

    # paths
    CONFIG = 'config'
    PATCH = 'patch'
    PATCHMETA = 'patchmeta'
    MANAGER_DIR = "manager_dir"
    FS = 'fs'
    FS_CONF = 'fs_conf'

    JAVA = 'java'
    JAVA_PID = 'java_pid'
    JAR = 'jar'
    PATH_BAT = 'path_bat'
    APP_YML = 'app_yml'
    MANAGER = "manager"
    UPDATER = "updater"
    STARTER = "starter"

    # timer
    HB = 'heartbeat'
    VC = 'versionCheck'

class UpgradeMark(Enum):
    INITIAL = -1
    NOTAVAILABLE = 0
    OPTIONAL = 1
    MANDATORY = 2

class VersionInfo(Enum):
    VCODE = 'versionCode'
    VNUM = 'versionNum'
    MD5 = 'fileMd5'
    REMARK = 'remark'
    STAT = 'status'
    CONFMAP = 'argumentConfigMap'

class FS_Status(Enum):
    OTHER = -1
    FAIL_WAIT = 0
    REGED = 1
    NO_REG = 2


# 一个主要更新流程的所有态
@total_ordering
class PatchCyclePhase(Enum):
    READY = 0  # 【准备完毕】初态, 准备开始下一次更新流程, 或者暂无更新
    INCEPTION = 1  # 【开始】更新流程的开始, 表明有新的更新
    DOWNLOAD = 2  # 【下载中】正在下载的过程中, 也有可能是下载好了在解压
    PENDING = 3  # 【等待安装】安装包准备完成, 等待安装开始
    BACKUP_CREATED = 4  # 【备份完毕】备份已经完成
    FILES_UPDATED = 5  # 【文件已更替】所有安装包需要安装的文件已完成更替
    SELF_UPDATE_PENDING = 6  # 【等待自更新】
    SELF_UPDATE_COMPLETE = 7  # 【自更新完成】
    COMPLETE = 8  # 【更新流程完成】
    ROLLEDBACK = 9  # 【回滚】
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

class PatchStatus(Enum):
    PENDING = 0  # 【等待下载】最初态
    DOWNLOADING = 1  # 【正在下载】
    DOWNLOADED = 2  # 【下载完成, 等待安装】
    INSTALLED = 3  # 【安装完成】
    REVERTED = 4  # 【回滚】

class TaskStatusRequestSignal(Enum):
    PAUSE = 1
    RESUME = 2

class GetTasksAPIType(Enum):
    UNFINISHED = "未完成"
    PAUSED = "已暂停"

class ThreadLock(Enum):
    HEARTBEAT = 'heartbeat'
    VERSION_CHECK = 'version_check'
    GET_TOKEN = 'get_token'
    INSTALL_UPDATE = 'install_update'
