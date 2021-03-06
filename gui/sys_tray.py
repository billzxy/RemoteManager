import traceback
import pathlib, sys
from utils.my_logger import logger
from PyQt5.QtGui import * 
from PyQt5.QtWidgets import * 


@logger
class SysTray:
    def __init__(self, app, gui_manager, **executables):
        self.app = app
        curr_script_path = pathlib.Path(__file__).parent.absolute()
        # Adding an icon
        icon_path = ".\\resources\\fast.ico" if not gui_manager.settings_manager.dev_mode else ".\\resources\\cogger.ico"
        icon = QIcon(icon_path)
        # Adding item on the menu bar
        self.tray = QSystemTrayIcon()
        self.tray.setToolTip("智能精灵运维管理")
        self.tray.setIcon(icon)
        self.tray.setVisible(True)
        self.icon_flag = True
        
        self.logger.info("加载系统托盘菜单")
        # Creating the options
        menu = QMenu()
        self.update_menu = menu.addMenu("更新")
        self.debug_menu = menu.addMenu("调试") if gui_manager.settings_manager.dev_mode else ""
        menus = {
            'update': self.update_menu,
            'debug': self.debug_menu
        }
        update_actions = [
            {'title': '安装更新', 'fn': 'installUpdate', 'menu':'update'},
            {'title': '清除缓存', 'fn': 'clearCache', 'menu':'update'},
            {'title': '获取口令', 'fn': 'getUserToken', 'menu':'debug'},
            {'title': '重载配置', 'fn': 'updateConfig', 'menu':'debug'},
            {'title': '心跳发送', 'fn': 'sendHeartbeat', 'menu':'debug'},
            {'title': '检查更新', 'fn': 'getVersionCheck', 'menu':'debug'},
            {'title': '版本回退', 'fn': 'revertToLast', 'menu':'debug'}
        ]
        # print(fns)
        self.action_execution_list = []
        self.executables = executables
        for index, action in enumerate(update_actions):
            option = QAction(action['title'], self.app)
            option.triggered.connect(lambda _, index=index: self.execute_action_by_index(index))
            if gui_manager.settings_manager.dev_mode:
                menus[action['menu']].addAction(option)
            else:
                if not action['menu']=='debug':
                    menus[action['menu']].addAction(option)
                
            self.action_execution_list.append(self.executables[action['fn']])
        
        start_qthz_action = QAction("启动精灵")
        start_qthz_action.triggered.connect(executables['startQTHZ'])
        menu.addAction(start_qthz_action)

        # icon_action = QAction("变变变")
        # icon_action.triggered.connect(self.change_icon)
        # menu.addAction(icon_action)

        # To quit the app
        quit = QAction("退出")
        quit.triggered.connect(lambda: executables['safeExit'](self.exit_gracefully))
        menu.addAction(quit)
        
        # Adding options to the System Tray
        self.tray.setContextMenu(menu)
        self.app.exec_()


    def execute_action_by_index(self, index):
        executable = self.action_execution_list[index]
        fn_threaded_action = executable['fn']
        kwargs = executable['kwargs']
        fn_threaded_action(**kwargs)

    def change_icon(self):
        icon_path = ".\\resources\\fast.ico" if self.icon_flag else ".\\resources\\tool-box-64.ico"
        icon = QIcon(icon_path)
        self.logger.debug(icon_path)
        self.tray.setIcon(icon)
        self.icon_flag = not self.icon_flag

    def exit_gracefully(self):
        print("退出")
        self.app.quit()
    
