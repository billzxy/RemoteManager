from jsonpickle.util import in_dict
from misc.enumerators import VersionInfo, PatchStatus

"""
远端返回的需要被更新的一个版本的数据, 包含:
版本码: version_code version_num
MD5校验码: file_MD5
更新内容备注: remark
远端下放的参数(FS配置之类的): argument_config_map
该版本的更新状态: status (区别于整个更新流程的状态)

注意: 
这个对象是用来管理需要更新的版本的, 
一次更新可能需要更新多个版本,
这个对象的状态status是对应的那些版本的安装状态, 而不是此次更新整体的状态
"""
class PatchObject(object):
    def __init__(self, version_data=None):
        self.version_code = version_data[VersionInfo.VCODE.value] if version_data is not None else None
        self.version_num = version_data[VersionInfo.VNUM.value] if version_data is not None else None
        self.file_MD5 = version_data[VersionInfo.MD5.value] if version_data is not None else None
        self.remark = version_data[VersionInfo.REMARK.value] if version_data is not None else None
        try:
            self.argument_config_map = version_data[VersionInfo.CONFMAP.value]
        except:
            self.argument_config_map = {}
        self.status = PatchStatus.PENDING

    @staticmethod
    def to_dict(patch_obj):
        return {
            "version_code": patch_obj.version_code,
            "version_num": patch_obj.version_num,
            "file_MD5": patch_obj.file_MD5,
            "remark": patch_obj.remark,
            "status": patch_obj.status.value,
            "argument_config_map": patch_obj.argument_config_map
        }
    
    @staticmethod
    def from_dict(in_dict):
        patch_obj = PatchObject()
        patch_obj.version_code = in_dict["version_code"]
        patch_obj.version_num = in_dict["version_num"]
        patch_obj.file_MD5 = in_dict["file_MD5"]
        patch_obj.remark = in_dict["remark"]
        patch_obj.status = PatchStatus(int(in_dict["status"]))
        patch_obj.argument_config_map = in_dict["argument_config_map"]
        return patch_obj

    def set_status(self, new_status):
        self.status = new_status
    
    