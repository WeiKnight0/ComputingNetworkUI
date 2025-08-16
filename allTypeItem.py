import copy
from PySide6.QtWidgets import QGraphicsItem, QMenu, QMessageBox
from PySide6.QtGui import QPixmap, QAction
from PySide6.QtCore import Qt, QObject, SignalInstance
from nodeItem import NodeItem
from set_IPConfig_widget import IPConfigWidget
from set_computingNode_widget import SetComputingNodeWidget


# 定义用户节点类，继承自NodeItem
class UserNode(NodeItem):
    def __init__(self, name, index, icon_path, mainwindow, parent=None):
        # 调用父类的构造函数，初始化节点的基本属性
        super().__init__(name, "UserNode", index, icon_path, mainwindow, parent)
        # 任务队列
        self.task_queue = []

    def __getstate__(self):
        # 调用父类的__getstate__方法获取节点的状态
        state = super().__getstate__()
        state["task_queue"] = self.task_queue
        return state

    def __setstate__(self, state):
        # 调用父类的__setstate__方法恢复节点的基本状态
        super().__setstate__(state)
        self.task_queue = state.get("task_queue", [])


    def contextMenuEvent(self, event):
        """
        处理节点的右键菜单事件，显示设置和删除菜单项。

        :param event: 鼠标事件
        """
        # 创建一个右键菜单
        menu = QMenu()

        set_node_action = QAction("任务设置", self.scene())
        set_node_action.triggered.connect(self.show_task_widget)
        menu.addAction(set_node_action)

        # "属性设置"菜单项
        set_node_action = QAction("属性设置", self.scene())
        set_node_action.triggered.connect(self.show_node_widget)
        menu.addAction(set_node_action)
        if not self.mainwindow.scene_editable_state:
            set_node_action.setEnabled(False)

        # "删除节点"菜单项
        delete_action = QAction("删除节点", self.scene())
        delete_action.triggered.connect(self.delete_node)
        menu.addAction(delete_action)

        # 显示菜单
        menu.exec(event.screenPos())

    def show_task_widget(self):
        from set_task_widget import SetTaskWidget
        self.task_widget = SetTaskWidget(self)
        self.task_widget.show()
        self.task_widget.task_updated.connect(self.on_task_updated)

    def on_task_updated(self):
        if hasattr(self, "task_widget"):
            del self.task_widget
        QMessageBox.information(None,"提示",f"{self.name}任务队列设置成功")

    def add_task(self, task_info):
        self.task_queue.append(task_info)

# 定义算力节点类，继承自NodeItem
class ComputingNode(NodeItem):
    def __init__(self, name, index, icon_path, mainwindow, parent=None):
        # 调用父类的构造函数，初始化节点的基本属性
        super().__init__(name, "ComputingNode", index, icon_path, mainwindow, parent)
        # 算力节点特有的属性，存储容量
        self.storage_space = 1024 # 单位：GB
        self.computing_type = 0 # 0表示CPU、1表示GPU
        self.computing_power = 1e9 # 单位：FLOPS
        self.switching_capacitance = 1e-15 # 单位：fF
        self.static_power = 1e-9 # 单位：nW
        self.price = 0.01 # 单位：元/s
        self.power_mix = 100 # 混合能源参数

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
        state["power_mix"] = self.power_mix

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
        self.power_mix = state.get("power_mix", 100)

    def show_node_widget(self):
        self.widget = SetComputingNodeWidget(self)
        self.widget.ui.show()
        self.widget.node_updated.connect(self.on_node_updated)

    def contextMenuEvent(self, event):
        """
        处理节点的右键菜单事件，显示设置和删除菜单项。

        :param event: 鼠标事件
        """
        # 创建一个右键菜单
        menu = QMenu()

        show_status_action = QAction("显示状态", self.scene())
        show_status_action.triggered.connect(self.show_status_widget)
        menu.addAction(show_status_action)

        # "属性设置"菜单项
        set_node_action = QAction("属性设置", self.scene())
        set_node_action.triggered.connect(self.show_node_widget)
        menu.addAction(set_node_action)
        if not self.mainwindow.scene_editable_state:
            set_node_action.setEnabled(False)

        # "删除节点"菜单项
        delete_action = QAction("删除节点", self.scene())
        delete_action.triggered.connect(self.delete_node)
        menu.addAction(delete_action)

        # 显示菜单
        menu.exec(event.screenPos())

    def show_status_widget(self):
        import os
        from compute_node_monitors import ComputeNodePropertyWindow
        json_path = os.path.join(self.mainwindow.PROJECT_DIR, "compute_node_status.json")
        property_widget = ComputeNodePropertyWindow(self,json_path)
        property_widget.exec()

# 定义路由器类，继承自NodeItem
class Router(NodeItem):
    def __init__(self, name, index, icon_path, mainwindow , routerType="Router", parent=None):
        # 调用父类的构造函数，初始化节点的基本属性
        super().__init__(name, routerType, index, icon_path,mainwindow , parent)
        # 路由器特有的属性，IP地址字典
        self.ip_dict = dict()
        # 路由器特有的属性，子网掩码字典
        self.mask_dict = dict()
        # 更新列表
        self.update_dicts()

    def update_dicts(self):
        # 获取当前所有连接的设备
        connected_items = set()
        for channel in self.channelList:
            if channel.start_item == self:
                item = channel.end_item
            elif channel.end_item == self:
                item = channel.start_item
            else:
                raise RuntimeError(f"{self.name}的channel列表出错！\n{self.channelList}")
            connected_items.add(item)

        # 删除channelList中没有的项
        for item in list(self.ip_dict.keys()):  # 使用list()避免在迭代时修改字典
            if item not in connected_items:
                del self.ip_dict[item]
                del self.mask_dict[item]

        # 添加channelList中有但字典中没有的项（初始化为None）
        for item in connected_items:
            if item not in self.ip_dict:
                self.ip_dict[item] = None
                self.mask_dict[item] = None

    def __getstate__(self):
        # 调用父类的__getstate__方法获取节点的状态
        state = super().__getstate__()
        # 将路由器特有的属性添加到状态中
        state["ip_dict"] = self.ip_dict
        state["mask_dict"] = self.mask_dict
        return state

    def __setstate__(self, state):
        # 调用父类的__setstate__方法恢复节点的基本状态
        super().__setstate__(state)
        # 从状态中获取路由器特有的属性
        self.ip_dict = state.get("ip_dict")
        self.mask_dict = state.get("mask_dict")

    # 路由器特有的方法，用于显示节点的设置窗口
    def show_node_widget(self):
        # 创建一个IPConfigWidget对象，传入当前节点
        self.widget = IPConfigWidget(node=self)
        # 显示设置窗口
        self.widget.show()
        # 连接设置窗口的node_updated信号到当前节点的update_node方法
        self.widget.node_updated.connect(self.on_node_updated)

# 定义用户网关类，继承自Router
class UserGateway(Router):
    def __init__(self, name, index, icon_path, mainwindow, parent=None):
        # 调用父类的构造函数，初始化节点的基本属性
        super().__init__(name, index, icon_path, mainwindow, "UserGateway", parent)

# 定义算力网关类，继承自Router
class ComputingGateway(Router):
    def __init__(self, name, index, icon_path, mainwindow, parent=None):
        # 调用父类的构造函数，初始化节点的基本属性
        super().__init__(name, index, icon_path, mainwindow, "ComputingGateway", parent)

# 定义调度决策网关类，继承自NodeItem
class ComputeScheduleNode(NodeItem):
    def __init__(self, name, index, icon_path, mainwindow, parent=None):
        super().__init__(name, "ComputeScheduleNode", index, icon_path, mainwindow, parent)
        self.color = "green"
        self.size = 55