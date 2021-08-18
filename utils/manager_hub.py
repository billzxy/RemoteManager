import traceback
"""
this will bind all the singleton managers (with membership) to each others as class members
this huge chunk of terrible copy-pasta code serves solely the purpose of avoiding circular imports
"""
def add_members(manager_instance):
    manager_name = manager_instance.__class__.__name__
    # from utils.db_operator import DBOperator
    if not manager_name == "DBOperator":
        try:
            import utils.db_operator as imported
            setattr(manager_instance, 'db_operator', imported.DBOperator())
        except:
            print(traceback.format_exc())
            pass

    # from processcontroller.processstatus import ProcessManager
    if not manager_name == "ProcessManager":
        try:
            import processcontroller.processstatus as imported
            setattr(manager_instance, 'process_manager', imported.ProcessManager())
        except:
            print(traceback.format_exc())
            pass

     # from heartbeat.heartbeatdata import HeartBeatManager
    if not manager_name == "HeartBeatManager":
        try:
            import heartbeat.heartbeatdata as imported
            setattr(manager_instance, 'heartbeat_manager', imported.HeartBeatManager())
        except:
            print(traceback.format_exc())
            pass

    # from patching.install_manager import InstallManager
    if not manager_name == "InstallManager":
        try:
            import patching.install_manager as imported
            setattr(manager_instance, 'install_manager', imported.InstallManager())
        except:
            print(traceback.format_exc())
            pass

    # from patching.patch_manager import PatchManager
    if not manager_name == "PatchManager":
        try:
            import patching.patch_manager as imported
            setattr(manager_instance, 'patch_manager', imported.PatchManager())
        except:
            print(traceback.format_exc())
            pass

    # from request.request_manager import RequestManager
    if not manager_name == "RequestManager":
        try:
            import request.request_manager as imported
            setattr(manager_instance, 'request_manager', imported.RequestManager())
        except:
            print(traceback.format_exc())
            pass

    # from request.auth_manager import AuthenticationManager
    if not manager_name == "AuthenticationManager":
        try:
            import request.auth_manager as imported
            setattr(manager_instance, 'auth_manager', imported.AuthenticationManager())
        except:
            print(traceback.format_exc())
            pass

    # from request.api import APIManager
    if not manager_name == "APIManager":
        try:
            import request.api as imported
            setattr(manager_instance, 'api_manager', imported.APIManager())
        except:
            print(traceback.format_exc())
            pass

    # from request.encryption import EncryptionManager
    if not manager_name == "EncryptionManager":
        try:
            import request.encryption as imported
            setattr(manager_instance, 'encryption_manager', imported.EncryptionManager())
        except:
            print(traceback.format_exc())
            pass

    # from conf.config import ConfigManager
    if not manager_name == "ConfigManager":
        try:
            import conf.config as imported
            setattr(manager_instance, 'config_manager', imported.ConfigManager())
        except:
            print(traceback.format_exc())
            pass

    #from utils.log_manager import LoggerManager
    if not manager_name == "LoggerManager":
        try:
            import utils.log_manager as imported
            setattr(manager_instance, 'log_manager', imported.LoggerManager())
        except:
            print(traceback.format_exc())

    if not manager_name == "SettingsManager":
        try:
            import settings.settings_manager as imported
            setattr(manager_instance, 'settings_manager', imported.SettingsManager())
        except:
            print(traceback.format_exc())
    # ++++++++++++++++++++++++++++++++++++++++++++
    # # from settings.settings_manager import SettingsManager
    # manager_name = manager_instance.__class__.__name__
    # if not manager_name == "SettingsManager":
    #     try:
    #         import settings.settings_manager as imported
    #         setattr(manager_instance, 'settings_manager', imported.SettingsManager())
    #     except:
    #         print(traceback.format_exc())

    # #from utils.log_manager import LoggerManager
    # if not manager_name == "LoggerManager":
    #     try:
    #         import utils.log_manager as imported
    #         setattr(manager_instance, 'log_manager', imported.LoggerManager())
    #     except:
    #         print(traceback.format_exc())

    # # from conf.config import ConfigManager
    # if not manager_name == "ConfigManager":
    #     try:
    #         import conf.config as imported
    #         setattr(manager_instance, 'config_manager', imported.ConfigManager())
    #     except:
    #         print(traceback.format_exc())
    #         pass

    # # from request.encryption import EncryptionManager
    # if not manager_name == "EncryptionManager":
    #     try:
    #         import request.encryption as imported
    #         setattr(manager_instance, 'encryption_manager', imported.EncryptionManager())
    #     except:
    #         print(traceback.format_exc())
    #         pass

    # # from request.api import APIManager
    # if not manager_name == "APIManager":
    #     try:
    #         import request.api as imported
    #         setattr(manager_instance, 'api_manager', imported.APIManager())
    #     except:
    #         print(traceback.format_exc())
    #         pass

    # # from request.auth_manager import AuthenticationManager
    # if not manager_name == "AuthenticationManager":
    #     try:
    #         import request.auth_manager as imported
    #         setattr(manager_instance, 'auth_manager', imported.AuthenticationManager())
    #     except:
    #         print(traceback.format_exc())
    #         pass

    # # from request.request_manager import RequestManager
    # if not manager_name == "RequestManager":
    #     try:
    #         import request.request_manager as imported
    #         setattr(manager_instance, 'request_manager', imported.RequestManager())
    #     except:
    #         print(traceback.format_exc())
    #         pass

    # # from patching.patch_manager import PatchManager
    # if not manager_name == "PatchManager":
    #     try:
    #         import patching.patch_manager as imported
    #         setattr(manager_instance, 'patch_manager', imported.PatchManager())
    #     except:
    #         print(traceback.format_exc())
    #         pass

    # # from patching.install_manager import InstallManager
    # if not manager_name == "InstallManager":
    #     try:
    #         import patching.install_manager as imported
    #         setattr(manager_instance, 'install_manager', imported.InstallManager())
    #     except:
    #         print(traceback.format_exc())
    #         pass

    # # from heartbeat.heartbeatdata import HeartBeatManager
    # if not manager_name == "HeartBeatManager":
    #     try:
    #         import heartbeat.heartbeatdata as imported
    #         setattr(manager_instance, 'heartbeat_manager', imported.HeartBeatManager())
    #     except:
    #         print(traceback.format_exc())
    #         pass

    # # from processcontroller.processstatus import ProcessManager
    # if not manager_name == "ProcessManager":
    #     try:
    #         import processcontroller.processstatus as imported
    #         setattr(manager_instance, 'process_manager', imported.ProcessManager())
    #     except:
    #         print(traceback.format_exc())
    #         pass

    # # from utils.db_operator import DBOperator
    # if not manager_name == "DBOperator":
    #     try:
    #         import utils.db_operator as imported
    #         setattr(manager_instance, 'db_operator', imported.DBOperator())
    #     except:
    #         print(traceback.format_exc())
    #         pass
# ========================================================
    # from gui.sys_tray import SysTray
    # if not manager_name == "SysTray":
    #     try:
    #         import gui.sys_tray as imported
    #         setattr(manager_instance, 'sys_tray', imported.SysTray())
    #     except:
    #         print(traceback.format_exc())
    #         pass

    #from gui.gui_manager import GUIManager
    # if not manager_name == "GUIManager":
    #     try:
    #         import gui.gui_manager as imported
    #         setattr(manager_instance, 'gui_manager', imported.GUIManager())
    #     except:
    #         print(traceback.format_exc())
    #         pass

    