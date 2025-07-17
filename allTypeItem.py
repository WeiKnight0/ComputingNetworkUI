import copy
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QObject, SignalInstance
from nodeItem import NodeItem
from set_userNode_widget import SetUserNodeWidget
from set_userGateway_widget import SetUserGatewayWidget
from set_computingGateway_widget import SetComputingGatewayWidget
from set_IPConfig_widget import IPConfigWidget
# from temp.allTypeItem import DecisionRouter


# 定义用户节点类，继承自NodeItem
class UserNode(NodeItem):
    def __init__(self, name, index, icon_path, firstCreate=True, parent=None):
        # 调用父类的构造函数，初始化节点的基本属性
        super().__init__(name, "UserNode", index, icon_path, firstCreate, parent)
        if firstCreate == True:
            # 用户节点特有的属性，任务的最高限制
            self.task_highest_limit = 2.56e6
            # 用户节点特有的属性，任务的最低限制
            self.task_lowest_limit = 0

    def __getstate__(self):
        # 调用父类的__getstate__方法获取节点的状态
        state = super().__getstate__()
        # 将用户节点特有的属性添加到状态中
        state["task_highest_limit"] = self.task_highest_limit
        state["task_lowest_limit"] = self.task_lowest_limit
        return state

    def __setstate__(self, state):
        # 调用父类的__setstate__方法恢复节点的基本状态
        super().__setstate__(state)
        # 从状态中获取用户节点特有的属性，如果不存在则使用默认值
        self.task_highest_limit = state.get("task_highest_limit", 2.56e6)
        self.task_lowest_limit = state.get("task_lowest_limit", 0)

    # 用户节点特有的方法，用于显示节点的设置窗口
    def show_node_widget(self):
        # 创建一个SetUserNodeWidget对象，传入当前节点
        self.widget = SetUserNodeWidget(self)
        # 显示设置窗口
        self.widget.ui.show()

        # 连接设置窗口的node_updated信号到当前节点的update_node方法
        self.widget.node_updated.connect(self.update_node)

    # 用户节点特有的方法，用于更新节点的属性
    def update_node(self):
        print(
            f"IP， 子网掩码，上限，下限分别更新为：{self.ip}, {self.mask}, {self.task_highest_limit}, {self.task_lowest_limit}")


# 定义算力节点类，继承自NodeItem
class ComputeNode(NodeItem):
    def __init__(self, name, index, icon_path, firstCreate=True, parent=None):
        # 调用父类的构造函数，初始化节点的基本属性
        super().__init__(name, "ComputeNode", index, icon_path, firstCreate, parent)
        if firstCreate == True:
            # 算力节点特有的属性，存储容量
            self.storage = 1024  # 其他算力节点的行为

    def __getstate__(self):
        # 调用父类的__getstate__方法获取节点的状态
        state = super().__getstate__()
        # 将算力节点特有的属性添加到状态中
        state["storage"] = self.storage
        return state

    def __setstate__(self, state):
        # 调用父类的__setstate__方法恢复节点的基本状态
        super().__setstate__(state)
        # 从状态中获取算力节点特有的属性
        self.storage = state.get("storage")

    # 算力节点特有的方法
    def custom_method(self):
        print("This is a ComputeNode.")


# 定义路由器类，继承自NodeItem
class Router(NodeItem):
    def __init__(self, name, index, icon_path, firstCreate=True, routerType="Router", parent=None):
        # 调用父类的构造函数，初始化节点的基本属性
        super().__init__(name, routerType, index, icon_path, firstCreate, parent)
        # 路由器特有的属性，IP地址列表
        self.ip_list = []
        # 路由器特有的属性，子网掩码列表
        self.mask_list = []

    def __getstate__(self):
        # 调用父类的__getstate__方法获取节点的状态
        state = super().__getstate__()
        # 将路由器特有的属性添加到状态中
        state["ip_list"] = self.ip_list
        state["mask_list"] = self.mask_list
        return state

    def __setstate__(self, state):
        # 调用父类的__setstate__方法恢复节点的基本状态
        super().__setstate__(state)
        # 从状态中获取路由器特有的属性
        self.ip_list = state.get("ip_list")
        self.mask_list = state.get("mask_list")

    # 路由器特有的方法，用于显示节点的设置窗口
    def show_node_widget(self):
        # 创建一个IPConfigWidget对象，传入当前节点
        self.widget = IPConfigWidget(self)
        # 显示设置窗口
        self.widget.show()

        # 连接设置窗口的node_updated信号到当前节点的update_node方法
        self.widget.node_updated.connect(self.update_node)

    # 路由器特有的方法，用于更新节点的属性
    def update_node(self):
        print(f"update成功，ip_list更新为{self.ip_list}")


# 定义用户网关类，继承自Router
class UserGateway(Router):
    def __init__(self, name, index, icon_path, firstCreate=True, parent=None):
        # 调用父类的构造函数，初始化节点的基本属性
        super().__init__(name, index, icon_path, firstCreate, "UserGateway", parent)


# 定义算力网关类，继承自Router
class ComputingGateway(Router):
    def __init__(self, name, index, icon_path, firstCreate=True, parent=None):
        # 调用父类的构造函数，初始化节点的基本属性
        super().__init__(name, index, icon_path, firstCreate, "ComputingGateway", parent)


# 定义调度决策网关类，继承自NodeItem
class ComputeScheduleNode(NodeItem):
    def __init__(self, name, index, icon_path, firstCreate=True, parent=None):
        # 调用父类的构造函数，初始化节点的基本属性
        super().__init__(name, "ComputeScheduleNode", index, icon_path, firstCreate, parent)
        if firstCreate == True:
            # 调度决策网关特有的属性，颜色
            self.color = "green"
            # 调度决策网关特有的属性，大小
            self.size = 55

    # 调度决策网关特有的方法
    def custom_method(self):
        print("This is a UserGateway.")

