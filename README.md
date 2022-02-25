# 盒子远程运维管理工具

智能盒子的自动更新运维后台程序

功能: 
- 自动发送状态心跳
- 自动检查与安装更新(包括配置下发的更新)
- 维持本地Java与FS服务的运行状态

由张笑颜与郑寅开发

*建议在64位的Windows操作系统下开发使用*

# 调试与编译

### 用 Python 3.8版本

### 首先用pip从`requirements.txt`安装依赖

### 用anaconda从`conda_requirements.txt`安装依赖(建议)
建议整个anaconda的环境, 如果还是有依赖缺失就手动安装吧

### 调试:
调试有这么一个问题: 如果是直接用VSCode的debug功能, 会导致windows的消息提示弹窗(toast)功能失效报错(PyCharm未知), 因此, 为了避免这个问题, 请在调试时候加上`debug`参数:
```
python3 module_manager.py debug
```
使用VSCode调试功能的话, 不能从`entrypoint.py`作为入口调试, 否则IDE的终端因为不是管理员权限, 获取不到输出, 看不到日志, 所以要从`module_manager.py`作为入口调试; 但这样又有个问题, 就是如果遇到需要管理员权限的操作, 可能会报没有权限的错, 那只能建议试试看用管理员权限打开VSCode试试能不能解决这个问题, 不行的话, 就用管理员权限启动一个`cmd`命令行窗口, 然后从`entrypoint.py`调试
```
python3 entrypoint.py debug
```
### 编译:
- 确保`pyinstaller`和`pyinstaller-versionfile`装好了 
  ```
  pip install pyinstaller
  pip install pyinstaller-versionfile
  ```
- 检查根目录下```version.yml```里的版本号等信息
- 生成一个`pyinstaller`用的version file: 
  ```
  create-version-file version.yml --outfile version.txt
  ```
- 编译`entrypoint.exe`可执行文件: 
  ```
  pyinstaller entrypoint.py -F --windowed --uac-admin --icon=./resources/tool-box-64.ico --version-file=version.txt
  ```
- 编译`updater.exe`可执行文件: 
  ```
  pyinstaller self_updater.py -F --uac-admin --icon=./resources/tool-box-64.ico
  ```
- 生成的`exe`在`./dist`目录下

### 运行:
在同一目录下准备以下文件与目录:
- ```entrypoint.exe```编译出来的可执行文件
- 新建```./logs```目录
- ```./model/data.yml```文件
- ```./resources```目录以及四个图标
- ```./settings/settings.ini```设置配置文件(如下)

然后双击`entrypoint.exe`就应该能用了, 日志请在```./logs/out.log```查看

### 运行设置`settings.ini`详解:
**注意: 这个文件必须放置在与本程序`entrypoint.exe`与`updater.exe`所处的同一目录的`./settings/settings.ini`相对路径下, 这是写死的**
*请保证所有配置项目的存在*
```ini
[general]
host_addr=https://www.tongtongcf.com:10007 ; 云平台通讯服务器地址, 用于发送心跳和获取更新状态

env=uat  ; 环境名称, 可以是 local, dev, uat, ymt, prod 中任意一个值
logging=debug  ; 日志输出级别, info, debug等
log_expiration=30  ; 日志保留的天数
debug_mode=on  ; 是否作为debug模式运行, on是开启, off是关闭, debug模式运行不会自动发送心跳与检查版本, 需要手动在系统托盘触发, 而且会开放一些调试功能的触发, 生产环境(给客户安装)下请将这个关闭, 设置为off

[paths] ; 以下路径都是相对路径, 根目录是盒子的安装路径
config=\conf\configuration.ini  ; 盒子的参数配置文件保存的相对路径, 这个配置是类似于appkey等给盒子外呼用的参数
patch=\patch  ; 盒子更新安装所保存的临时文件目录
patchmeta=\patch.meta  ; 盒子更新状态跟踪的文件, 请不要删了
backup=\backup  ; 盒子更新时, 备份文件用的目录
manager_dir=\\RemoteManagerDist  ; 这个运维工具所在的目录

fs=C:\\Program Files\\FreeSWITCH  ; FreeSWITCH的安装绝对路径
fs_conf=\\conf\\sip_profiles\\external\\  ; FreeSWITCH的配置文件路径, 相对于安装路径
java=C:\\Program Files\\java  ; Java的安装绝对路径

java_pid=\\pid.txt  ; java的进程id记录文件的相对路径(相对于盒子安装路径)
jar=\\icb-box.jar  ; 盒子jar包路径
app_yml=\\application.yml  ; 盒子jar包配置文件的路径
path_bat=\\DOS\\start.bat  ; 盒子jar包启动前的环境准备脚本路径
data=\data  ; 盒子的数据库文件路径

manager=\\entrypoint.exe  ; 本程序所在路径, 相对于运维工具存放的绝对路径
updater=\\self_updater.exe  ; 自更新辅助程序的路径
starter=\\start.exe  ; 盒子启动器的路径

[timer]
heartbeat=30  ; 心跳发送的间隔, 单位秒
versionCheck=3600  ; 更新检测的间隔, 单位秒
```


# 设计思路与哲学
其实功能需求不是很复杂, 基本上用几个脚本或函数组合以下成为一套流程就可以了, 但是当时为了追求些代码逻辑的清晰, 代码的可维护性, 和规范性, 导致最后造轮子设计了一套半吊子框架, 结果也不是特别好学习, 维护性也一般, 而且还有些尚未根本解决(规避掉)的问题, 但是也有一些可圈可点的地方, 以下就详细讲讲是怎么设计和实现的, 请结合代码一起看

先讲框架, 再讲各个功能组件

## 框架

设计核心还是面向对象OOP的, 尽管在Python里是个*anti-pattern*, ~~但是本来也就是练练手的~~

这套框架被评价非常有Java味, 事实确实如此, 设计的时候试图借鉴了Java的SpringBoot的许多使用方式, 初衷是希望简化使用, 节省重复的代码量, 尽管实现上与SpringBoot还是差了很多的; ~~不然就拿去开源社区骗星去了~~ 

### Manager and Manager Hub 经理与经理俱乐部
这个程序被划分成许多功能性组件, 比如有的组件专门管日志, 有的组件专门管发送请求, 有的组件专门管更新的管理更新的安装等等; 这套框架的核心, 主要是用一种方式, 把这些组件管理起来, **让它们互相能成为各自的类成员**, 这样可以方便调用其他组件里的方法, 或者交互

这些组件都以单例的形式, 实例化后持续运行, 避免重复对象, 毕竟没必要在需要一个组件的时候重复实例化对象. 这些单例组件, 都被称为"经理"——`Manager`(因为它们都有自己负责的职能)

想要一个组件类成为`Manager`很简单, 只要在类定义的地方给它点缀一个`@Manager`的头衔就行(类似于SpringBoot的注解)

在`./misc/decorators.py`文件里的 `manager()`点缀器, 实现了这个单例的构造方式: 篡改一个类的构造方法, 使它在正常构造步骤前或者后, 执行其他步骤; 这个方法里, 在正常构造这个类之后, 除了将它存在一个字典里(以管理单例)以外, 还有一个`add_members()`的调用(`./utils/manager_hub.py`), 这个步骤叫做`将Manager加入Manager Hub————经理俱乐部`, 具体作用请参考代码内注释.

效果就是: 所有经理都会"加入经理俱乐部", 而且经理俱乐部成员们都有个特权, 就是他们的对象内都引用了其他的经理的对象, 什么意思呢:

首先是需要在`manager_hub.py`里按引用层级顺序(被依赖的放在下层, 不过这里无所谓), 写声明代码:

```python
# manager_hub.py
def add_members(manager_instance):
    manager_name = manager_instance.__class__.__name__
    if not manager_name == "DeliveryManager":
        try:
            import managers as imported
            setattr(manager_instance, 'delivery_manager', imported.DeliveryManager())
        except:
            pass

    if not manager_name == "DevManager":
        try:
            import managers as imported
            setattr(manager_instance, 'dev_manager', imported.DevManager())
        except:
            pass
```

然后是实际声明类定义:

```python
# managers.py
from manager_hub import add_members

# 可以将类注册为经理的点缀器
def manager(cls):
    print("@manager wrapping: ", cls.__name__)
    instances = {}
    def _wrapper(*args, **kwargs):
        if cls not in instances:
            new_obj = cls(*args, **kwargs)
            instances[cls] = new_obj 
            add_members(new_obj)
            return new_obj
        return instances[cls]
    return _wrapper

# 假设我们定义两个经理:
@manager
class DeliveryManager:  # 交付经理
  def receive_product(self, product): # 接受成品
    print("交付产品: ", product)  # 交付产品

@manager
class DevManager:  # 开发经理
  def receive_demand(self, product_demand):  # 接受需求
    print("开发需求: ", product_demand) 
    finished_product = product_demand  # 开发产品
    self.delivery_manager.deliver(finished_product)  # 产品转交交付, delivery_manager已经是在初始化以后成为DevManager实例的一个成员, 可以直接引用
```

实际使用方法:
```python
# 主流程:
# 我们给开发经理一个需求
dev_manager = DevManager()
dev_manager.receive_demand("第一季度开发需求")

# 输出:
# @manager wrapping:  DeliveryManager
# @manager wrapping:  DevManager
# 开发需求:  第一季度开发需求
# 交付产品:  第一季度开发需求

```
以上的伪代码表明, 任何一个俱乐部内的经理都可以用`self`关键字, 在类内部的方法调用其他经, 而不需要在类的构造方法`__init__()`下额外声明

那怎么避免**循环依赖**呢? 因为当时我还不懂SpringBoot注入的原理, 所以用了规避的方法; 

依赖的顺序还是比较重要的, 这个框架不像`SpringBoot`那样可以无视上下级关系, 因此, 建议先理清一个依赖关系, 被依赖的优先级高, 需要放在`manager_hub.py`的声明列表的底层一些

**注意: `SettingsManager`和`LoggerManager`作为框架最基础的依赖, 它们是不能被放进`经理俱乐部`的**


#### `__init__()` and `post_init()`: 经理类的构造方法与构造后方法

这个框架还有个功能, 就是所有经理, 在普通构造方法`__init__()`执行后, 还有个"构造后方法"`post_init()`会被执行

经理类的构造执行顺序是:
1. 先执行该类的`__init__()`方法, 生成一个对象
2. 到`manager_hub.py`的`add_members()`方法, 为该生成的对象添加其他经理对象的引用
3. 再执行`post_init()`方法

这个设计是为了解决啥问题的:

这个是东西的产生, 是因为: 为了实施规避循环依赖措施, 有副作用产生了, 而为了规避这个副作用, 设计了"构造后方法"这个步骤

具体情况就是: 假设某个经理, 需要在构造的时候获取`settings_manager`的一些设置, 如果直接在`__init__()`里调用`self.settings_manager`会出现引用错误; 因为从经理类的构造顺序来看, `settings_manager`的引用, 是在第二步才被存放到这个经理对象的成员里的, 而`__init__()`是第一步就执行的

***所以, 如果想要在构造的时候引用其他任何经理对象的话, 必须放在`post_init()`里***


### 日志框架
还有一个花了点心思设计的, 就是日志框架, 为了给每个类都在不需要额外写代码申明的前提下, 增加调用日志输出的功能

使用方式就是在每个类(可以是任何一个类, 不一定是经理)的声明处添加`@logger`点缀

```python
@logger
class MyClass:
  def __init__(self):
    self.logger.info("Initialized class")  # 甚至可以在构造方法内使用

  def do_something(self):
    self.logger.info("Doing something now")  # 可以直接这么用
    self.debug("Still doing something")  # 也可以这么用, 但是有弊端
```
具体实现请参考`./utils/my_logger.py`

***重要提示: `@logger`的点缀必须放在`@manager`点缀的下面***
```python
# OK
@manager
@logger
class MyManager:
  pass

# NOT OK
@logger
@manager
class MyManager:
  pass
```


#### 日志配置
所有的`logging`库的设置与配置都放在了`./utils/log_manager.py`的`LoggerManager`类里了


## 程序初始化流程

首先讲两个知识点:

1. 引用一个python文件(不管是`import xxx`还是`from xxx import yyy`), 都会执行一遍该文件里的代码

2. 如果用点缀器点缀一个类, 它的执行逻辑是:
```python
def decorator(cls):
  print("wrapping class: ", cls.__name__)
  def wrapped_class(*args, **kwargs):
    print("do something before obj init")
    return cls.__init__(*args, **kwargs)
  return wrapped_class

@decorator
class MyClass:
  print("Compile MyClass")
  def __init__(self):
    print("Init MyClass")

my_obj = MyClass()

"""
输出结果:
Compile MyClass
wrapping class:  MyClass
do something before obj init
Init MyClass
"""
# 这样一个函数定义
@func_decorator
def wrapped_func():
  pass
# 相当于
def func():
  pass
wrapped_func = func_decorator(func())
```

### 框架初始化步骤
- 入口: 从`entrypoint.py`开始, 获取Windows管理员权限
- 运行`module_manager.py`执行`entrypoint()`里的`BoxRemoteManager()`实例化, 但是因为`BoxRemoteManager`类是被`@logger`点缀过, 因此先会到`@logger`的`new_init()`(篡改类的构造方法的函数)里, 首先实例化`LoggerManager`(又因为`LoggerManager`是个点缀过的单例, 所以以后再实例化其他被`@logger`点缀过的类的时候, 拿到的`LoggerManager`对象都是同一个实体)
- 实例化`LoggerManager`的时候, 又会去调用`SettingsManager`的实例化
- 随后完成`BoxRemoteManager`本身的`__init__()`的执行
- 由于`@manager`会"劫持"`BoxRemoteManager`的`__init__()`, 并在它实例化以后调用`add_members()`, 因此会产生一个连锁反应, 所有的经理会按`add_members()`里声明的倒叙去被挨个实例化, 并且反复进入`add_members()`去实例化其他经理, 并且将这些经理的引用收入囊中

### 实例化顺序
前文有提过, 除了`LoggerManager`和`SettingsManager`以外的所有经理, 都需要在`manager_hub.py`的`add_members()`函数里, 定义一个引用声明, 而且它们的顺序最好是越被依赖的, 越要被放在下层

因为经理的`__init__()`实例化顺序, 是跟着`manager_hub.py`的声明代码块的顺序的来的, 而它们的`post_init()`顺序是反过来的; 所以, 越下层(受依赖强)的经理类会先被`post_init()`初始化

**警告: `InstallManager`与`PatchManager`的位置不能发生改变**

`PatchManager`的定义必须在`InstallManager`的下面, 因为`InstallManager`的`post_init()`初始化流程里的一个步骤, 需要依赖`PatchManager`的`post_init()`执行完成.


初始化日志:
```
# 省略了其他无关日志
LOggerManager init #并非由manager_hub启动
SettingsManager init #并非由manager_hub启动
__init__():  BoxRemoteManager
__init__():  DBOperator
__init__():  ProcessManager
__init__():  HeartBeatManager
__init__():  InstallManager
__init__():  PatchManager
__init__():  RequestManager
__init__():  AuthenticationManager
__init__():  APIManager
__init__():  EncryptionManager
__init__():  ConfigManager
post_init():  ConfigManager
post_init():  EncryptionManager
post_init():  APIManager
post_init():  AuthenticationManager
post_init():  RequestManager
post_init():  PatchManager
post_init():  InstallManager
post_init():  HeartBeatManager
post_init():  ProcessManager
post_init():  DBOperator
post_init():  BoxRemoteManager
```

### 重要经理类的文件路径

|类名|路径|作用|
|---|-----|-----|
|SettingsManager        |./settings/setting_manager.py    |管理本程序设置
|LoggerManager          |./utils/log_manager.py           |管理本程序日志配置
|ConfigManager          |./conf/config.py                 |管理盒子和FS参数配置
|EncryptionManager      |./request/encryption.py          |管理文件加密(闲置)
|APIManager             |./request/api.py                 |管理控制请求底层方法
|AuthenticationManager  |./request/auth_manager.py        |管理云平台API的令牌
|RequestManager         |./request/request_manager.py     |管理云平台API的请求
|PatchManager           |./patching/patch_manager.py      |管理更新与版本的状态和进度
|InstallManager         |./patching/install_manager.py    |管理更新的安装和进度
|HeartBeatManager       |./heartbeat/heartbeatdata.py     |管理心跳发送
|ProcessManager         |./processcontroller/processstatus.py |管理盒子各进程的状态监控与启停
|DBOperator             |./utils/db_operator.py           |管理盒子数据库的操作
|其他:
|BoxRemoteManager       |./module_manager.py              |程序本体
|GUIManager             |./gui/gui_manager.py             |系统托盘的handler管理 映射系统托盘菜单选项对应的handler 以及管理配置这些handler的线程
|SysTray                |./gui/sys_tray.py                |系统托盘的菜单列表渲染声明和图标等可视化元素设置


### 综合初始化流程: 建议同时打开各个类所处的文件, 配合代码内注释阅读
1. 读取本程序的设置, 完成日志功能的配置, 由`SettingsManager`与`LoggerManager`管理
2. 读取盒子的参数(`appkey`, 盒子版本号, FreeSwitch的配置等), 由`ConfigManager`管理
3. 初始化一些API请求的配置准备(由`APIManager`获取), 并且拿到`ConfigManager`读出来的`appkey`等参数, 请求获取一次云平台令牌`token`(由`AuthenticationManager`操作)
4. 读取本地存储的安装状态元文件, 加载安装状态, 在`PatchManager`和`InstallManager`初始化完成后由`InstallManager`调用`PatchManager`的`load_meta()`方法触发
5. 检查安装状态元信息, 是否有【自更新】流程尚未走完; 如有, 将会完成自更新流程的最后步骤, 由`ProcessManager`在初始化后调用`InstallManager`的`post_installation_cleanup()`达成, 具体的自更新流程会在后文细讲
6. 如果在`settings.ini`内的`debug_mode`是`off`的话, `ModuleManager`会启动定时器, 执行首次的心跳包发送和版本检查流程
7. `ModuleManager`会调用`GUIManager`, 调用`SysTray`, 启动右下角系统托盘
8. 完成初始化


## 盒子更新与自更新流程

盒子的更新和自更新基本上属于是本程序的业务核心, 因此会重点分析一下, 请结合`PatchManager`,`InstallManager`和`self_updater.py`脚本源代码

### 盒子更新流程:
盒子更新流程需要负责的文件和功能:
- 更新`SQLite`数据库:
  - 执行`SQLite`的`.sql`脚本
- 更替盒子JAR包
- 更替盒子JAR包所依赖的YAML配置文件
- 执行命令行命令(尚未实现该功能)
- 应用远程下发的盒子配置, 保存在`configuration.ini`文件中
  - 配置会先保存在`configuration.ini`文件中, 然后等安装流程完成, 更新流程收尾的时候, 再保存配置到FS的各个XML文件中, 最后启动FS应用配置
- 自更新文件:
  - `start.exe` 盒子启动程序
  - `updater.exe` 自更新辅助程序
  - `settings.ini` 本运维管理程序的设置配置文件
  - `entrypoint.exe` 本运维管理程序本体

更新流程分很多个态, 这些态被定义在`./misc/enumerators.py`文件的`PatchCyclePhase`枚举类中:
```python
READY = 0  # 【准备完毕】初态, 准备开始下一次更新流程, 或者暂无更新
INCEPTION = 1  # 【开始】更新流程的开始, 表明有新的更新
DOWNLOAD = 2  # 【下载中】正在下载的过程中, 也有可能是下载好了在解压
PENDING = 3  # 【等待安装】安装包准备完成, 等待安装开始
BACKUP_CREATED = 4  # 【备份完毕】备份已经完成
FILES_UPDATED = 5  # 【文件已更替】所有安装包需要安装的文件已完成更替
SELF_UPDATE_PENDING = 6  # 【等待自更新】更新的内容中包含自更新
SELF_UPDATE_COMPLETE = 7  # 【自更新完成】
COMPLETE = 8  # 【更新流程完成】终态 仅作记录用 不会影响流程
ROLLEDBACK = 9  # 【回滚】
```
(代码中, `state`和`phase`这两个词都用来形容了`态`, 尽管从英语语言上来说, 两个词稍微有区别, 但是我写代码的时候就随便用了下, 所以就请当它俩是一个东西)
这些态会在一部分流程结束后被更新然后保存在本地, 默认保存在`.../盒子安装路径/patch/patch.meta`文件内, 以避免发生程序以外终止时刻造成的工作丢失与混乱; 这些态也决定了程序会从哪部分流程开始执行, 这意味着就算程序意外终止或出现异常, 再度启动时, 会根据态, 直接跳到那部分流程执行; 所以也可以直接通过本地修改状态元文件去控制更新流程

更新有时候是一次需要更新多个子版本, (比如跨版本更新, 不能直接从1.1升级到1.3, 需要从1.1升到1.2再升到1.3的情况) 这样的话, 每个子版本的更新状态都需要单独管理, 因此, 专门有个类负责子版本状态的管理, `./patching/patch_obj.py`里的`PatchObject`, 子版本自己的态的枚举如下:
```python
PENDING = 0  # 【等待下载】最初态
DOWNLOADING = 1  # 【正在下载】
DOWNLOADED = 2  # 【下载完成, 等待安装】
INSTALLED = 3  # 【安装完成】
REVERTED = 4  # 【回滚】
```

`更新流程`里的后半部分, 既`更新的安装流程`, 是个相对独立的子流程, 下文简称`安装流程`(`自更新流程`也包含在`安装流程`内) `更新流程`执行完下载等工作后, 会开始执行`安装流程`

`更新流程`的下载部分有一个兜底机制, 就是如果**由于任何原因导致更新流程的终止**, 将会记录失败次数, 再次尝试将会从失败的流程部分开始重来, 失败次数如果超过5次, 则将整个更新流程恢复到最初态, 全部重来

### 更新流程

1. 开始更新流程, 进入更新流程的方式有两种:
    - 定时器触发, 会上锁(与`心跳发送`和`安装流程`互斥)
    - 从系统托盘菜单手动触发(仅`调试模式`下可用), 同样会上锁

2. `更新流程态`最初处于`READY`或`COMPLETE`态, 检查是否有可用更新:
    - 无, 则流程结束(返回1)
    - 有, 解析出需要更新的内容, 子版本的数量与信息等, `更新流程态`变更为`INCEPTION`

3. `更新流程态`处于`INCEPTION`态, 开始下载流程:
    1. 根据解析出的更新内容, 循环遍历各个子版本:
        1. 请求接口下载文件
            - 有文件, 下载
            - 无文件, 直接跳过, 修改`子版本态`为`DOWNLOADED`(说明可能只是配置下发, 而不是程序更新)
        2. 校验MD5
            - 成功, 继续
            - 失败, `更新流程态`退回`INCEPTION`, **终止此次更新流程**(直接返回0)
        3. 解压
            - 成功, 记录`子版本态`为`DOWNLOADED`
            - 失败, 退回`子版本态`到`PENDING`
    2. 各个子版本下载完成后, `更新流程态`改为`PENIDNG`
    3. 判断是否是【强制更新】:
        - 否, 重置失败次数记录, 提示用户手动触发`安装流程`, 正常结束退出`更新流程`(返回1)
        - 是, 自动跳转到`安装流程`, 等完成后, 再重置失败次数记录
### 安装流程
1. 开始`安装流程`, 进入的方式有两种:
    - 由`更新流程`调用直接进去, 不用上锁(已经是用了之前`更新流程`的锁)
    - 手动触发, 这时候上的是`安装流程`的锁, 与`更新流程`和`心跳发送`互斥

2. 判断`更新流程态`是否为`DOWNLOAD`或`COMPLETE`:
    - 是, 则没有需要安装的更新, 正常退出(返回1)
    - 否, 则有已经下载好的更新需要安装, 继续下一步

3. 请求云平台接口暂停所有待执行任务, 并且判断是否有正在呼叫的任务
    - 有, 抛`UpdateIsNoGo`异常, 终止此次安装流程(返回0)
    - 无, 停止Java和FS的进程, 并且继续

4. 创建备份, `更新流程态`进入`BACKUP_CREATED`
    - 下面的步骤任何一步出现异常退出(返回0)或者异常拦截, 则将备份文件全部复原, 记录退回完整`更新流程`开始前的版本(并非上一个`子版本`), `更新流程态`进入`ROLLEDBACK`

5. `更新流程态`处于`BACKUP_CREATED`, 循环遍历子版本, 按顺序替换子版本的文件
    - 修改`子版本态`为`INSTALLED`
    - 完成全部子版本的替换后, `更新流程态`进入`FILES_UPDATED`
    - 如果需要更新`entrypoint.exe`, 暂作标记, `更新流程态`进入`SELF_UPDATE_PENDING`

6. `更新流程态`处于`SELF_UPDATE_PENDING`, 由第`5.`步触发, 则启动`updater.exe`, 该进程会终结本程序`entrypoint.exe`的进程, 因此`安装流程`会在这里终结, 执行`自更新流程`的流程, 完成后跳到第`8.`步执行

7. `更新流程态`处于`ROLLEDBACK`, 则表明之前有出错回滚了文件
    - 把所有`子版本态`改为`DOWNLOADED`
    - 将`更新流程态`改为`PENDING`
    - 启动盒子的Java进程和FS进程
    - 请求云平台, 恢复已暂停的外呼任务
    - 结束更新流程

8. `更新流程态`处于`FILES_UPDATED`, 则表明安装流程已经完成, 会进行最后的收尾工作:
    - 将之前存到`configuration.ini`里的FS配置, 保存到FS安装目录下的XML配置文件内
    - 将`更新流程态`改为`COMPLETE`
    - 启动盒子的Java进程和FS进程
    - 请求云平台, 恢复已暂停的外呼任务
    - 将`更新流程态`改为`READY`, 完成一次完整的更新流程
    
### 自更新流程:
`自更新流程`是为了更替本程序的可执行`entrypoint.exe`而设计的, 需要借助`updater.exe`完成, 源码位于`./self_updater.py`

1. `updater.exe`被`entrypoint.exe`启动
2. 从`./settings/settings.ini`获取更新状态元文件路径与配置信息, 读取`更新流程态`
3. 终止`entrypoint.exe`进程
4. 更替`entrypoint.exe`文件
5. 修改`patch.meta`元文件, 保存`更新流程态`为`SELF_UPDATE_COMPLETE`
6. 启动`entrypoint.exe`
7. 执行完成, `updater.exe`退出
8. `entrypoint.exe`启动后, 会执行各个经理类的实例化, 在`ProcessManager`类实例化的时候, 会调用`InstallManager`的`check_self_update_follow_up()`, 判断元文件内保存的`更新流程态`是否为`SELF_UPDATE_COMPLETE`, 如果是的, 则进行上文`安装流程`的第`8.`步内的操作
9. 完成自更新流程的全部流程

## 安装包的组装:
安装包是一个任意命名的`.zip`压缩包, 所有需要更新的东西都要按下面的目录结构, **直接放在压缩包的根目录**, 就是说, 压缩包打开来就是林林总总的东西, 不能是打开来还有个文件夹, 再打开里面才是东西

压缩包里的东西, 就是需要更新什么就把什么压缩进去, 比如只要更替JAR包, 就放一个JAR包; 需要更新JAR包以及数据库, 那就放JAR包和`.sql`文件; 需要更新远程运维管理工具的可执行, 就放`entrypoint.exe`; 但是注意, 文件一定要放在指定的位置, 请参考下面的目录结构规则


### 目录结构规则: 
```
/patch_dir
|----- /data 
|      |----- db_update.sql  # 要执行的SQL脚本放在名称为 `/data` 的目录下, 用法详见下文 
|      |----- ztdb-versionX  # 这个是SQLite数据库文件, 直接更库, 用法详见下文
|    
|----- application.yml  # JAR包的YAML配置文件
|
|----- icb-box.jar  # JAR包
|
|----- start.exe  # 盒子启动程序
|
|----- entrypoint.exe  # 远程运维工具
|
|----- updater.exe  # 远程运维工具的自更新辅助程序
|
|----- settings.ini  # 远程运维工具的新配置文件, 用法详见下文

```

#### SQL脚本注意事项:
- 文件的最开始一定要加上`BEGIN TRANSACTION;` 因为安装流程有做事务处理, 需要手动触发事务的开启

#### SQLite数据库源文件注意事项:
一般不做数据库源文件的直接替换, 但是如果需要做这件事情的话, 记得在盒子的远程运维平台(发布更新的Web服务)上新增版本的时候, 添加一个额外的参数键: `dbfileName`, 然后值填写的就是文件的名称, 例如`ztdb-version3`; 这个参数会作为远程下发参数, 被写入`configuration.ini`里, 最后在启动时候更新到`application.yml`里; 远程参数的对照表参照`./conf/consts.py`的`REMOTE_CONF_MAPPING`

#### `settings.ini`配置文件注意事项:
如果需要自更新, 随之而需要更新`settings.ini`的配置项, 则需要新建一个`settings.ini`文件, 然后**只需要在文件里填写新增或者修改的项目**, 其他不需要修改的项目则不用写进去, 例如:

我们现在需要新增一个参数`[general] new_setting`, 修改一个参数`[paths] jar`(jar包路径):
```ini
[default]
new_setting = some value

[paths]
jar=\\jar\\icb-box.jar

; 其他的都不需要管了
```
