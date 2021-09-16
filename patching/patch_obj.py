from jsonpickle.util import in_dict
from misc.enumerators import VersionInfo, PatchStatus

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
    
    