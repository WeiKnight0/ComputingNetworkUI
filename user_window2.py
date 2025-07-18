# This Python file uses the following encoding: utf-8
import gc
import os
import pickle
import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsItem,
    QListWidget,
    QMenu,
    QGraphicsProxyWidget,
    QLineEdit,
    QMessageBox,
    QFileDialog,
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt, QPointF, QRectF, QLineF, QEvent
from PySide6.QtGui import (
    QPixmap,
    QPen,
    QColor,
    QTransform,
    QAction,
    QKeySequence,
    QShortcut,
    QUndoCommand,
    QUndoStack,
)

from channel import Channel, ChannelInfo
from nodeItem import NodeItem
from allTypeItem import (
    UserNode,
    UserGateway,
    ComputeNode,
    ComputingGateway,
    Router,
    ComputeScheduleNode,
)
import omnet_file_utils

uiLoader = QUiLoader()


class UserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.undo_stack = QUndoStack(self)
        self.ui = uiLoader.load("design_window.ui")
        self.scene = QGraphicsScene()
        self.ui.graphicsView.setScene(self.scene)

        # 设置右键菜单
        self.ui.listWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.listWidget.customContextMenuRequested.connect(self.show_context_menu)

        # 存储节点和连线
        self.nodes = []
        self.channels = []
        self.is_alt_pressed = False  # 记录 Alt 键是否被按住
        self.start_item = None  # 用于记录连线的起点
        self.clipboard = None  # 初始化剪贴板

        # 用字典记录各类节点的数量
        self.typeNumDict = {
            "UserNode": 0,
            "ComputeNode": 0,
            "UserGateway": 0,
            "ComputingGateway": 0,
            "ComputeScheduleNode": 0,
            "Router": 0,
        }

        # 安装事件过滤器
        self.ui.graphicsView.viewport().installEventFilter(self)
        # self.installEventFilter(self)
        # self.setFocusPolicy(Qt.StrongFocus)  # 确保窗口可以接收键盘焦点

        # 获取菜单项
        self.submit_action = self.ui.findChild(QAction, "actionsubmit")
        self.clear_action = self.ui.findChild(QAction, "actionclear")
        self.save_action = self.ui.findChild(QAction, "actionsave")
        self.load_action = self.ui.findChild(QAction, "actionload")

        # 连接菜单项的事件
        self.submit_action.triggered.connect(self.on_submit)
        self.clear_action.triggered.connect(self.on_clear)
        self.save_action.triggered.connect(self.on_save)
        self.load_action.triggered.connect(self.on_load)

        # 添加快捷键
        # 全选（CTRL + A）
        self.select_all_shortcut = QShortcut(
            QKeySequence("Ctrl+A"), self.ui.graphicsView
        )
        self.select_all_shortcut.activated.connect(self.select_all)
        # 撤销（CTRL + Z）
        self.undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self.ui.graphicsView)
        self.undo_shortcut.activated.connect(self.undo)
        # 还原（CTRL + Y）
        self.redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), self.ui.graphicsView)
        self.redo_shortcut.activated.connect(self.redo)
        # 复制（CTRL + C)
        self.copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self.ui.graphicsView)
        self.copy_shortcut.activated.connect(self.copy)
        # 粘贴（CTRL + V）
        self.paste_shortcut = QShortcut(QKeySequence("Ctrl+V"), self.ui.graphicsView)
        self.paste_shortcut.activated.connect(self.paste)
        # 剪切(CTRL + X)
        self.cut_shortcut = QShortcut(QKeySequence("Ctrl+X"), self.ui.graphicsView)
        self.cut_shortcut.activated.connect(self.cut)

    def eventFilter(self, obj, event):
        # print("eventFilter函数启动")
        # 捕获 Alt 键的按下和释放

        # 处理鼠标事件
        if obj == self.ui.graphicsView.viewport():
            if event.type() == QEvent.Type.MouseButtonPress:
                self.mouse_press_event(event)
                if event.button() == Qt.RightButton:
                    scene_pos = self.ui.graphicsView.mapToScene(event.pos())
                    items = self.scene.items(scene_pos)
                    if not items:
                        self.show_view_context_menu(event.pos())
                        return True
                return super().eventFilter(obj, event)
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self.mouse_release_event(event)
        return super().eventFilter(obj, event)

    def show_context_menu(self, pos):
        item = self.ui.listWidget.itemAt(pos)
        if not item:
            return

        # 创建右键菜单
        menu = QMenu()
        add_action = QAction("添加", self)
        add_action.triggered.connect(lambda: self.add_node(item))
        menu.addAction(add_action)
        menu.exec(self.ui.listWidget.mapToGlobal(pos))

    def show_view_context_menu(self, pos):
        menu = QMenu()

        select_all_action = QAction("全选", self)
        select_all_action.triggered.connect(self.select_all)
        menu.addAction(select_all_action)

        # 分割线
        menu.addSeparator()

        undo_action = QAction("撤销", self)
        undo_action.triggered.connect(self.undo)
        undo_action.setEnabled(self.undo_stack.canUndo())
        menu.addAction(undo_action)

        redo_action = QAction("还原", self)
        redo_action.triggered.connect(self.redo)
        redo_action.setEnabled(self.undo_stack.canRedo())
        menu.addAction(redo_action)

        # 分割线
        menu.addSeparator()

        copy_action = QAction("复制", self)
        copy_action.triggered.connect(self.copy)
        copy_action.setEnabled(len(self.scene.selectedItems()) > 0)
        menu.addAction(copy_action)

        paste_action = QAction("粘贴", self)
        paste_action.triggered.connect(self.paste)
        paste_action.setEnabled(self.clipboard is not None and len(self.clipboard) > 0)
        menu.addAction(paste_action)

        cut_action = QAction("剪切", self)
        cut_action.triggered.connect(self.cut)
        cut_action.setEnabled(len(self.scene.selectedItems()) > 0)
        menu.addAction(cut_action)

        menu.exec(self.ui.graphicsView.mapToGlobal(pos))

    def add_node(self, list_item):
        # 根据ListWidget的item生成节点
        icon_path = f"icon/{list_item.text().lower().replace(' ', '_')}.png"
        nodetype = self.getNodeType(list_item.text())

        command = AddNodeCommand(self, list_item.text(), nodetype, icon_path)
        self.undo_stack.push(command)

    def undo(self):
        self.undo_stack.undo()

    def redo(self):
        self.undo_stack.redo()

    def select_all(self):
        for node in self.nodes:
            node.setSelected(True)
        for channel in self.channels:
            channel.setSelected(True)

    def copy(self):
        selected_items = self.scene.selectedItems()

        nodes = [item for item in selected_items if isinstance(item, NodeItem)]
        channels = [item for item in selected_items if isinstance(item, Channel)]

        related_channels = []
        for channel in channels:
            if channel.start_item in nodes and channel.end_item in nodes:
                related_channels.append(channel)

        if nodes:
            self.clipboard = {"nodes": nodes, "channels": related_channels}

            print(f"已复制{len(nodes)} 个节点和 {len(channels)} 个链路")

        else:
            self.clipboard = None

    def paste(self):
        if (
            not hasattr(self, "clipboard")
            or not self.clipboard
            or not self.clipboard["nodes"]
        ):
            return

        print("粘贴开始")

        command = PasteCommand(self, self.clipboard)
        self.undo_stack.push(command)

    def cut(self):
        selected_items = self.scene.selectedItems()

        # 过滤出节点和链路
        nodes = [item for item in selected_items if isinstance(item, NodeItem)]
        channels = [item for item in selected_items if isinstance(item, Channel)]

        if not nodes and not channels:
            return

        self.clipboard = {"nodes": nodes, "channels": channels, "node_map": {}}

        command = CutCommand(self, nodes, channels)
        self.undo_stack.push(command)

    def getNodeType(self, nodeName):
        typeDict = {
            "用户节点": "UserNode",
            "算力节点": "ComputeNode",
            "用户网关": "UserGateway",
            "算力网关": "ComputingGateway",
            "调度决策网关": "ComputeScheduleNode",
            "路由器": "Router",
        }
        return typeDict.get(nodeName, None)

    def createNewItemByType(self, nodetype, name, index, icon_path):
        if nodetype == "UserNode":
            return UserNode(name, index, icon_path)
        elif nodetype == "ComputeNode":
            return ComputeNode(name, index, icon_path)
        elif nodetype == "UserGateway":
            return UserGateway(name, index, icon_path)
        elif nodetype == "ComputingGateway":
            return ComputingGateway(name, index, icon_path)
        elif nodetype == "ComputeScheduleNode":
            return ComputeScheduleNode(name, index, icon_path)
        elif nodetype == "Router":
            return Router(name, index, icon_path)
        else:
            return "错误的节点类型"

    def isChannelNew(self, start, end):
        for channel in self.channels:
            if channel.start_item == start and channel.end_item == end:
                print("不能重复插入")
                return False
            elif channel.start_item == end and channel.end_item == start:
                print("不能重复插入")
                return False

        return True

    def mouse_press_event(self, event):
        if event.modifiers() == Qt.AltModifier:  # 仅在 Alt 键按下时处理
            scene_pos = self.ui.graphicsView.mapToScene(event.pos())
            item = self.scene.itemAt(scene_pos, self.ui.graphicsView.transform())
            if isinstance(item, NodeItem) and not self.start_item:  # 仅首次单击记录起点
                self.start_item = item

    def mouse_release_event(self, event):
        """
        按住 Alt 键选择终点并绘制连线
        """
        if (
            event.modifiers() == Qt.AltModifier and self.start_item
        ):  # 仅在 Alt 键按下且有起点时处理
            scene_pos = self.ui.graphicsView.mapToScene(event.pos())
            item = self.scene.itemAt(scene_pos, self.ui.graphicsView.transform())
            if (
                isinstance(item, NodeItem)
                and item != self.start_item
                and self.isChannelNew(self.start_item, item)
            ):
                # 使用命令模式添加链路
                command = AddChannelCommand(self, self.start_item, item)
                self.undo_stack.push(command)

                self.start_item = None  # 重置起点

    def remove_channel(self, channel):
        print("进入remove_channel函数")
        if channel in self.channels:
            self.channels.remove(channel)
            print(f"通道 {channel} 已从 channels 列表中移除")

        print(f"主场景的Channel列表为:{self.channels}")

    def remove_node(self, node):
        print("进入remove_node函数")
        command = DeleteNodeCommand(self, node)
        self.undo_stack.push(command)

    # 删除节点后更新其他节点的编号
    def update_index(self, nodetype, nodeIndex):
        print("进入update_index函数")
        for node in self.nodes[::-1]:
            if node.nodetype == nodetype and node.index > nodeIndex:
                node.index -= 1
                node.name = self.type_to_name(node.nodetype) + str(node.index + 1)
                node.text_edit.setText(node.name)

                for channel in node.channelList:
                    item = channel.another_point_of_channel(node)
                    interface_tuple = item.find_interface_tuple_by_channel(node)
                    interface_tuple[2] -= 1

    def on_submit(self):
        # 1. 打开文件夹选择器，让用户选择 OMNeT++ 的 workspace 目录
        folder_path = QFileDialog.getExistingDirectory(
            None, "选择 OMNeT++ Workspace 文件夹", ""
        )
        print([node.name for node in self.nodes])
        print([len(node.channelList) for node in self.nodes])
        if not folder_path:
            QMessageBox.warning(None, "警告", "未选择任何文件夹，提交取消。")
            return

        try:
            # 2. 构建目标路径 inet/examples/computing_power_network
            target_dir = os.path.join(
                folder_path, "inet", "examples", "computing_power_network"
            )
            os.makedirs(target_dir, exist_ok=True)  # 如果目录不存在就创建

            # 3. 处理 network.ned 文件
            ned_path = os.path.join(target_dir, "network.ned")
            with open(ned_path, "w", encoding="utf-8") as f_ned:
                omnet_file_utils.write_network_ned(
                    f_ned, self.typeNumDict, self.nodes, self.channels
                )

            # 4. 处理 omnetpp.ini 文件
            ini_path = os.path.join(target_dir, "omnetpp.ini")
            with open(ini_path, "w", encoding="utf-8") as f_ini:
                omnet_file_utils.write_omnetpp_ini(f_ini, self.nodes, self.channels)

            QMessageBox.information(
                None, "成功", "测试数据已成功写入 network.ned 和 omnetpp.ini"
            )
            # 缺少xml文件的编写和终端运行的脚本的编写和运行

        except Exception as e:
            QMessageBox.critical(None, "错误", f"提交过程中出现错误：{str(e)}")

    # 清除所有节点
    def on_clear(self):
        for node in self.nodes[::-1]:
            node.delete_node()

        print(f"self.nodes列表为:{self.nodes}")

    def on_save(self):
        # 打开文件对话框，让用户选择保存路径和文件名
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存网络数据",
            "network_data.pickle",
            "Pickle Files (*.pickle);;All Files (*)",
        )

        # 如果用户取消选择，则不进行保存
        if not file_path:
            return

        # 调用保存函数
        self.save_to_file(file_path)

    def on_load(self):
        # 打开文件对话框，获取用户选择的文件路径
        file_path, _ = QFileDialog.getOpenFileName(
            None,  # 父窗口（None 表示顶层窗口）
            "选择要加载的网络数据文件",  # 窗口标题
            "",  # 默认目录（空字符串表示当前目录）
            "Pickle 文件 (*.pickle);;所有文件 (*.*)",  # 过滤文件类型
        )

        # 用户可能取消选择，因此要检查文件路径是否为空
        if file_path:
            self.load_from_file(file_path)

    def save_to_file(self, filename="network_data.pickle"):
        # 保存当前的节点和连线数据到文件
        try:
            with open(filename, "wb") as file:
                nodes_data = [node for node in self.nodes]
                channels_data = [ChannelInfo(channel) for channel in self.channels]
                data = {"nodes": nodes_data, "channels": channels_data}
                print("!!!!!!!!")
                print(data)
                pickle.dump(data, file)
                print(f"数据已成功保存到 {filename}")
        except Exception as e:
            print(f"保存失败: {e}")

    def load_from_file(self, filename="network_data.pickle"):
        """从文件中加载节点和连线数据"""
        try:
            with open(filename, "rb") as file:
                data = pickle.load(file)
                self.on_clear()  # 清空现有的节点和连线

                node_map = {}
                # print(f"🔍 data['nodes']: {data['nodes']}")
                # print(type(obj) for obj in data["nodes"])
                for node in data["nodes"]:
                    print(f"node的id为：{id(node)}")
                    name = node.name
                    x = node.x
                    y = node.y
                    print(f"x:{type(x)}, y:{type(y)}")
                    node.setPos(x, y)
                    self.scene.addItem(node)
                    self.nodes.append(node)
                    typeAndIndex = (node.nodetype, node.index)
                    node_map[typeAndIndex] = node
                    print(f"创建的node的id为：{id(node)}")
                    # print(f"delete_self的类型:{type(node.delete_self)}")

                for channel_data in data["channels"]:
                    start_type = channel_data.start_type
                    start_index = channel_data.start_index
                    end_type = channel_data.end_type
                    end_index = channel_data.end_index
                    start_typeAndNode = (start_type, start_index)
                    end_typeAndNode = (end_type, end_index)

                    if start_typeAndNode in node_map and end_typeAndNode in node_map:
                        start_node = node_map[start_typeAndNode]
                        end_node = node_map[end_typeAndNode]
                        channel = Channel(start_node, end_node, channel_data)
                        self.scene.addItem(channel)
                        self.channels.append(channel)
                        start_node.channelList.append(channel)
                        end_node.channelList.append(channel)
                        print(
                            f"append成功, start_node的Channel列表为{start_node.channelList}"
                        )
                        print(f"start_node的id为：{id(start_node)}")

                print(f"数据已成功从 {filename} 加载")
        except Exception as e:
            raise (e)
            # print(f"加载失败: {e}")

    def type_to_name(self, nodetype):
        nameDict = {
            "UserNode": "用户节点",
            "ComputeNode": "算力节点",
            "UserGateway": "用户网关",
            "ComputingGateway": "算力网关",
            "ComputeScheduleNode": "调度决策网关",
            "Router": "路由器",
        }
        return nameDict.get(nodetype, None)


class AddNodeCommand(QUndoCommand):
    def __init__(self, window, node_name, node_type, icon_path):
        super().__init__()
        self.window = window
        self.node_name = node_name
        self.node_type = node_type
        self.icon_path = icon_path
        self.node = None

    def redo(self):
        # 执行添加节点操作
        if self.node is None:
            index = self.window.typeNumDict[self.node_type]
            self.node = self.window.createNewItemByType(
                self.node_type, self.node_name, index, self.icon_path
            )

            view_center = self.window.ui.graphicsView.mapToScene(
                self.window.ui.graphicsView.viewport().rect().center()
            )
            self.node.setPos(
                view_center.x() - self.node.boundingRect().width() / 2,
                view_center.y() - self.node.boundingRect().height() / 2,
            )

            self.node.delete_self.connect(self.window.remove_node)

        # 添加节点到场景和列表
        self.window.scene.addItem(self.node)
        self.window.nodes.append(self.node)
        self.window.typeNumDict[self.node_type] += 1

        self.setText(f"添加 {self.node_name}")

    def undo(self):
        # 撤销添加节点操作
        if self.node and self.node in self.window.nodes:
            self.window.scene.removeItem(self.node)
            self.window.nodes.remove(self.node)
            self.window.typeNumDict[self.node_type] -= 1

            for node in self.window.nodes:
                if node.nodetype == self.node_type and node.index > self.node.index:
                    node.index -= 1
                    node.name = self.window.type_to_name(node.nodetype) + str(
                        node.index + 1
                    )
                    node.text_edit.setText(node.name)


class DeleteNodeCommand(QUndoCommand):
    def __init__(self, window, node):
        super().__init__()
        self.window = window
        self.node = node
        self.channel_list = []

    def redo(self):
        # 保存要删除的节点的连接信息
        self.channel_list = self.node.channelList.copy()

        # 删除相关的链路
        for channel in self.channel_list:
            other_node = channel.another_point_of_channel(self.node)
            if other_node:
                # 移除接口信息
                interface_tuple = other_node.find_interface_tuple_by_channel(self.node)
                if interface_tuple in other_node.interface_id_to_object:
                    other_node.interface_id_to_object.remove(interface_tuple)

                if channel in other_node.channelList:
                    other_node.channelList.remove(channel)

            if channel in self.window.channels:
                self.window.channels.remove(channel)
                self.window.scene.removeItem(channel)

        # 删除节点
        if self.node in self.window.nodes:
            node_type = self.node.nodetype
            node_index = self.node.index
            self.window.nodes.remove(self.node)
            self.window.scene.removeItem(self.node)
            self.window.typeNumDict[node_type] -= 1

            # 更新索引
            self.window.update_index(node_type, node_index)

        self.setText(f"删除 {self.node.name}")

    def undo(self):
        # 恢复节点
        node_type = self.node.nodetype
        node_index = self.node.index

        self.window.scene.addItem(self.node)
        self.window.nodes.append(self.node)
        self.window.typeNumDict[node_type] += 1

        # 恢复索引
        for node in self.window.nodes:
            if node.nodetype == node_type and node.index >= node_index:
                node.index += 1
                node.name = self.window.type_to_name(node.nodetype) + str(
                    node.index + 1
                )
                node.text_edit.setText(node.name)

        self.node.index = node_index
        self.node.name = self.window.type_to_name(node_type) + str(node_index + 1)
        self.node.text_edit.setText(self.node.name)

        # 恢复链路
        for channel in self.channel_list:
            start_item = channel.start_item
            end_item = channel.end_item

            # 恢复接口信息
            start_item.interface_counter += 1
            end_item.interface_counter += 1
            start_item.interface_id_to_object.append(
                [start_item.interface_counter, type(end_item), end_item.index]
            )
            end_item.interface_id_to_object.append(
                [end_item.interface_counter, type(start_item), start_item.index]
            )

            # 添加链路到场景和列表
            self.window.scene.addItem(channel)
            self.window.channels.append(channel)
            start_item.channelList.append(channel)
            end_item.channelList.append(channel)


class AddChannelCommand(QUndoCommand):
    def __init__(self, window, start_item, end_item):
        super().__init__()
        self.window = window
        self.start_item = start_item
        self.end_item = end_item
        self.channel = None

    def redo(self):
        # 执行添加链路操作
        if self.channel is None:
            # 增加接口计数器并记录接口信息
            self.start_item.interface_counter += 1
            self.end_item.interface_counter += 1
            self.start_item.interface_id_to_object.append(
                [
                    self.start_item.interface_counter,
                    type(self.end_item),
                    self.end_item.index,
                ]
            )
            self.end_item.interface_id_to_object.append(
                [
                    self.end_item.interface_counter,
                    type(self.start_item),
                    self.start_item.index,
                ]
            )

            # 创建链路
            self.channel = Channel(self.start_item, self.end_item)
            self.channel.delete_self.connect(self.window.remove_channel)

        # 添加链路到场景和列表
        self.window.scene.addItem(self.channel)
        self.window.channels.append(self.channel)
        self.start_item.channelList.append(self.channel)
        self.end_item.channelList.append(self.channel)

        self.setText(f"添加链路: {self.start_item.name} -> {self.end_item.name}")

    def undo(self):
        # 撤销添加链路操作
        if self.channel and self.channel in self.window.channels:
            if self.channel in self.start_item.channelList:
                self.start_item.channelList.remove(self.channel)
            if self.channel in self.end_item.channelList:
                self.end_item.channelList.remove(self.channel)
            self.window.channels.remove(self.channel)

            # 从场景中移除链路
            self.window.scene.removeItem(self.channel)

            if self.start_item.interface_id_to_object:
                self.start_item.interface_id_to_object.pop()
            if self.end_item.interface_id_to_object:
                self.end_item.interface_id_to_object.pop()


class DeleteChannelCommand(QUndoCommand):
    def __init__(self, window, channel):
        super().__init__()
        self.window = window
        self.channel = channel
        self.start_item = channel.start_item
        self.end_item = channel.end_item

    def redo(self):
        # 保存接口信息
        self.start_interface = None
        self.end_interface = None

        for interface in self.start_item.interface_id_to_object:
            if (
                interface[1] == type(self.end_item)
                and interface[2] == self.end_item.index
            ):
                self.start_interface = interface
                break

        for interface in self.end_item.interface_id_to_object:
            if (
                interface[1] == type(self.start_item)
                and interface[2] == self.start_item.index
            ):
                self.end_interface = interface
                break

        # 从接口列表中移除
        if (
            self.start_interface
            and self.start_interface in self.start_item.interface_id_to_object
        ):
            self.start_item.interface_id_to_object.remove(self.start_interface)

        if (
            self.end_interface
            and self.end_interface in self.end_item.interface_id_to_object
        ):
            self.end_item.interface_id_to_object.remove(self.end_interface)

        # 从所有相关列表中移除链路
        if self.channel in self.start_item.channelList:
            self.start_item.channelList.remove(self.channel)
        if self.channel in self.end_item.channelList:
            self.end_item.channelList.remove(self.channel)
        if self.channel in self.window.channels:
            self.window.channels.remove(self.channel)

        # 从场景中移除链路
        self.window.scene.removeItem(self.channel)

        self.setText(f"删除链路: {self.start_item.name} -> {self.end_item.name}")

    def undo(self):
        # 恢复接口信息
        if self.start_interface:
            self.start_item.interface_id_to_object.append(self.start_interface)
        if self.end_interface:
            self.end_item.interface_id_to_object.append(self.end_interface)

        # 恢复链路
        self.window.scene.addItem(self.channel)
        self.window.channels.append(self.channel)
        self.start_item.channelList.append(self.channel)
        self.end_item.channelList.append(self.channel)


class PasteCommand(QUndoCommand):
    def __init__(self, window, clipboard):
        super().__init__()
        self.window = window
        self.clipboard = clipboard
        self.new_nodes = []
        self.new_channels = []
        self.setText("粘贴")

    def redo(self):
        # 克隆节点
        for node in self.clipboard["nodes"]:
            new_node = node.clone()
            self.window.scene.addItem(new_node)
            self.window.nodes.append(new_node)
            self.new_nodes.append(new_node)

        # 克隆通道
        for channel in self.clipboard["channels"]:
            start_item = next(
                (n for n in self.new_nodes if n.name == channel.start_item.name), None
            )
            end_item = next(
                (n for n in self.new_nodes if n.name == channel.end_item.name), None
            )
            if start_item and end_item:
                new_channel = Channel(start_item, end_item)
                self.window.scene.addItem(new_channel)
                self.window.channels.append(new_channel)
                self.new_channels.append(new_channel)

    def undo(self):
        # 移除新节点
        for node in self.new_nodes:
            self.window.scene.removeItem(node)
            self.window.nodes.remove(node)

        # 移除新通道
        for channel in self.new_channels:
            self.window.scene.removeItem(channel)
            self.window.channels.remove(channel)

    def _clear_copies(self):
        self.undo()

    def _channel_exists(self, start_node, end_node):
        for channel in start_node.channelList:
            if channel.another_point_of_channel(start_node) == end_node:
                return True
        return False


class CutCommand(QUndoCommand):
    def __init__(self, window, nodes, channels):
        super().__init__()
        self.window = window
        self.nodes = nodes
        self.channels = channels
        self.deleted_nodes = []
        self.deleted_channels = []
        self.setText("剪切")

    def redo(self):
        # 保存要删除的节点和链路的信息
        self.deleted_nodes = []
        self.deleted_channels = []

        # 先删除链路
        for channel in self.channels:
            start_item = channel.start_item
            end_item = channel.end_item

            # 保存接口信息
            interface_start = None
            for interface in start_item.interface_id_to_object:
                if interface[1] == type(end_item) and interface[2] == end_item.index:
                    interface_start = interface
                    break

            interface_end = None
            for interface in end_item.interface_id_to_object:
                if (
                    interface[1] == type(start_item)
                    and interface[2] == start_item.index
                ):
                    interface_end = interface
                    break

            self.deleted_channels.append(
                {
                    "channel": channel,
                    "start_item": start_item,
                    "end_item": end_item,
                    "interface_start": interface_start,
                    "interface_end": interface_end,
                }
            )

            # 从接口列表中移除
            if interface_start in start_item.interface_id_to_object:
                start_item.interface_id_to_object.remove(interface_start)
            if interface_end in end_item.interface_id_to_object:
                end_item.interface_id_to_object.remove(interface_end)

            # 从所有相关列表中移除链路
            if channel in start_item.channelList:
                start_item.channelList.remove(channel)
            if channel in end_item.channelList:
                end_item.channelList.remove(channel)
            if channel in self.window.channels:
                self.window.channels.remove(channel)

            # 从场景中移除链路
            self.window.scene.removeItem(channel)

        # 再删除节点
        for node in self.nodes:
            # 保存节点信息
            node_info = {
                "node": node,
                "node_type": node.nodetype,
                "index": node.index,
                "pos": node.pos(),
                "interface_id_to_object": [
                    list(i) for i in node.interface_id_to_object
                ],
                "interface_counter": node.interface_counter,
            }

            self.deleted_nodes.append(node_info)

            # 从场景和列表中移除节点
            if node in self.window.nodes:
                node_type = node.nodetype
                self.window.nodes.remove(node)
                self.window.scene.removeItem(node)
                self.window.typeNumDict[node_type] -= 1

                # 更新索引
                self.window.update_index(node_type, node.index)

    def undo(self):
        # 恢复节点
        for node_info in reversed(self.deleted_nodes):
            node = node_info["node"]
            node_type = node_info["node_type"]
            index = node_info["index"]

            # 恢复节点到场景和列表
            self.window.scene.addItem(node)
            self.window.nodes.append(node)
            self.window.typeNumDict[node_type] += 1

            # 恢复接口信息
            node.interface_id_to_object = node_info["interface_id_to_object"]
            node.interface_counter = node_info["interface_counter"]

            # 恢复索引
            for existing_node in self.window.nodes:
                if existing_node.nodetype == node_type and existing_node.index >= index:
                    existing_node.index += 1

            node.index = index
            node.name = self.window.type_to_name(node_type) + str(node.index + 1)
            node.text_edit.setText(node.name)

        # 恢复链路
        for channel_info in reversed(self.deleted_channels):
            channel = channel_info["channel"]
            start_item = channel_info["start_item"]
            end_item = channel_info["end_item"]
            interface_start = channel_info["interface_start"]
            interface_end = channel_info["interface_end"]

            # 恢复接口信息
            if (
                interface_start
                and interface_start not in start_item.interface_id_to_object
            ):
                start_item.interface_id_to_object.append(interface_start)
            if interface_end and interface_end not in end_item.interface_id_to_object:
                end_item.interface_id_to_object.append(interface_end)

            # 恢复链路到场景和列表
            self.window.scene.addItem(channel)
            self.window.channels.append(channel)
            start_item.channelList.append(channel)
            end_item.channelList.append(channel)


if __name__ == "__main__":
    app = QApplication([])
    window = UserWindow()
    window.ui.show()
    sys.exit(app.exec())
