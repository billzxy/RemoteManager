import sys

from elevate import elevate
from module_manager import entrypoint

"""
程序的入口, 
主要功能是获取管理员权限,
编译为可执行的话, 也需要从该文件编译
调试代码可以直接从 module_manager 的 main() 走
"""

def is_admin():
	try:
		return ctypes.windll.shell32.IsUserAnAdmin()
	except:
		return False

if not is_admin():
	elevate(show_console=False)

entrypoint()