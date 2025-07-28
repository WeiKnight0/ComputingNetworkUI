# coding=utf-8
import gc
import os
import pickle
import sys
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QDockWidget, QWidget, QTableWidgetItem,
                              QGraphicsScene, QVBoxLayout, QTableWidget, QLabel,
                              QMenu, QMessageBox, QFileDialog,QDialog)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt, QEvent, QTimer
from PySide6.QtGui import  QAction, QKeySequence, QShortcut, QUndoStack

from channel import Channel, ChannelInfo
from nodeItem import NodeItem
from allTypeItem import (UserNode, UserGateway, ComputingNode, ComputingGateway, 
                         Router, DecisionRouter)
from pathlib import Path

# 四种快捷键
from commands import (DeleteNodeCommand, CutCommand, DeleteChannelCommand, AddChannelCommand,
                       PasteCommand, AddNodeCommand)

uiLoader = QUiLoader()

class UserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.undo_stack = QUndoStack(self)
        self.ui = uiLoader.load('design_window.ui')
        self.ui.setWindowTitle("算力网络仿真平台——算域天枢")
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
        self.run_action = self.ui.findChild(QAction, 'actionrun')
        self.config_action = self.ui.findChild(QAction, 'actionconfig')
        self.export_action = self.ui.findChild(QAction, 'actionexport')

        # 连接菜单项的事件
        self.submit_action.triggered.connect(self.on_submit)
        self.clear_action.triggered.connect(self.on_clear)
        self.save_action.triggered.connect(self.on_save)
        self.load_action.triggered.connect(self.on_load)
        self.run_action.triggered.connect(self.on_run)
        self.config_action.triggered.connect(self.on_config)
        self.export_action.triggered.connect(self.on_export)

        # 添加快捷键
        self.setup_shortcuts()

        # 设置omnetpp路径与项目路径
        self.OMNETPP_DIR = ""
        self.PROJECT_DIR = ""
        '''
        C:/Users/WeiKnight/Documents/omnetpp-5.6.2/samples/inet/examples/computing_power_network/simpletest
        '''
        self.update_statusLabel()

        # 添加监控面板
        self.setup_monitor_panel()

        # 添加文件监控
        # self.json_file_path = 'network_status.json'
        self.last_modified = self.get_file_modification_time()
        
        # 创建定时器，每1秒检查一次文件变化
        self.file_check_timer = QTimer(self)
        self.file_check_timer.timeout.connect(self.check_file_changes)
        self.file_check_timer.start(1000)

        self.setDockNestingEnabled(True)
        self.show()

    def setup_shortcuts(self):
        # 全选（CTRL + A）
        self.select_all_shortcut = QShortcut(QKeySequence("Ctrl+A"), self.ui.graphicsView)
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

    def setup_monitor_panel(self):
        # 创建监控面板
        self.monitor_dock = QDockWidget("网络状态监控", self)
        self.monitor_dock.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        
        # 创建面板内容
        self.monitor_widget = QWidget()
        self.monitor_layout = QVBoxLayout()
        
        # 创建延迟表格
        self.delay_table = QTableWidget()
        self.delay_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 禁止编辑
        self.delay_table.setSelectionBehavior(QTableWidget.SelectRows)  # 整行选择
        self.delay_table.setAlternatingRowColors(True)  # 交替行颜色
        
        # 创建丢包率标签
        self.packet_loss_label = QLabel()
        self.packet_loss_label.setStyleSheet("font-weight: bold;")
        
        # 添加到布局
        self.monitor_layout.addWidget(self.delay_table)
        self.monitor_layout.addWidget(self.packet_loss_label)
        self.monitor_widget.setLayout(self.monitor_layout)
        
        # 设置面板内容
        self.monitor_dock.setWidget(self.monitor_widget)
        
        # 添加到主窗口
        self.monitor_dock.setMinimumSize(300, 200)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.monitor_dock)
        
        # 添加视图菜单控制
        self.view_menu = self.menuBar().addMenu("视图")
        self.show_monitor_action = QAction("网络状态监控", self, checkable=True, checked=True)
        self.show_monitor_action.triggered.connect(self.toggle_monitor)
        self.view_menu.addAction(self.show_monitor_action)
        
        # 确保面板初始可见
        self.monitor_dock.show()
        self.monitor_dock.raise_()

        # 调试输出
        print("监控面板已创建")
        print(f"主窗口 dock 数量: {len(self.findChildren(QDockWidget))}")

    def get_file_modification_time(self):
        try:
            network_status_json_path = Path(self.PROJECT_DIR) / 'network_status.json'
            if os.path.exists(network_status_json_path):
                return os.path.getmtime(network_status_json_path)
            return -1
        except Exception as e:
            print(f"获取文件修改时间失败: {e}")
            return -1

    def check_file_changes(self):
        current_modified = self.get_file_modification_time()
        if current_modified > self.last_modified and current_modified != 0:
            print("检测到JSON文件更新，刷新监控面板...")
            self.last_modified = current_modified
            self.on_run()

    def toggle_monitor(self, checked):
        if checked:
            self.monitor_dock.show()
        else:
            self.monitor_dock.hide()

    def eventFilter(self, obj, event):
        #print("eventFilter函数启动")
        # 捕获 Alt 键的按下和释放

        # 处理鼠标事件
        if obj == self.ui.graphicsView.viewport():
            if event.type() == QEvent.Type.MouseButtonPress:
                self.mouse_press_event(event)
                if event.button() == Qt.RightButton:
                    scene_pos = self.ui.graphicsView.mapToScene(event.position().toPoint())
                    items = self.scene.items(scene_pos)
                    if not items:
                        self.show_view_context_menu(event.position().toPoint())
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

        #分割线
        menu.addSeparator()

        undo_action = QAction("撤销", self)
        undo_action.triggered.connect(self.undo)
        undo_action.setEnabled(self.undo_stack.canUndo())
        menu.addAction(undo_action)

        redo_action = QAction("还原", self)
        redo_action.triggered.connect(self.redo)
        redo_action.setEnabled(self.undo_stack.canRedo())
        menu.addAction(redo_action)

        #分割线
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
            self.clipboard = {
                'nodes': nodes,
                'channels': related_channels
            }

            print(f"已复制{len(nodes)} 个节点和 {len(channels)} 个链路")

        else:
            self.clipboard = None
        
    def paste(self):
        if not hasattr(self, "clipboard") or not self.clipboard or not self.clipboard['nodes']:
            return
        
        command = PasteCommand(self, self.clipboard)
        self.undo_stack.push(command)

    def cut(self):
        selected_items = self.scene.selectedItems()
        
        # 过滤出节点和链路
        nodes = [item for item in selected_items if isinstance(item, NodeItem)]
        channels = [item for item in selected_items if isinstance(item, Channel)]
        
        if not nodes and not channels:
            return
        
        self.clipboard = {
            'nodes': nodes,
            'channels': channels,
            'node_map': {}
        }
        
        command = CutCommand(self, nodes, channels)
        self.undo_stack.push(command)

    def on_run(self):
        from omnetpp_runner import OmnetppRunner
        try:
            run_command = ""
            runner = OmnetppRunner(self.OMNETPP_DIR,self.PROJECT_DIR,run_command)
            runner.run()
        except Exception as e:
            print(f"出现错误！{e}")
            return False
        try:
            with open('network_status.json', 'r') as f:
                network_status = json.load(f)
                self.update_monitor_panel(network_status)
        except FileNotFoundError:
            print("未找到 network_status.json 文件")
        except json.JSONDecodeError:
            print("无法解析 network_status.json 文件")


    def update_monitor_panel(self, network_status):
        # 清空延迟表格
        self.delay_table.setRowCount(0)
        self.delay_table.setColumnCount(0)

        # 获取所有算力节点 ID
        compute_node_ids = []
        for entry in network_status:
            for node_id in entry['delayVector']['computeNodeIds']:
                if node_id not in compute_node_ids:
                    compute_node_ids.append(node_id)

        # 设置表格列数和表头
        self.delay_table.setColumnCount(len(compute_node_ids) + 1)
        headers = ['用户节点ID'] + [str(id) for id in compute_node_ids]
        self.delay_table.setHorizontalHeaderLabels(headers)

        # 填充延迟表格
        for entry in network_status:
            row = self.delay_table.rowCount()
            self.delay_table.insertRow(row)
            self.delay_table.setItem(row, 0, QTableWidgetItem(str(entry['triggeringUserNodeId'])))
            for i, node_id in enumerate(entry['delayVector']['computeNodeIds']):
                col = headers.index(str(node_id))
                self.delay_table.setItem(row, col, QTableWidgetItem(str(entry['delayVector']['delays'][i])))

        # 计算总丢包率
        total_packets_sent = 0
        total_packets_dropped = 0
        for entry in network_status:
            total_packets_sent += entry['packetLoss']['packetsSentSinceLastLog']
            total_packets_dropped += entry['packetLoss']['packetsDroppedSinceLastLog']

        if total_packets_sent > 0:
            total_packet_loss_rate = (total_packets_dropped / total_packets_sent) * 100
            self.packet_loss_label.setText(f"总丢包率: {total_packet_loss_rate:.2f}%")
        else:
            self.packet_loss_label.setText("总丢包率: 0.00%")

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
            raise ValueError("错误的节点类型")
    
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
                # 使用命令模式添加链路
                command = AddChannelCommand(self, self.start_item, item)
                self.undo_stack.push(command)
                
                self.start_item = None  # 重置起点

    def remove_channel(self, channel):
        # print("进入remove_channel函数")
        if channel in self.channels:
            self.channels.remove(channel)
            # print(f"通道 {channel} 已从 channels 列表中移除")
        
        # print(f"主场景的Channel列表为:{self.channels}")

    def remove_node(self, node):
        # print("进入remove_node函数")
        command = DeleteNodeCommand(self, node)
        self.undo_stack.push(command)

    # 删除节点后更新其他节点的编号
    def update_index(self, nodetype, nodeIndex):
        # print("进入update_index函数")
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
        # print([node.name for node in self.nodes])
        # print([len(node.channelList) for node in self.nodes])
        if not folder_path:
            QMessageBox.warning(None, "警告", "未选择任何文件夹，提交取消。")
            return

        try:
            import file_utils
            # 2. 构建目标路径 inet/examples/computing_power_network
            target_dir = os.path.join(folder_path, "inet", "examples", "computing_power_network")
            os.makedirs(target_dir, exist_ok=True)  # 如果目录不存在就创建

            # 3. 处理 network.ned 文件
            ned_path = os.path.join(target_dir, "network.ned")
            nedwriter = file_utils.NEDWriter(ned_path,self.nodes,self.channels)
            nedwriter.write()
            del nedwriter

            # 4. 处理 omnetpp.ini 文件
            ini_path = os.path.join(target_dir, "omnetpp.ini")
            iniwriter = file_utils.INIWriter(ini_path,self.nodes,self.channels)
            iniwriter.write()
            del iniwriter

            QMessageBox.information(None, "成功", "测试数据已成功写入 network.ned 和 omnetpp.ini")
            # 缺少xml文件的编写和终端运行的脚本的编写和运行

        except Exception as e:
            QMessageBox.critical(None, "错误", f"提交过程中出现错误：{str(e)}")
    
    # 清除所有节点
    def on_clear(self):
        for node in self.nodes[::-1]:
            node.delete_node()
        
        # print(f"self.nodes列表为:{self.nodes}")

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
                # print('!!!!!!!!')
                # print(data)
                pickle.dump(data, file)
                print(f"数据已成功保存到 {filename}")
        except Exception as e:
            print(f"保存失败: {e}")
            # raise e

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
                    # print(f"node的id为：{id(node)}")
                    name = node.name
                    x = node.x
                    y = node.y
                    print(f"x:{type(x)}, y:{type(y)}")
                    node.setPos(x, y)
                    self.scene.addItem(node)
                    self.nodes.append(node)
                    typeAndIndex = (node.nodetype, node.index)
                    node_map[typeAndIndex] = node
                    # print(f"创建的node的id为：{id(node)}")
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

    def on_config(self):
        """显示配置对话框并更新路径"""
        from PathConfig import PathConfigDialog
        dialog = PathConfigDialog(self.OMNETPP_DIR, self.PROJECT_DIR,self)
        if dialog.exec() == QDialog.Accepted:
            paths = dialog.get_paths()
            self.OMNETPP_DIR = paths["OMNETPP_DIR"]
            self.PROJECT_DIR = paths["PROJECT_DIR"]

            # 更新状态栏
            self.update_statusLabel()
            return True
        return False

    def update_statusLabel(self):
        """更新主程序状态栏显示路径"""
        if hasattr(self, 'ui') and hasattr(self.ui, 'statusLabel'):
            status_text = (f"OMNETPP软件路径: {self.OMNETPP_DIR if self.OMNETPP_DIR else '未配置'} "
                           f"\n项目路径: {self.PROJECT_DIR if self.PROJECT_DIR else '未配置'}")
            self.ui.statusLabel: QLabel
            self.ui.statusLabel.setText(status_text)

    def on_export(self):
        result_path = Path(self.PROJECT_DIR) / "results.json"
        if result_path.exists():
            from simulation_export import SimulationExportDialog
            dialog = SimulationExportDialog(str(result_path), self)
            dialog.show()
        else:
            QMessageBox.information(None, "提示", "结果文件不存在", QMessageBox.Ok)
        
if __name__ == "__main__":
    app = QApplication([])
    window = UserWindow()
    window.ui.show()
    sys.exit(app.exec())