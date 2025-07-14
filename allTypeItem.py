import copy
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QObject, SignalInstance
from nodeItem import NodeItem
from set_userNode_widget import SetUserNodeWidget
from set_userRouter_widget import SetUserRouterWidget
from set_computingRouter_widget import SetComputingRouterWidget
from set_IPConfig_widget import IPConfigWidget

class UserNode(NodeItem):
    def __init__(self, name, index, icon_path, firstCreate=True, parent=None):
        super().__init__(name, "UserNode", index, icon_path, firstCreate, parent)
        if firstCreate == True:
            # 用户节点特有的属性或行为
            self.task_highest_limit = 2.56e6
            self.task_lowest_limit = 0

    def __getstate__(self):
        state = super().__getstate__()
        state["task_highest_limit"] = self.task_highest_limit
        state["task_lowest_limit"] = self.task_lowest_limit
        return state

    def __setstate__(self, state):
        super().__setstate__(state)
        self.task_highest_limit = state.get("task_highest_limit", 2.56e6)
        self.task_lowest_limit = state.get("task_lowest_limit", 0)

    # 用户节点特有的方法
    def show_node_widget(self):
        self.widget = SetUserNodeWidget(self)
        self.widget.ui.show()

        self.widget.node_updated.connect(self.update_node)

    def update_node(self):
        print(f"IP， 子网掩码，上限，下限分别更新为：{self.ip}, {self.mask}, {self.task_highest_limit}, {self.task_lowest_limit}")

class ComputingNode(NodeItem):
    def __init__(self, name, index, icon_path, firstCreate=True, parent=None):
        super().__init__(name, "ComputingNode", index, icon_path, firstCreate, parent)
        if firstCreate == True:
            # 算力节点特有的属性或行为
            self.storage = 1024 # 其他算力节点的行为

    def __getstate__(self):
        state = super().__getstate__()
        state["storage"] = self.storage
        return state

    def __setstate__(self, state):
        super().__setstate__(state)
        self.storage = state.get("storage")

    def custom_method(self):
        print("This is a ComputingNode.")

class Router(NodeItem):
    def __init__(self, name, index, icon_path, firstCreate=True,routerType="Router", parent=None):
        super().__init__(name, routerType, index, icon_path, firstCreate, parent)
        self.ip_list = []
        self.mask_list = []

    def __getstate__(self):
        state = super().__getstate__()
        state["ip_list"] = self.ip_list
        state["mask_list"] = self.mask_list
        return state

    def __setstate__(self, state):
        super().__setstate__(state)
        self.ip_list = state.get("ip_list")
        self.mask_list = state.get("mask_list")

    # 路由器特有的方法
    def show_node_widget(self):
        self.widget = IPConfigWidget(self)
        self.widget.show()

        self.widget.node_updated.connect(self.update_node)
    
    def update_node(self):
        print(f"update成功，ip_list更新为{self.ip_list}")

class UserRouter(Router):
    def __init__(self, name, index, icon_path, firstCreate=True, parent=None):
        super().__init__(name, index, icon_path, firstCreate, "UserRouter", parent)

class ComputingRouter(Router):
    def __init__(self, name, index, icon_path, firstCreate=True, parent=None):
        super().__init__(name, index, icon_path, firstCreate, "ComputingRouter", parent)

class DecisionRouter(NodeItem):
    def __init__(self, name, index, icon_path, firstCreate=True, parent=None):
        super().__init__(name, "DecisionRouter", index, icon_path, firstCreate, parent)
        if firstCreate == True:
            self.color = "green"
            self.size = 55

    def custom_method(self):
        print("This is a UserRouter.")

