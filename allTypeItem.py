import copy
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QObject, SignalInstance
from nodeItem import NodeItem
from set_userNode_widget import SetUserNodeWidget
from set_userGateway_widget import SetUserGatewayWidget
from set_computingGateway_widget import SetComputingGatewayWidget
from set_IPConfig_widget import IPConfigWidget
from set_computingNode_widget import SetComputingNodeWidget

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
            # 任务队列
            self.task_queue = []

    def __getstate__(self):
        # 调用父类的__getstate__方法获取节点的状态
        state = super().__getstate__()
        # 将用户节点特有的属性添加到状态中
        state["task_highest_limit"] = self.task_highest_limit
        state["task_lowest_limit"] = self.task_lowest_limit
        state["task_queue"] = self.task_queue
        return state

    def __setstate__(self, state):
        # 调用父类的__setstate__方法恢复节点的基本状态
        super().__setstate__(state)
        # 从状态中获取用户节点特有的属性，如果不存在则使用默认值
        self.task_highest_limit = state.get("task_highest_limit", 2.56e6)
        self.task_lowest_limit = state.get("task_lowest_limit", 0)
        self.task_queue = state.get("task_queue", [])

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

    # 添加任务到任务队列
    def add_task(self, task_info):
        self.task_queue.append(task_info)

# 定义算力节点类，继承自NodeItem
class ComputingNode(NodeItem):
    def __init__(self, name, index, icon_path, firstCreate=True, parent=None):
        # 调用父类的构造函数，初始化节点的基本属性
        super().__init__(name, "ComputingNode", index, icon_path, firstCreate, parent)
        if firstCreate == True:
            # 算力节点特有的属性，存储容量
            self.storage_space = 1024 # 单位：GB
            self.computing_type = 0 # 0表示CPU、1表示GPU
            self.computing_power = 1e9 # 单位：FLOPS
            self.switching_capacitance = 1e-15 # 单位：fF
            self.static_power = 1e-9 # 单位：nW
            self.price = 0.01 # 单位：元/s

    def __getstate__(self):
        # 调用父类的__getstate__方法获取节点的状态
        state = super().__getstate__()
        # 将算力节点特有的属性添加到状态中
        state["storage_space"] = self.storage_space
        state['computing_type'] = self.computing_type
        state["computing_power"] = self.computing_power
        state["switching_capacitance"] = self.switching_capacitance
        state["static_power"] = self.static_power
        state["price"] = self.price

        return state

    def __setstate__(self, state):
        # 调用父类的__setstate__方法恢复节点的基本状态
        super().__setstate__(state)
        # 从状态中获取算力节点特有的属性
        self.storage_space = state.get("storage_space", 1024)
        self.computing_type = state.get("computing_type", 0)
        self.computing_power = state.get("computing_power", 1e9)
        self.switching_capacitance = state.get("switching_capacitance", 1e-15)
        self.static_power = state.get("static_power", 1e-9)
        self.price = state.get("price", 0.01)

    def show_node_widget(self):
        self.widget = SetComputingNodeWidget(self)
        # 显示设置窗口
        self.widget.ui.show()

        self.widget.node_updated.connect(self.update_node)

    def update_node(self):
        print(f"节点{self.index}已更新")
        self.update_name()

    # 算力节点特有的方法
    def custom_method(self):
        print("This is a ComputingNode.")


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
class DecisionRouter(NodeItem):
    def __init__(self, name, index, icon_path, firstCreate=True, parent=None):
        super().__init__(name, "DecisionRouter", index, icon_path, firstCreate, parent)
        self.color = "green" 
        self.size = 55        
        self.ip = "111.111.111.111" 
        self.mask = "255.255.255.255"  
        
    def show_node_widget(self):
        from set_decisionRouter_widget import SetNodeConfigWidget
        self.widget = SetNodeConfigWidget(self)
        self.widget.show()
        self.widget.node_updated.connect(self.update_node)
        
    def update_node(self):
        print(f"更新成功: IP={self.ip}, Mask={self.mask}")