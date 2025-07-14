# This Python file uses the following encoding: utf-8
import gc
import os
import pickle
import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsView, 
                              QGraphicsScene, QGraphicsItem, QListWidget, 
                              QMenu, QGraphicsProxyWidget, QLineEdit, QMessageBox, QFileDialog)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt, QPointF, QRectF, QLineF, QEvent
from PySide6.QtGui import QPixmap, QPen, QColor, QTransform, QAction

from channel import Channel, ChannelInfo
from nodeItem import NodeItem
from allTypeItem import (UserNode, UserGateway, ComputingNode, ComputingGateway, 
                         Router, DecisionRouter)
import omnet_file_utils

uiLoader = QUiLoader()


class UserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = uiLoader.load('design_window.ui')
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

        # 用字典记录各类节点的数量
        self.typeNumDict = {"UserNode": 0,
                    "ComputingNode": 0, 
                    "UserGateway": 0, 
                    "ComputingGateway": 0, 
                    "DecisionRouter": 0, 
                    "Router": 0}
        
        # 安装事件过滤器
        self.ui.graphicsView.viewport().installEventFilter(self)
        #self.installEventFilter(self)
        #self.setFocusPolicy(Qt.StrongFocus)  # 确保窗口可以接收键盘焦点

        # 获取菜单项
        self.submit_action = self.ui.findChild(QAction, 'actionsubmit')
        self.clear_action = self.ui.findChild(QAction, 'actionclear')
        self.save_action = self.ui.findChild(QAction, 'actionsave')
        self.load_action = self.ui.findChild(QAction, 'actionload')

        # 连接菜单项的事件
        self.submit_action.triggered.connect(self.on_submit)
        self.clear_action.triggered.connect(self.on_clear)
        self.save_action.triggered.connect(self.on_save)
        self.load_action.triggered.connect(self.on_load)

        
    def eventFilter(self, obj, event):
        #print("eventFilter函数启动")
        # 捕获 Alt 键的按下和释放

        # 处理鼠标事件
        if obj == self.ui.graphicsView.viewport():
            if event.type() == QEvent.Type.MouseButtonPress:
                self.mouse_press_event(event)
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
        
    def add_node(self, list_item):
        # 根据ListWidget的item生成节点
        icon_path = f"icon/{list_item.text().lower().replace(' ', '_')}.png"
        nodetype = self.getNodeType(list_item.text())
        node = self.createNewItemByType(nodetype, list_item.text(), self.typeNumDict[nodetype], icon_path)
        self.typeNumDict[nodetype] += 1
        self.scene.addItem(node)
        
        # 将节点放置在视图中心
        view_center = self.ui.graphicsView.mapToScene(
            self.ui.graphicsView.viewport().rect().center())
        node.setPos(view_center.x() - node.boundingRect().width()/2, 
                   view_center.y() - node.boundingRect().height()/2)
        self.nodes.append(node)
        node.delete_self.connect(self.remove_node)

    def getNodeType(self, nodeName):
        typeDict = {"用户节点": "UserNode", 
                    "算力节点": "ComputingNode", 
                    "用户网关": "UserGateway", 
                    "算力网关": "ComputingGateway", 
                    "调度决策网关": "DecisionRouter", 
                    "路由器": "Router"}
        return typeDict.get(nodeName, None)

        
    def createNewItemByType(self, nodetype, name, index, icon_path):
        if nodetype == "UserNode":
            return UserNode(name, index, icon_path)
        elif nodetype == "ComputingNode":
            return ComputingNode(name, index, icon_path)
        elif nodetype == "UserGateway":
            return UserGateway(name, index, icon_path)
        elif nodetype == "ComputingGateway":
            return ComputingGateway(name, index, icon_path)
        elif nodetype == "DecisionRouter":
            return DecisionRouter(name, index, icon_path)
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
        if event.modifiers() == Qt.AltModifier and self.start_item:  # 仅在 Alt 键按下且有起点时处理
            scene_pos = self.ui.graphicsView.mapToScene(event.pos())
            item = self.scene.itemAt(scene_pos, self.ui.graphicsView.transform())
            if isinstance(item, NodeItem) and item != self.start_item and self.isChannelNew(self.start_item, item):
                self.start_item.interface_counter += 1
                item.interface_counter += 1
                self.start_item.interface_id_to_object.append\
                    ([self.start_item.interface_counter, type(item), item.index])
                item.interface_id_to_object.append\
                    ([item.interface_counter, type(self.start_item), self.start_item.index])

                #print(f"终点: {item.name}")
                channel = Channel(self.start_item, item)
                self.scene.addItem(channel)
                self.channels.append(channel)
                self.start_item.channelList.append(channel)
                item.channelList.append(channel)

                self.start_item = None  # 重置起点

                # 连接信号
                channel.delete_self.connect(self.remove_channel)
            
            #self.start_item = None  # 重置连线起点

    def remove_channel(self, channel):
        print("进入remove_channel函数")
        if channel in self.channels:
            self.channels.remove(channel)
            print(f"通道 {channel} 已从 channels 列表中移除")
        
        print(f"主场景的Channel列表为:{self.channels}")

    def remove_node(self, node):
        print("进入remove_node函数")
        if node in self.nodes:
            nodeType = node.nodetype
            nodeIndex = node.index
            self.typeNumDict[nodeType] -= 1
            self.nodes.remove(node)
            self.update_index(nodeType, nodeIndex)
            
            print(f"节点 {node} 已从 nodes 列表中移除")
        
        print(f"主场景的node列表为:{self.nodes}")

    # 删除节点后更新其他节点的编号
    def update_index(self, nodetype, nodeIndex):
        print("进入update_index函数")
        for node in self.nodes[::-1]:
            if node.nodetype == nodetype and node.index > nodeIndex:
                node.index -= 1
                node.name = self.type_to_name(node.nodetype) + str(node.index+1)
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
            target_dir = os.path.join(folder_path, "inet", "examples", "computing_power_network")
            os.makedirs(target_dir, exist_ok=True)  # 如果目录不存在就创建

            # 3. 处理 network.ned 文件
            ned_path = os.path.join(target_dir, "network.ned")
            with open(ned_path, "w", encoding="utf-8") as f_ned:
                omnet_file_utils.write_network_ned(f_ned, self.typeNumDict, self.nodes, self.channels)

            # 4. 处理 omnetpp.ini 文件
            ini_path = os.path.join(target_dir, "omnetpp.ini")
            with open(ini_path, "w", encoding="utf-8") as f_ini:
                omnet_file_utils.write_omnetpp_ini(f_ini, self.nodes, self.channels)

            QMessageBox.information(None, "成功", "测试数据已成功写入 network.ned 和 omnetpp.ini")
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
            self, "保存网络数据", "network_data.pickle", "Pickle Files (*.pickle);;All Files (*)"
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
            "Pickle 文件 (*.pickle);;所有文件 (*.*)"  # 过滤文件类型
        )

        # 用户可能取消选择，因此要检查文件路径是否为空
        if file_path:
            self.load_from_file(file_path)
    
    def save_to_file(self, filename="network_data.pickle"):
        #保存当前的节点和连线数据到文件
        try:
            with open(filename, "wb") as file:
                nodes_data = [node for node in self.nodes]
                channels_data = [ChannelInfo(channel) for channel in self.channels]
                data = {
                    "nodes": nodes_data,
                    "channels": channels_data
                }
                print('!!!!!!!!')
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
                #print(f"🔍 data['nodes']: {data['nodes']}")
                #print(type(obj) for obj in data["nodes"])
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
                    #print(f"delete_self的类型:{type(node.delete_self)}")
                
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
                        print(f"append成功, start_node的Channel列表为{start_node.channelList}")
                        print(f"start_node的id为：{id(start_node)}")

                
                print(f"数据已成功从 {filename} 加载")
        except Exception as e:
            raise(e)
            # print(f"加载失败: {e}")
    
    def type_to_name(self, nodetype):
        nameDict = {"UserNode": "用户节点", 
                    "ComputingNode": "算力节点", 
                    "UserGateway": "用户网关", 
                    "ComputingGateway": "算力网关",
                    "DecisionRouter": "调度决策网关", 
                    "Router": "路由器"}
        return nameDict.get(nodetype, None)



if __name__ == "__main__":
    app = QApplication([])
    window = UserWindow()
    window.ui.show()
    sys.exit(app.exec())