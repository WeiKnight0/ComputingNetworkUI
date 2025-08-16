# coding=utf-8
import gc
import os
import pickle
import sys
import json
import csv
import typing
from sys import stderr

from PySide6.QtWidgets import (QApplication, QMainWindow, QDockWidget, QWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QListWidget, QListWidgetItem,
                              QGraphicsScene, QVBoxLayout, QTableWidget, QLabel, QMenuBar, QPushButton, QStackedWidget, QGridLayout, QScrollArea, QSizeGrip,
                              QMenu, QMessageBox, QFileDialog, QHBoxLayout, QDialog, QToolButton, QFrame, QToolTip, QDialogButtonBox, QRadioButton
                               , QGraphicsLineItem, QGraphicsItem)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt, QEvent, QTimer, QDateTime, QPointF, QPoint, QMimeData, QSize, QLineF, QSignalBlocker
from PySide6.QtGui import  (QAction, QKeySequence, QShortcut, QUndoStack, QPen, QColor, QIcon, QDrag,
                            QCursor, QMouseEvent)
from sympy.utilities.decorator import deprecated

from channel import Channel, ChannelInfo
from nodeItem import NodeItem
from allTypeItem import (UserNode, UserGateway, ComputingNode, ComputingGateway,
                         Router, ComputeScheduleNode)
from pathlib import Path
from integrated_scheduler_trace import EventFlowAnimation, EventTraceItem, Event

# 四种快捷键
from commands import (DeleteNodeCommand, CutCommand, DeleteChannelCommand, AddChannelCommand,
                       PasteCommand, AddNodeCommand)

from compute_node_monitors import ComputeNodeStatusReader
from collections import defaultdict
from filelock import FileLock

class StartupDialog(QDialog):
    """启动时的强制选择对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setParent(parent)
        self.setWindowTitle("选择操作")
        self.setMinimumSize(300, 150)
        self.setModal(True)  # 模态对话框，阻止用户操作其他窗口

        # 确保对话框置顶显示
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)
        
        # 添加说明文字
        label = QLabel("请选择要执行的操作：", self)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 14px; margin: 10px;")
        layout.addWidget(label)
        
        # 单选按钮
        self.new_radio = QRadioButton("新建网络环境", self)
        self.load_radio = QRadioButton("加载网络环境", self)
        self.new_radio.setChecked(True)  # 默认选择新建
        
        # 设置单选按钮样式和大小
        radio_style = "font-size: 12px; margin: 5px 20px;"
        self.new_radio.setStyleSheet(radio_style)
        self.load_radio.setStyleSheet(radio_style)
        
        layout.addWidget(self.new_radio)
        layout.addWidget(self.load_radio)
        
        # 添加按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

class UserWindow(QMainWindow):

    # 定义消息类型映射
    MESSAGE_TYPE_MAPPING = {
        1: "任务上报",
        2: "算力节点状态采集",
        3: "网络状态采集",
        4: "算力节点状态更新",
        5: "网络状态上报",
        6: "任务决策",
        7: "任务传输",
        8: "任务结果",
        9: "任务评估"
    }
    
    # 定义节点类型映射
    NODE_TYPE_MAPPING = {
        1: "用户节点",
        2: "用户网关",
        3: "算力节点",
        4: "算力网关",
        5: "路由节点",
        6: "算力调度节点"
    }
    
    def __init__(self):
        super().__init__()
        # 1. 先初始化核心数据结构
        self.nodes = []
        self.channels = []
        self.events = []
        self.animations = []
        self.current_event_index = 0
        self.playing = False
        self.play_speed = 1.0
        self.event_table_rows = 0
        self.node_mapping_debug = {}
        self.schedule_row_count = 0
        self.last_csv_file_size = 0
        self.run_clicked = False
        self.play_speed = 1.0 
        self.pending_play_speed = 1.0  
        
        # 节点计数和索引字典
        self.typeNumDict = {
            "UserNode": 0,
            "ComputingNode": 0, 
            "UserGateway": 0, 
            "ComputingGateway": 0, 
            "ComputeScheduleNode": 0,
            "Router": 0
        }
        
        self.indexDict = {
            "UserNode": 0,
            "ComputingNode": 0,
            "UserGateway": 0,
            "ComputingGateway": 0,
            "ComputeScheduleNode": 0,
            "Router": 0
        }
        
        # 路径相关变量
        self.OMNETPP_DIR:str = ""
        self.PROJECT_DIR:str = ""
        self.PROJECT_NAME:str = ""
        self.network_status_json:str = "network_status.json"
        self.dispatch_events_csv:str = "dispatch_events.csv"
        self.compute_node_status_json:str = "compute_node_status.json"
        self.network_status_json_mtime = 0.0
        self.dispatch_events_csv_mtime = 0.0
        self.compute_node_status_json_mtime = 0.0
        self.last_highlighted_row = -1 

        # 2. 初始化UI组件
        self.ui = QUiLoader().load('design_window.ui')
        self.ui.setWindowTitle("算力网络仿真平台——算域天枢")
        self.scene = QGraphicsScene()
        self.ui.graphicsView.setScene(self.scene)
        
        # 设置右键菜单
        self.ui.listWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.listWidget.customContextMenuRequested.connect(self.show_context_menu)
        
        # 其他UI相关初始化
        self.is_alt_pressed = False
        self.start_item = None
        self.clipboard = None
        self.ui.graphicsView.setAcceptDrops(True)
        self.scene_editable_state = True
        
        # 3. 安装事件过滤器
        self.ui.graphicsView.viewport().installEventFilter(self)

        # 4. 初始化菜单栏和动作
        self.setup_menu_actions()

        # 5. 添加快捷键
        self.setup_shortcuts()

        # 7. 确保菜单栏存在
        if not self.menuBar():
            self.setMenuBar(QMenuBar(self))
        
        # 8. 添加监控面板和调度事件面板
        self.setup_monitor_panel()
        self.setDockNestingEnabled(True)

        # 9. 初始化动画定时器
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animations)

        # 10. 连接主窗口按钮
        self.setup_simulation_actions_and_buttons()

        # 12. 初始化算力节点读取器
        self.compute_node_status_json_reader = ComputeNodeStatusReader(
            os.path.join(self.PROJECT_DIR, "compute_node_status.json")
        )

        # 13. 初始化文件监控计时器
        self.files_check_timer = QTimer(self)
        self.files_check_timer.timeout.connect(self.check_network_status_changes)
        self.files_check_timer.timeout.connect(self.check_csv_update)
        self.files_check_timer.timeout.connect(self.check_compute_node_status_changes)
        # self.files_check_timer.start(100)

        # 14. 初始化撤销栈
        self.undo_stack = QUndoStack(self)

        # 15. 更新节点部件
        self.update_node_widget()

        # 16. 显示主窗口
        self.ui.show()

        # 17. 设置非运行
        self.set_non_running_state()

        # 11. 先显示启动对话框
        self.show_startup_dialog()

    def set_scene_non_editable(self):
        """禁止修改场景（不可添加、删除、移动等）"""
        # 禁用视图的交互
        self.ui.graphicsView.setInteractive(False)

        # 禁用视图的焦点（防止键盘事件影响场景）
        self.ui.graphicsView.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # 禁用所有现有项目的交互标志
        for item in self.scene.items():
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, False)

        # 存储当前状态以便恢复
        self.scene_editable_state = False

    def set_scene_editable(self):
        """恢复场景的可编辑状态（允许添加、删除、移动等）"""
        # 启用视图的交互
        self.ui.graphicsView.setInteractive(True)

        # 恢复视图的焦点策略（允许键盘交互）
        self.ui.graphicsView.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # 恢复所有现有项目的交互标志
        for item in self.scene.items():
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)

        # 存储当前状态
        self.scene_editable_state = True

    def set_running_state(self):
        """
        包含按钮和scene
        """
        self.run_clicked = True
        self.set_scene_non_editable()

        self.run_action.setEnabled(False)
        self.run_button.setEnabled(False)
        self.reset_button.setEnabled(False)
        self.reset_action.setEnabled(False)

        self.accelerate_action.setEnabled(True)
        self.accelerate_button.setEnabled(True)
        self.decelerate_button.setEnabled(True)
        self.decelerate_action.setEnabled(True)
        self.pause_button.setEnabled(True)
        self.pause_action.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.stop_action.setEnabled(True)

        # 禁用所有动作
        self.clear_action.setEnabled(False)
        self.save_action.setEnabled(False)
        self.load_action.setEnabled(False)
        self.run_action.setEnabled(False)
        self.config_action.setEnabled(False)
        self.export_action.setEnabled(False)

    def set_non_running_state(self):
        """
        包含按钮和scene
        """
        self.run_clicked = False
        self.set_scene_editable()

        self.run_action.setEnabled(True)
        self.run_button.setEnabled(True)
        if hasattr(self, "has_played"):
            self.reset_button.setEnabled(True)
            self.reset_action.setEnabled(True)
        else:
            self.reset_button.setEnabled(False)
            self.reset_action.setEnabled(False)

        self.accelerate_action.setEnabled(False)
        self.accelerate_button.setEnabled(False)
        self.decelerate_button.setEnabled(False)
        self.decelerate_action.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.pause_action.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.stop_action.setEnabled(False)

        # 启用所有动作
        self.clear_action.setEnabled(True)
        self.save_action.setEnabled(True)
        self.load_action.setEnabled(True)
        self.run_action.setEnabled(True)
        self.config_action.setEnabled(True)
        self.export_action.setEnabled(True)

    def setup_menu_actions(self):
        # 获取菜单项
        self.clear_action = self.ui.findChild(QAction, 'actionclear')
        self.save_action = self.ui.findChild(QAction, 'actionsave')
        self.load_action = self.ui.findChild(QAction, 'actionload')
        self.run_action = self.ui.findChild(QAction, 'actionrun')
        self.config_action = self.ui.findChild(QAction, 'actionconfig')
        self.export_action = self.ui.findChild(QAction, 'actionexport')

        # 连接菜单项的事件
        self.clear_action.triggered.connect(self.on_clear)
        self.save_action.triggered.connect(self.on_save)
        self.load_action.triggered.connect(self.on_load)
        self.run_action.triggered.connect(self.on_run)
        self.config_action.triggered.connect(self.on_config)
        self.export_action.triggered.connect(self.on_export)

    def show_startup_dialog(self):
        """显示启动对话框，强制用户选择新建或加载网络环境"""
        while True:
            dialog = StartupDialog(self)
            
            # 显示对话框并获取结果
            result = dialog.exec()

            # 如果用户点击关闭按钮（叉号）或取消按钮，直接退出程序
            if result != QDialog.Accepted:
                # PySide6中正确的退出方式
                QApplication.quit()
                sys.exit(0)
                return
                
            # 根据用户选择执行相应操作
            if dialog.new_radio.isChecked():
                # 新建网络环境 - 确保环境是干净的
                self.on_clear()
                break
            else:
                self.activateWindow()
                # 加载网络环境 - 调用已有的加载功能
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "选择要加载的网络数据文件", "", "网络拓扑文件 (*.pickle);"
                )

                if not file_path:
                    # 主窗口未显示时，使用无父窗口的弹窗
                    msg = QMessageBox()
                    msg.setWindowFlags(Qt.WindowStaysOnTopHint)
                    msg.information(None, "提示", "请选择一个文件或选择新建网络环境")
                elif file_path:
                    try:
                        self.load_from_file(file_path)
                        break
                    except Exception as e:
                        # 错误弹窗同样处理
                        msg = QMessageBox()
                        msg.setWindowFlags(Qt.WindowStaysOnTopHint)
                        msg.critical(None, "加载失败", f"加载文件时出错: {str(e)}")
                        self.on_clear()

    def check_compute_node_status_changes(self):
        """检查算力节点状态文件是否有更新"""
        # 如果文件不存在或未运行，不检查
        if not os.path.exists(self.compute_node_status_json) or not self.run_clicked:
            return
            
        try:
            current_mtime = os.path.getmtime(self.compute_node_status_json)
            # 如果文件有更新且当前显示的是算力节点页面
            if (current_mtime > self.compute_node_status_json_mtime and
                hasattr(self, 'stackedWidget') and 
                self.stackedWidget.currentIndex() == 2):  # 2是算力节点页面索引
                print("检测到算力节点状态文件更新，刷新表格...")
                self.load_compute_node_status()
        except Exception as e:
            print(f"算力节点文件监控错误: {e}")

    def update_node_widget(self):
        old_list = self.ui.listWidget
        if old_list:
            # 保存原有列表项数据
            items = []
            for i in range(old_list.count()):
                item = old_list.item(i)
                items.append({
                    "text": item.text(),
                    "icon": item.icon(),
                    "data": item.data(Qt.UserRole)
                })
            
            # 关键：保存原控件的所有尺寸相关属性
            old_geometry = old_list.geometry()  # 位置和大小
            old_min_size = old_list.minimumSize()
            old_max_size = old_list.maximumSize()
            old_size_policy = old_list.sizePolicy()
            old_base_size = old_list.baseSize()
            
            # 获取父布局
            parent_layout = old_list.parent().layout()
            if parent_layout:
                # 处理网格布局
                if isinstance(parent_layout, QGridLayout):
                    found = False
                    for row in range(parent_layout.rowCount()):
                        for col in range(parent_layout.columnCount()):
                            item = parent_layout.itemAtPosition(row, col)
                            if item and item.widget() == old_list:
                                # 移除旧控件
                                parent_layout.removeWidget(old_list)
                                old_list.deleteLater()
                                
                                # 创建新控件
                                self.ui.listWidget = CustomListWidget()
                                
                                # 应用所有尺寸属性
                                self.ui.listWidget.setGeometry(old_geometry)
                                self.ui.listWidget.setMinimumSize(old_min_size)
                                self.ui.listWidget.setMaximumSize(old_max_size)
                                self.ui.listWidget.setSizePolicy(old_size_policy)
                                self.ui.listWidget.setBaseSize(old_base_size)
                                
                                # 恢复其他属性
                                self.ui.listWidget.setContextMenuPolicy(Qt.CustomContextMenu)
                                self.ui.listWidget.customContextMenuRequested.connect(self.show_context_menu)
                                self.ui.listWidget.setIconSize(old_list.iconSize())
                                
                                # 恢复列表项
                                for item_data in items:
                                    new_item = QListWidgetItem(item_data["text"])
                                    new_item.setIcon(item_data["icon"])
                                    new_item.setData(Qt.UserRole, item_data["data"])
                                    
                                # 添加到原位置并保持布局比例
                                parent_layout.addWidget(self.ui.listWidget, row, col)
                                parent_layout.setRowStretch(row, parent_layout.rowStretch(row))
                                parent_layout.setColumnStretch(col, parent_layout.columnStretch(col))
                                
                                found = True
                                break
                        if found:
                            break
                else:
                    # 处理其他布局
                    list_index = parent_layout.indexOf(old_list)
                    parent_layout.removeWidget(old_list)
                    old_list.deleteLater()
                    
                    self.ui.listWidget = CustomListWidget()
                    
                    # 应用所有尺寸属性
                    self.ui.listWidget.setGeometry(old_geometry)
                    self.ui.listWidget.setMinimumSize(old_min_size)
                    self.ui.listWidget.setMaximumSize(old_max_size)
                    self.ui.listWidget.setSizePolicy(old_size_policy)
                    self.ui.listWidget.setBaseSize(old_base_size)
                    
                    # 恢复其他属性
                    self.ui.listWidget.setContextMenuPolicy(Qt.CustomContextMenu)
                    self.ui.listWidget.customContextMenuRequested.connect(self.show_context_menu)
                    self.ui.listWidget.setIconSize(old_list.iconSize())
                    
                    # 恢复列表项
                    for item_data in items:
                        new_item = QListWidgetItem(item_data["text"])
                        new_item.setIcon(item_data["icon"])
                        new_item.setData(Qt.UserRole, item_data["data"])
                        
                    parent_layout.insertWidget(list_index, self.ui.listWidget)
                    
            # 强制布局更新
            if parent_layout:
                parent_layout.update()
            self.ui.listWidget.updateGeometry()

        node_type_mapping = {
            "用户节点": "UserNode",
            "算力节点": "ComputingNode",
            "用户网关": "UserGateway",
            "算力网关": "ComputingGateway",
            "算力调度节点": "ComputeScheduleNode",
            "路由节点": "Router"
        }

        for display_name, node_type in node_type_mapping.items():
            item = QListWidgetItem(display_name)
            icon_path = f"icon/{display_name}.png"
            if os.path.exists(icon_path):
                item.setIcon(QIcon(icon_path))
            item.setData(Qt.UserRole, node_type)
            self.ui.listWidget.addItem(item)

    def create_dragged_node(self, node_type, pos):
        """根据拖拽的节点类型创建节点，严格遵循命令类中的计数器和命名规则"""
        if not self.scene_editable_state:
            return
        # 验证节点类型是否存在于计数器中
        if node_type not in self.typeNumDict or node_type not in self.indexDict:
            QMessageBox.warning(self, "错误", f"未知节点类型: {node_type}")
            return

        # 节点类映射
        node_classes = {
            "UserNode": UserNode,
            "ComputingNode": ComputingNode,
            "UserGateway": UserGateway,
            "ComputingGateway": ComputingGateway,
            "ComputeScheduleNode": ComputeScheduleNode,
            "Router": Router
        }
        node_class = node_classes.get(node_type)
        if not node_class:
            return

        # 生成节点名称
        display_name = self.type_to_name(node_type)
        node_name = f"{display_name}"  # 例如：用户节点1、算力节点2

        # 图标路径
        icon_path = f"icon/{display_name}.png"

        # 创建并推送撤销命令
        add_command = AddNodeCommand(
            self,
            node_name=node_name,
            node_type=node_type,
            icon_path=icon_path
        )
        self.undo_stack.push(add_command)
        # 关联已创建的节点，避免命令中重复创建
        assert add_command.node
        # 设置节点位置
        add_command.node.setPos(pos)
        add_command.node.setSelected(True)

    def reset_simulation(self):
        """
        重新设置监控面板与动画
        """
        # 1. 重置网络状态表格
        if hasattr(self, 'delay_matrix_table'):
            self.delay_matrix_table.clearContents()
            self.delay_matrix_table.setRowCount(0)
            self.delay_matrix_table.setColumnCount(0)
        else:
            raise RuntimeError("时延矩阵不存在！")

        # 2. 重置调度事件表格
        if hasattr(self, 'dispatch_event_table'):
            self.dispatch_event_table.clearContents()
            self.dispatch_event_table.setRowCount(0)
            self.schedule_row_count = 0
            self.last_csv_file_size = 0
        else:
            raise RuntimeError("调度信息表不存在！")

        # 3. 重置算力节点状态表格
        if hasattr(self, 'compute_node_table'):
            self.compute_node_table.clearContents()
            self.compute_node_table.setRowCount(0)
        else:
            raise RuntimeError("算力节点信息表不存在！")

        # 4. 清除滚动区域内容
        if hasattr(self, 'scroll_layout'):
            while self.scroll_layout.count():
                item = self.scroll_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        # 5. 重置相关状态变量
        self.network_status_json_mtime = 0.0
        self.dispatch_events_csv_mtime = 0.0
        self.compute_node_status_json_mtime = 0.0
        self.events.clear()
        self.all_node_data = []
        self.latest_node_data = []

        self._reset_event_loading_state()

        # 6. 重置事件相关状态
        self.current_event_index = 0
        self.playing = False
        self.play_speed = 1.0
        self.last_highlighted_row = -1

        # 7. 清除所有动画
        for anim in self.animations[:]:
            anim.remove_animation()
        self.animations.clear()

    def load_csv_events(self):
        """
        优化后的高速事件加载函数，解决表格空缺问题
        采用批量更新和文件锁定机制
        """
        try:
            if not os.path.exists(self.dispatch_events_csv):
                return False

            # 使用文件锁避免读写冲突
            with FileLock(self.dispatch_events_csv + '.lock'):
                current_size = os.path.getsize(self.dispatch_events_csv)

                # 文件被清空或覆盖的情况处理
                if current_size == 0:
                    if hasattr(self, 'last_csv_file_size') and self.last_csv_file_size > 0:
                        self._reset_event_loading_state()
                    return False

                # 检查文件是否真正有更新
                if (hasattr(self, 'last_csv_file_size') and
                        current_size == self.last_csv_file_size):
                    return True

                # 读取文件内容
                with open(self.dispatch_events_csv, 'r') as file:
                    # 获取当前位置，用于后续判断是否是新文件
                    initial_pos = file.tell()

                    # 如果是首次加载或文件被覆盖，读取并丢弃表头行
                    if not hasattr(self, 'last_csv_file_size') or current_size < self.last_csv_file_size:
                        header = file.readline()  # 读取并丢弃表头行
                        if hasattr(self, 'all_events_data'):
                            self.all_events_data.clear()
                        self.dispatch_event_table.setRowCount(0)
                        self.schedule_row_count = 0
                    else:
                        # 定位到上次读取的位置
                        file.seek(self.last_csv_file_size)

                    # 检查是否还有数据可读
                    if file.tell() == current_size:
                        return True

                    # 读取剩余内容
                    reader = csv.reader(file)
                    new_lines = [row for row in reader if
                                 row and len(row) >= 7 and not any(field == 'simTime' for field in row)]

                if not new_lines:
                    return True

                # 准备批量更新的数据
                new_events = []
                new_animation_events = []
                current_row = self.dispatch_event_table.rowCount()

                # 使用QSignalBlocker避免频繁UI更新
                blocker = QSignalBlocker(self.dispatch_event_table)

                try:
                    self.dispatch_event_table.setRowCount(current_row + len(new_lines))

                    for i, row in enumerate(new_lines):
                        # 确保不是表头行
                        if row[0] == 'simTime':
                            continue

                        # 添加到表格数据
                        new_events.append(row)

                        # 批量更新表格（先存储数据，稍后统一更新）
                        row_pos = current_row + i
                        self._queue_table_update(row_pos, row)

                        # 创建动画事件对象
                        try:
                            animation_event = EventTraceItem(
                                sim_time=float(row[0]),
                                packet_type=int(row[1]),
                                packet_id=int(row[2]),
                                source_node_type=int(row[3]),
                                source_node_id=int(row[4]),
                                dest_node_type=int(row[5]),
                                dest_node_id=int(row[6])
                            )
                            new_animation_events.append(animation_event)
                        except (ValueError, IndexError) as e:
                            print(f"创建动画事件失败: {e}，行内容: {row}")

                    # 批量提交表格更新
                    self._apply_queued_updates()

                    # 更新数据状态
                    self.events.extend(new_animation_events)
                    if not hasattr(self, 'all_events_data'):
                        self.all_events_data = []
                    self.all_events_data.extend(new_events)
                    self.schedule_row_count += len(new_events)
                    self.last_csv_file_size = current_size
                    print(f"已经加载{len(new_events)}条事件数据")
                    # 只在最后触发一次滚动
                    if new_events:
                        self.dispatch_event_table.scrollToBottom()

                finally:
                    blocker.unblock()

            return True

        except Exception as e:
            print(f"加载事件失败: {e}")
            self.ui.statusBar().showMessage(f"加载事件失败: {str(e)}", 3000)
            return False

    def _queue_table_update(self, row_pos, row_data):
        """队列化表格更新操作"""
        if not hasattr(self, '_table_update_queue'):
            self._table_update_queue = []
        self._table_update_queue.append((row_pos, row_data))

    def _apply_queued_updates(self):
        """应用所有队列化的表格更新"""
        if not hasattr(self, '_table_update_queue'):
            return

        for row_pos, row_data in self._table_update_queue:
            self._add_event_to_table_row(row_pos, row_data)

        del self._table_update_queue

    def _reset_event_loading_state(self):
        """重置事件加载状态"""
        self.events = []
        self.all_events_data = []
        self.schedule_row_count = 0
        self.dispatch_event_table.setRowCount(0)
        self.current_event_index = 0
        self.last_highlighted_row = -1
        if hasattr(self, 'event_processed_flags'):
            del self.event_processed_flags

    def _add_event_to_table_row(self, row_pos, event_data):
        """辅助方法：将事件数据添加到表格的指定行"""
        # 时间戳
        self.dispatch_event_table.setItem(row_pos, 0, QTableWidgetItem(event_data[0]))

        # 消息类型（转换为文本）
        try:
            packet_type = int(event_data[1])
            packet_type_text = self.MESSAGE_TYPE_MAPPING.get(packet_type, f"未知({packet_type})")
            self.dispatch_event_table.setItem(row_pos, 1, QTableWidgetItem(packet_type_text))
        except ValueError:
            self.dispatch_event_table.setItem(row_pos, 1, QTableWidgetItem("格式错误"))

        # 消息ID
        self.dispatch_event_table.setItem(row_pos, 2, QTableWidgetItem(event_data[2]))

        # 源节点类型（转换为文本）
        try:
            source_type = int(event_data[3])
            source_type_text = self.NODE_TYPE_MAPPING.get(source_type, f"未知({source_type})")
            self.dispatch_event_table.setItem(row_pos, 3, QTableWidgetItem(source_type_text))
        except ValueError:
            self.dispatch_event_table.setItem(row_pos, 3, QTableWidgetItem("格式错误"))

        # 源节点ID
        self.dispatch_event_table.setItem(row_pos, 4, QTableWidgetItem(event_data[4]))

        # 目标节点类型
        try:
            dest_type = int(event_data[5])
            dest_type_text = self.NODE_TYPE_MAPPING.get(dest_type, f"未知({dest_type})")
            self.dispatch_event_table.setItem(row_pos, 5, QTableWidgetItem(dest_type_text))
        except ValueError:
            self.dispatch_event_table.setItem(row_pos, 5, QTableWidgetItem("格式错误"))

        # 目标节点ID
        self.dispatch_event_table.setItem(row_pos, 6, QTableWidgetItem(event_data[6]))

    def update_animations(self):
        """更新动画状态"""
        if not self.events:
            return
        print(f"更新动画 - 当前索引: {self.current_event_index}, 播放状态: {self.playing}")
        if not self.playing:
            print("没有播放，动画不更新")
            return

        # 初始化仿真时间基准和必要属性
        if not hasattr(self, 'simulation_start_time'):
            self.simulation_start_time = QDateTime.currentDateTime().toMSecsSinceEpoch() / 1000.0
            # 确保时间偏移量属性存在
            if not hasattr(self, 'time_offset'):
                self.time_offset = 0.0
            self.last_highlighted_row = -1  # 高亮行记录
            self.last_processed_time = 0.0  # 最后处理的事件时间
            # 确保事件处理标记集合存在
            if not hasattr(self, 'event_processed_flags'):
                self.event_processed_flags = set()  # 记录已处理的事件ID
            
        # 计算当前仿真时间
        current_real_time = QDateTime.currentDateTime().toMSecsSinceEpoch() / 1000.0
        current_sim_time = (current_real_time - self.simulation_start_time) * self.play_speed + self.time_offset
        
        # 处理所有已到达播放时间的事件
        while self.current_event_index < len(self.events):
            event = self.events[self.current_event_index]
            # 使用索引+packet_id+sim_time组合作为唯一ID
            event_id = f"{self.current_event_index}_{event.packet_id}_{event.sim_time}"
     
            if not hasattr(self, 'event_processed_flags'):
                self.event_processed_flags = set()
                
            if (event.sim_time <= current_sim_time and 
                event_id not in self.event_processed_flags and
                self.current_event_index >= 0):
                
                if not self.animations:  # 当前无动画播放
                    if self.play_speed != self.pending_play_speed:
                        # 调整时间基准以平滑过渡速度变化
                        current_real_time = QDateTime.currentDateTime().toMSecsSinceEpoch() / 1000.0
                        # 计算当前时间偏移量
                        self.time_offset = current_sim_time
                        # 更新仿真开始时间
                        self.simulation_start_time = current_real_time
                        # 应用新速度
                        self.play_speed = self.pending_play_speed
                    self.process_event(event)
                    
                    # 更新高亮
                    self.clear_highlight(self.last_highlighted_row)
                    self.set_highlight(self.current_event_index)
                    self.last_highlighted_row = self.current_event_index
                    
                    # 更新表格显示
                    self.dispatch_event_table.setRowCount(self.current_event_index + 1)
                    self.dispatch_event_table.scrollToItem(
                        self.dispatch_event_table.item(self.current_event_index, 0),
                        QAbstractItemView.PositionAtCenter
                    )
                    
                    # 记录已处理事件
                    self.event_processed_flags.add(event_id)
                    self.last_processed_time = event.sim_time
                    
                    # 索引递增
                    self.current_event_index += 1
                    print(f"处理事件 {self.current_event_index - 1}，下一索引: {self.current_event_index}")
                break
            elif event_id in self.event_processed_flags:
                # 跳过已播放的事件
                print(f"跳过已处理事件 {self.current_event_index}")
                self.current_event_index += 1
            else:
                # 尚未到达下一个事件时间
                break
        
        # 更新现有动画
        for animation in self.animations[:]:
            if animation.update(current_sim_time):
                self.animations.remove(animation)
                animation.remove_animation()
        
        # 更新状态栏
        total_events = len(self.events)
        self.ui.statusBar().showMessage(
            f"播放中: {self.current_event_index}/{total_events} 事件 | "
            f"当前速度: {self.pending_play_speed:.2f}x | "
        )
        
        self.scene.update()

    def restore_playback_state(self, saved_state):
        """恢复播放状态，确保索引正确"""
        # 恢复事件索引（带边界检查）
        if 0 <= saved_state['current_index'] <= len(self.events):
            self.current_event_index = saved_state['current_index']
        else:
            self.current_event_index = min(max(0, saved_state['current_index']), len(self.events))
            print(f"修正索引: {saved_state['current_index']} -> {self.current_event_index}")
        
        # 恢复高亮行
        self.last_highlighted_row = saved_state['highlight_row']
        if self.last_highlighted_row != -1 and self.last_highlighted_row < len(self.events):
            # 修复：使用正确的高亮方法名
            self.set_highlight(self.last_highlighted_row)
        
        # 恢复播放状态
        self.playing = saved_state['is_playing']
        
        # 恢复时间基准和已处理事件标记
        self.last_processed_time = saved_state['last_time']
        self.time_offset = saved_state['time_offset']
        self.event_processed_flags = saved_state['processed_flags'].copy()
        self.simulation_start_time = QDateTime.currentDateTime().toMSecsSinceEpoch() / 1000.0
        
        print(f"已恢复播放状态: 从事件 {self.current_event_index} 继续")

    def clear_highlight(self, row):
        """清除指定行的高亮"""
        if row != -1 and row < self.dispatch_event_table.rowCount():
            for col in range(self.dispatch_event_table.columnCount()):
                item = self.dispatch_event_table.item(row, col)
                if item:
                    item.setBackground(QColor(255, 255, 255))  # 恢复白色背景

    def set_highlight(self, row):
        """设置指定行的高亮"""
        if row != -1 and row < self.dispatch_event_table.rowCount():  # 增加边界检查
            for col in range(self.dispatch_event_table.columnCount()):
                item = self.dispatch_event_table.item(row, col)
                if item:
                    item.setBackground(QColor(255, 255, 153))  # 浅黄色高亮

    def add_event_to_table(self, event):
        """辅助方法：将事件添加到表格，确保UI立即更新"""
        row_pos = self.dispatch_event_table.rowCount()
        self.dispatch_event_table.insertRow(row_pos)
        
        # 时间戳
        self.dispatch_event_table.setItem(row_pos, 0, QTableWidgetItem(event[0]))
        
        # 消息类型（转换为文本）
        packet_type = int(event[1])
        packet_type_text = self.MESSAGE_TYPE_MAPPING.get(packet_type, f"未知类型({packet_type})")
        self.dispatch_event_table.setItem(row_pos, 1, QTableWidgetItem(packet_type_text))
        
        # 消息ID
        self.dispatch_event_table.setItem(row_pos, 2, QTableWidgetItem(event[2]))
        
        # 源节点类型（转换为文本）
        source_node_type = int(event[3])
        source_node_type_text = self.NODE_TYPE_MAPPING.get(source_node_type, f"未知类型({source_node_type})")
        self.dispatch_event_table.setItem(row_pos, 3, QTableWidgetItem(source_node_type_text))
        
        # 源节点ID
        self.dispatch_event_table.setItem(row_pos, 4, QTableWidgetItem(event[4]))
        
        # 目标节点类型
        dest_node_type = int(event[5])
        dest_node_type_text = self.NODE_TYPE_MAPPING.get(dest_node_type, f"未知类型({dest_node_type})")
        self.dispatch_event_table.setItem(row_pos, 5, QTableWidgetItem(dest_node_type_text))
        
        # 目标节点ID
        self.dispatch_event_table.setItem(row_pos, 6, QTableWidgetItem(event[6]))
        
        # 强制刷新表格UI，确保立即显示
        self.dispatch_event_table.viewport().update()

    def setup_simulation_actions_and_buttons(self):
        """连接仿真的按钮与菜单到相应功能"""
        
        # 获取按钮
        self.run_button = self.ui.findChild(QPushButton, 'runButton')
        self.accelerate_button = self.ui.findChild(QPushButton, 'accelerateButton')
        self.decelerate_button = self.ui.findChild(QPushButton, 'decelerateButton')
        self.pause_button = self.ui.findChild(QPushButton, 'pauseButton')
        self.reset_button = self.ui.findChild(QPushButton, 'resetButton')
        self.showMonitor_button = self.ui.findChild(QPushButton, 'showMonitorButton')
        self.stop_button = self.ui.findChild(QPushButton,'stopButton')
        # 获取菜单
        self.accelerate_action = self.ui.findChild(QAction, "accelerateAction")
        self.decelerate_action = self.ui.findChild(QAction, "decelerateAction")
        self.pause_action = self.ui.findChild(QAction, "pauseAction")
        self.reset_action = self.ui.findChild(QAction, "resetAction")
        self.showMonitor_action = self.ui.findChild(QAction, "showMonitorAction")
        self.stop_action = self.ui.findChild(QAction, 'stopAction')
        
        # 连接按钮事件
        self.run_button.clicked.connect(self.on_run)
        self.accelerate_button.clicked.connect(self.speed_up)
        self.decelerate_button.clicked.connect(self.slow_down)
        self.pause_button.clicked.connect(self.pause_simulation)
        self.reset_button.clicked.connect(self.reset_simulation)
        self.showMonitor_button.clicked.connect(self.show_monitor_panel)
        self.stop_button.clicked.connect(self.on_stop)

        self.accelerate_action.triggered.connect(self.speed_up)
        self.decelerate_action.triggered.connect(self.slow_down)
        self.pause_action.triggered.connect(self.pause_simulation)
        self.reset_action.triggered.connect(self.reset_simulation)
        self.showMonitor_action.triggered.connect(self.show_monitor_panel)
        self.stop_action.triggered.connect(self.on_stop)

        # 设置按钮图片
        self.run_button.setIcon(QIcon("./icon/运行.png"))
        self.accelerate_button.setIcon(QIcon("./icon/加速.png"))
        self.decelerate_button.setIcon(QIcon("./icon/减速.png"))
        self.pause_button.setIcon(QIcon("./icon/暂停.png"))
        self.stop_button.setIcon(QIcon("./icon/停止.png"))
        self.reset_button.setIcon(QIcon("./icon/重置.png"))
        self.showMonitor_button.setIcon(QIcon("./icon/面板.png"))
     
    def find_node_by_type_and_id(self, node_type: int, node_id: int):
        """根据节点类型和ID查找节点，适配新的命名规则"""
        # 节点类型映射（数字类型 -> 类名）
        type_to_class = {
            1: "UserNode",
            2: "UserGateway",
            3: "ComputingNode",
            4: "ComputingGateway",
            5: "Router",
            6: "ComputeScheduleNode"
        }
        
        # 节点类型映射（数字类型 -> 显示名称）
        type_to_display = {
            1: "用户节点",
            2: "用户网关",
            3: "算力节点",
            4: "算力网关",
            5: "路由节点",
            6: "算力调度节点"
        }
        
        class_name = type_to_class.get(node_type, None)
        display_name = type_to_display.get(node_type, None)
        
        if not class_name or not display_name:
            print(f"错误: 未知节点类型 {node_type}")
            return None
        
        # 构建预期的节点名称（新格式：显示名称+ID，如"用户节点1"）
        expected_name = f"{display_name}{node_id}"
        
        # 收集节点映射信息用于调试
        self.node_mapping_debug[class_name] = []
        for node in self.nodes:
            self.node_mapping_debug[class_name].append((node.name, node.index))
            
            # 检查条件：类名匹配且名称完全匹配
            if node.nodetype == class_name and node.name == expected_name:
                return node
                
        # 容错查找：尝试部分匹配
        for node in self.nodes:
            if node.nodetype == class_name and str(node_id) in node.name:
                print(f"警告: 使用部分匹配找到节点 {node.name} (预期: {expected_name})")
                return node
                
        # 打印调试信息
        print(f"未找到节点: 类型={display_name}, ID={node_id}, 预期名称={expected_name}")
        print(f"当前可用节点: {self.node_mapping_debug}")
        return None
   
    def speed_up(self):
        """加快播放速度"""
        if self.pending_play_speed >= 1:
            self.pending_play_speed = min(10.0, self.pending_play_speed + 1)
        else:
            self.pending_play_speed = max(0.1, self.pending_play_speed + 0.1)
        self.ui.statusBar().showMessage(
            f"加速已设置，将在下一个动画生效 | 当前速度: {self.play_speed:.1f}x，待应用: {self.pending_play_speed:.1f}x"
        )
        
    def slow_down(self):
        """减慢播放速度"""
        if self.pending_play_speed > 1:
            self.pending_play_speed = max(0.1, self.pending_play_speed - 1)
        else:
            self.pending_play_speed = max(0.1, self.pending_play_speed - 0.1)
        self.ui.statusBar().showMessage(
            f"减速已设置，将在下一个动画生效 | 当前速度: {self.play_speed:.1f}x，待应用: {self.pending_play_speed:.1f}x"
        )
        
    def pause_simulation(self):
        """暂停仿真"""
        if self.playing:
            self.playing = False
            # 保存当前时间偏移量
            if hasattr(self, 'simulation_start_time'):
                current_real_time = QDateTime.currentDateTime().toMSecsSinceEpoch() / 1000.0
                self.time_offset = (current_real_time - self.simulation_start_time) * self.play_speed + self.time_offset
                delattr(self, 'simulation_start_time')
            self.animation_timer.stop()
            self.ui.statusBar().showMessage("已暂停调度轨迹")
                      
    def process_event(self, event):
        """处理事件并添加到表格和动画中，只高亮最新一行"""
        source_node = self.find_node_by_type_and_id(event.source_node_type, event.source_node_id)
        dest_node = self.find_node_by_type_and_id(event.dest_node_type, event.dest_node_id)
        
        if not dest_node:
            print(f"无法为事件创建动画: 找不到目标节点{event.dest_node_type},{event.dest_node_id}")
            return

        if not source_node:
            print(f"无法为事件创建动画: 找不到源节点{event.source_node_type},{event.source_node_id}")
            return
            
        # 创建事件动画
        animation = EventFlowAnimation(
            scene=self.scene,
            source_node=source_node,
            dest_node=dest_node,
            packet_type=event.packet_type,
            packet_id=event.packet_id,
            sim_time=event.sim_time,
            source_node_id=event.source_node_id  
        )
        self.animations.append(animation)
        
        # 添加当前事件到表格
        if 0 <= self.current_event_index < len(self.all_events_data):
            row = self.all_events_data[self.current_event_index]
            self.add_event_to_table(row)
            
            current_row = self.current_event_index
            
            # 清除上一行的高亮
            self.clear_highlight(self.last_highlighted_row)
            
            # 高亮当前行
            self.set_highlight(current_row)
            
            # 更新上一个高亮行的记录
            self.last_highlighted_row = current_row
            
            # 滚动到当前行
            self.dispatch_event_table.scrollToItem(
                self.dispatch_event_table.item(current_row, 0),
                QAbstractItemView.PositionAtCenter
            )

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

    def on_run(self):
        """
        仿真程序入口
        准备工作
        """
        # 检查路径
        if not (self.OMNETPP_DIR and self.PROJECT_DIR):
            QMessageBox.critical(self,"错误","请先配置路径地址")
            return

        # 检查拓扑
        if not self.nodes:
            QMessageBox.critical(self, "错误", "请先创建网络拓扑！")
            return

        # 检查目录是否存在
        if not os.path.exists(self.PROJECT_DIR):
            QMessageBox.critical(self, "错误", "项目路径不存在！请检查路径设置！")
            return
        # 检查mintty是否打开
        import psutil
        for proc in psutil.process_iter(['name', 'exe', 'cmdline']):
            try:
                # 检查进程名是否为 mintty.exe
                if proc.info['name'] == 'mintty.exe':
                    exe_path = proc.info['exe'] or ""
                    target_dir = os.path.normcase(self.OMNETPP_DIR)  # 统一路径格式（Windows 下转小写+反斜杠）
                    exe_dir = os.path.normcase(os.path.dirname(exe_path))
                    if target_dir in exe_dir:  # 严格匹配目录
                        QMessageBox.critical(self, "错误", "MSYS2窗口已打开，请关闭后重试！")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        # 检查网络是否正确
        pass
        # 清空当前文件夹
        def clear_folder(folder_path):
            """
            清空指定文件夹内的所有内容，但保留文件夹本身

            参数:
                folder_path: 要清空的文件夹路径
            """
            import shutil
            # 检查文件夹是否存在
            if not os.path.exists(folder_path):
                raise FileNotFoundError(f"文件夹不存在: {folder_path}")

            # 检查是否是一个文件夹
            if not os.path.isdir(folder_path):
                raise NotADirectoryError(f"不是一个文件夹: {folder_path}")

            # 遍历文件夹内的所有内容
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)

                try:
                    # 如果是文件或符号链接，直接删除
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                    # 如果是文件夹，递归删除
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except Exception as e:
                    raise RuntimeError(f"清空 {item_path} 时出错: {e}")
        try:
            clear_folder(self.PROJECT_DIR)
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
            return

        # 生成配置文件
        self.generate_config_files()
        # 启动仿真程序
        from omnetpp_runner import OmnetppRunner
        try:
            run_command = [f"cd ./samples/inet/examples/computing_power_network/{self.PROJECT_NAME}",
                           r"opp_run -u Cmdenv -c static -n ../../../src:../..:../../../tutorials:../../../showcases -l ../../../src/INET omnetpp.ini"
                           ]
            self.runner = OmnetppRunner(self.OMNETPP_DIR,self.PROJECT_DIR,run_command)
            self.runner.simulation_finished.connect(self.end_running)
            self.runner.encountering_errors.connect(lambda: QMessageBox.critical(self, "错误", "仿真未能完成！"))
            self.runner.run()
        except Exception as e:
            QMessageBox.critical(self,"错误",f"启动仿真出现错误！{e}")
            del self.runner
            return

        self.start_running()

    def reset_clocks(self):
        if hasattr(self, 'files_check_timer'):
            self.files_check_timer.stop()
            self.files_check_timer.start(100)

    def start_running(self):
        """
        真仿真程序：支持从暂停状态继续运行
        """
        # 确保动画计时器已停止，避免多重启动
        if self.animation_timer.isActive():
            self.animation_timer.stop()

        if not self.run_clicked:
            # 首次运行才需要重置监控面板
            self.reset_simulation()
            self.dispatch_event_table.setVisible(True)
            self.compute_node_table.setVisible(True)
            self.show_monitor_panel()
            self.run_clicked = True    
            self.stackedWidget.setCurrentIndex(0)

        self.reset_clocks()
        self.set_running_state()
        
        # 从当前状态继续运行
        if not self.playing:
            self.playing = True
            # 确保时间偏移量属性存在
            if not hasattr(self, 'time_offset'):
                self.time_offset = 0.0
            # 重新初始化仿真时间基准，但保留已有的时间偏移
            self.simulation_start_time = QDateTime.currentDateTime().toMSecsSinceEpoch() / 1000.0
            self.animation_timer.start(30)
            # 根据是否首次运行显示不同消息
            status_msg = "开始播放调度轨迹" if not self.run_clicked else "继续播放调度轨迹"
            self.ui.statusBar().showMessage(status_msg)

    def end_running(self):
        """
        结束仿真运行，停止所有计时器和动画，但保留已显示的数据
        不重置表格内容，不清除已加载的事件数据
        """
        # 停止动画计时器
        if hasattr(self, 'animation_timer') and self.animation_timer.isActive():
            self.animation_timer.stop()

        # 关闭当前窗口
        import psutil
        for proc in psutil.process_iter(['name', 'exe', 'cmdline']):
            try:
                # 检查进程名是否为 mintty.exe
                if proc.info['name'] == 'mintty.exe':
                    exe_path = proc.info['exe'] or ""
                    target_dir = os.path.normcase(self.OMNETPP_DIR)  # 统一路径格式（Windows 下转小写+反斜杠）
                    exe_dir = os.path.normcase(os.path.dirname(exe_path))
                    if target_dir in exe_dir:  # 严格匹配目录
                        proc.terminate()
            except psutil.NoSuchProcess:
                continue
            except psutil.AccessDenied:
                QMessageBox.critical(self, "错误","无法关闭mintty窗口，需要管理员权限，请手动关闭！")
                continue

        if hasattr(self, 'runner'):
            del self.runner

        # 停止文件监控计时器
        if hasattr(self, 'files_check_timer') and self.files_check_timer.isActive():
            self.files_check_timer.stop()

        # 停止所有正在进行的动画
        for anim in self.animations[:]:
            if hasattr(anim, 'remove_animation'):
                anim.remove_animation()
        self.animations.clear()

        # 重置播放状态但不清除数据
        self.playing = False
        self.run_clicked = False

        # 清除当前高亮行
        if hasattr(self, 'last_highlighted_row') and self.last_highlighted_row != -1:
            self.clear_highlight(self.last_highlighted_row)
            self.last_highlighted_row = -1

        # 更新状态栏显示
        self.ui.statusBar().showMessage("仿真已停止", 3000)

        # 清除时间基准（如果存在）
        if hasattr(self, 'simulation_start_time'):
            delattr(self, 'simulation_start_time')

        # 清除已处理事件标记（如果存在）
        if hasattr(self, 'event_processed_flags'):
            delattr(self, 'event_processed_flags')

        if not hasattr(self, 'has_played'):
            self.has_played = True

        self.set_non_running_state()

        # 保留以下数据不被清除：
        # - self.events (已加载的事件列表)
        # - self.all_events_data (所有事件数据)
        # - self.schedule_row_count (已加载的行数)
        # - self.dispatch_event_table (表格中显示的数据)
        # - self.last_csv_file_size (最后文件大小)
        # - self.dispatch_events_csv_mtime (最后修改时间)

    def on_stop(self):
        self.end_running()
        if hasattr(self, "has_played"):
            delattr(self, "has_played")

    def setup_monitor_panel(self):
        # 从UI文件获取或创建新的DockWidget
        self.monitor_dock = self.ui.findChild(QDockWidget, "monitorDockWidget")
        if not self.monitor_dock:
            self.monitor_dock = QDockWidget("监控面板", self)
            self.monitor_dock.setObjectName("monitorDockWidget")
        
        # 初始设置为隐藏状态
        self.monitor_dock.hide()
        
        # 配置DockWidget属性
        self.monitor_dock.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        self.monitor_dock.setFloating(False)
        
        # 创建stackedWidget
        self.stackedWidget = QStackedWidget()
        
        # 创建网络状态页面（矩阵式布局：用户节点 vs 算力节点）
        self.network_status_widget = QWidget()
        self.network_status_layout = QVBoxLayout() 
        
        # 1. 先定义控制按钮组件
        self.control_buttons_widget = QWidget()  
        self.control_buttons_layout = QHBoxLayout(self.control_buttons_widget)
        
        # 添加刷新按钮
        self.refresh_btn = QPushButton("刷新状态")
        self.refresh_btn.clicked.connect(self.force_refresh_network_status)
        self.control_buttons_layout.addWidget(self.refresh_btn)
        
        self.control_buttons_layout.addStretch()  # 填充空白
        
        # 2. 再将控制按钮组件添加到主布局
        self.network_status_layout.addWidget(self.control_buttons_widget)
        
        # 创建滚动区域以容纳多个表格
        self.network_scroll_area = QScrollArea()
        self.network_scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.network_scroll_area.setWidget(self.scroll_content)
        
        # 将滚动区域添加到网络状态布局
        self.network_status_layout.addWidget(self.network_scroll_area)
        self.network_status_widget.setLayout(self.network_status_layout)
        
        # 创建矩阵表格说明标签
        self.matrix_description = QLabel("用户节点与算力节点延迟矩阵 (单位: ms)")
        self.matrix_description.setStyleSheet("font-weight: bold; text-align: center; padding: 5px;")
        self.matrix_description.setAlignment(Qt.AlignCenter)
        
        # 创建延迟矩阵表格
        self.delay_matrix_table = QTableWidget()
        self.configure_delay_matrix_table()
        
        # 创建丢包率标签
        self.packet_loss_label = QLabel("丢包率: 0%")
        self.packet_loss_label.setStyleSheet("font-weight: bold; padding: 5px;")
        
        self.matrix_description.hide()
        self.delay_matrix_table.hide()
        self.packet_loss_label.hide()

        # 添加到网络状态布局
        self.network_status_layout.addWidget(self.matrix_description)
        self.network_status_layout.addWidget(self.delay_matrix_table)
        self.network_status_layout.addWidget(self.packet_loss_label)
        self.network_status_widget.setLayout(self.network_status_layout)
        
        # 创建调度事件页面
        self.dispatch_event_widget = QWidget()
        self.dispatch_event_layout = QVBoxLayout()
        self.dispatch_event_table = QTableWidget()
        self.configure_dispatch_event_table()
        self.dispatch_event_table.setVisible(False) 
        self.dispatch_event_layout.addWidget(self.dispatch_event_table)
        self.dispatch_event_widget.setLayout(self.dispatch_event_layout)

        #算力节点状态页面
        self.compute_node_widget = QWidget()
        self.compute_node_layout = QVBoxLayout()
        
        # 算力节点页面控制按钮
        self.compute_node_controls = QWidget()
        self.compute_node_controls_layout = QHBoxLayout(self.compute_node_controls)
        
        self.compute_node_controls_layout.addStretch()
        self.compute_node_layout.addWidget(self.compute_node_controls)
        
        # 创建表格显示算力节点状态
        self.compute_node_table = QTableWidget()
        self.compute_node_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 禁止编辑
        self.compute_node_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.compute_node_table.setMinimumHeight(300)
        self.compute_node_table.setVisible(False)
        self.compute_node_table.setMouseTracking(True)
        # 添加鼠标悬停显示任务详情的功能
        def show_task_tooltip(row, col):
            if col == 9:  # 任务队列列
                item = self.compute_node_table.item(row, col)
                if item:
                    task_queue = item.data(Qt.UserRole)
                    if task_queue:
                        tooltip_text = "任务队列:\n"
                        for task in task_queue:
                            tooltip_text += f"任务ID: {task['taskId']}, 排队时间: {task['queuingTime']}s\n"
                        QToolTip.showText(QCursor.pos(), tooltip_text.strip())
        # 连接信号
        self.compute_node_table.cellEntered.connect(show_task_tooltip)
        self.compute_node_table.horizontalHeader().setStretchLastSection(True)
        self.compute_node_table.verticalHeader().setVisible(False)
        self.compute_node_table.setAlternatingRowColors(True)
        self.compute_node_table.setShowGrid(False)
        
        # 配置表格列标题
        self.configure_compute_node_table()
        
        # 添加表格到布局
        self.compute_node_layout.addWidget(self.compute_node_table)
        self.compute_node_widget.setLayout(self.compute_node_layout)

        # 将所有页面添加到stackedWidget
        self.stackedWidget.addWidget(self.dispatch_event_widget)       # 索引0
        self.stackedWidget.addWidget(self.network_status_widget)       # 索引1
        self.stackedWidget.addWidget(self.compute_node_widget)         # 索引2
        
        # 创建标签页切换控件
        self.tab_selector = QWidget()
        self.tab_selector_layout = QHBoxLayout(self.tab_selector)
        self.tab_selector_layout.setContentsMargins(5, 2, 5, 2)
        
        # 网络状态标签按钮
        self.network_tab_btn = QPushButton("仿真事件")
        self.network_tab_btn.setCheckable(True)
        self.network_tab_btn.setChecked(True)
        self.network_tab_btn.clicked.connect(lambda: self.switch_monitor_tab(0))
        self.tab_selector_layout.addWidget(self.network_tab_btn)
        
        # 调度事件标签按钮
        self.dispatch_tab_btn = QPushButton("网络状态")
        self.dispatch_tab_btn.setCheckable(True)
        self.dispatch_tab_btn.clicked.connect(lambda: self.switch_monitor_tab(1))
        self.tab_selector_layout.addWidget(self.dispatch_tab_btn)
        
        # 算力节点标签按钮
        self.compute_node_tab_btn = QPushButton("算力状态")
        self.compute_node_tab_btn.setCheckable(True)
        self.compute_node_tab_btn.clicked.connect(lambda: self.switch_monitor_tab(2))
        self.tab_selector_layout.addWidget(self.compute_node_tab_btn)

        self.dispatch_event_table.setMinimumHeight(50)  # 最小高度
        self.dispatch_event_table.setMaximumHeight(600)  # 最大高度

        self.compute_node_table.setMinimumHeight(50)
        self.compute_node_table.setMaximumHeight(600)

        self.delay_matrix_table.setMinimumHeight(50)
        self.delay_matrix_table.setMaximumHeight(600)

       # 添加尺寸调整手柄
        self.resize_handle = QWidget()
        self.resize_handle_layout = QHBoxLayout(self.resize_handle)
        self.resize_handle_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建尺寸调整控件
        size_grip = QSizeGrip(self.resize_handle)
        self.resize_handle_layout.addStretch()
        self.resize_handle_layout.addWidget(size_grip)
        self.resize_handle_layout.addStretch()
        
        # 设置调整手柄样式
        self.resize_handle.setStyleSheet("""
            background-color: #f0f0f0;
            border-top: 1px solid #ccc;
        """)
        self.resize_handle.setMinimumHeight(20)
        
        # 组装最终布局
        self.monitor_main_layout = QVBoxLayout()
        self.monitor_main_layout.addWidget(self.tab_selector)
        self.monitor_main_layout.addWidget(self.stackedWidget)
        self.monitor_main_layout.addWidget(self.resize_handle) 
        
        self.monitor_main_widget = QWidget()
        self.monitor_main_widget.setLayout(self.monitor_main_layout)
        
        # 设置DockWidget内容
        self.monitor_dock.setWidget(self.monitor_main_widget)
        self.monitor_dock.setMinimumSize(100, 10)
        self.monitor_dock.setMaximumHeight(2000)  
        
        # 设置标题栏菜单
        self.setup_title_bar_menu(self.monitor_dock, "仿真监控", self.hide_monitor_panel)
        
        # 初始显示网络状态页面
        self.stackedWidget.setCurrentIndex(0)

        # 初始化变量
        self.all_node_data = []  # 存储所有节点数据
        self.latest_node_data = []  # 存储最新节点数据
        
        # 调试输出
        print(f"监控面板初始化完成，包含{self.stackedWidget.count()}个标签页")

    def configure_compute_node_table(self):
        """配置算力节点表格的列标题和属性"""
        columns = [
            "算力节点ID",
            "所属算力网关编号",
            "IP地址",
            "子网掩码",
            "算力类型",
            "计算能力(FLOPS)",
            "可用存储空间(GB)",
            "开关电容(fF)",
            "静态功耗(nW)",
            "价格(元/s)",
            "任务队列"
        ]
        self.compute_node_table.setColumnCount(len(columns))
        self.compute_node_table.setHorizontalHeaderLabels(columns)
        self.compute_node_table.verticalHeader().setVisible(False)

        # 设置列宽
        column_widths = [100, 120, 120, 120, 80, 140, 120, 100, 100, 100, 200]
        for i, width in enumerate(column_widths):
            self.compute_node_table.setColumnWidth(i, width)

    def switch_monitor_tab(self, index):
        """切换监控面板的标签页"""
        # 更新按钮状态
        self.network_tab_btn.setChecked(index == 0)
        self.dispatch_tab_btn.setChecked(index == 1)
        self.compute_node_tab_btn.setChecked(index == 2)
        
        # 切换页面
        self.stackedWidget.setCurrentIndex(index)
        
        # 如果切换到算力节点页面且表格为空，则刷新数据
        if index == 2 and self.compute_node_table.rowCount() == 0:
            self.load_compute_node_status()
    
    def load_compute_node_status(self):
        """加载并解析算力节点状态JSON文件"""
        try:
            file_path = os.path.join(self.PROJECT_DIR, "compute_node_status.json")  # 假设JSON文件路径
            if not os.path.exists(file_path):
                print(f"算力节点状态文件不存在: {file_path}")
                return False
            
            # 检查文件是否更新
            current_mtime = os.path.getmtime(file_path)
            if current_mtime == self.compute_node_status_json_mtime:
                return True  # 文件未更新，无需处理
            
            self.compute_node_status_json_mtime = current_mtime
            
            self.compute_node_status_json_reader.update(file_path)

            data = self.compute_node_status_json_reader.get_node_status()

            self.populate_compute_node_table(data)
            
        except Exception as e:
            print(f"加载算力节点状态失败: {str(e)}")
            return False

    def populate_compute_node_table(self, node_data: dict):
        # 清空表格
        self.compute_node_table.clear()

        # 设置表头
        headers = [
            "节点ID", "存储空间(GB)", "算力类型", "计算能力(FLOPS)",
            "开关电容(fF)", "静态功耗(nW)", "价格(元/s)", "能源混合参数",
            "可用存储(GB)", "任务队列"
        ]
        self.compute_node_table.setColumnCount(len(headers))
        self.compute_node_table.setHorizontalHeaderLabels(headers)

        # 获取节点数据
        node_states = node_data.get("nodeStates", [])

        # 设置行数
        self.compute_node_table.setRowCount(len(node_states))

        node_dict = defaultdict(lambda: None)
        node_dict.update({
            node.index: node
            for node in self.nodes
            if node.nodetype == "ComputingNode"
        })

        # 填充表格数据
        for row, node_state in enumerate(node_states):
            node_id = node_state["nodeId"]
            node = node_dict.get(node_id)

            # 节点ID
            item = QTableWidgetItem(str(node_id))
            self.compute_node_table.setItem(row, 0, item)

            # 节点属性
            if node:
                # 存储空间
                node:ComputingNode
                item = QTableWidgetItem(str(node.storage_space))
                self.compute_node_table.setItem(row, 1, item)

                # 计算类型
                computing_type = "CPU" if node.computing_type == 0 else "GPU"
                item = QTableWidgetItem(computing_type)
                self.compute_node_table.setItem(row, 2, item)

                # 计算能力
                item = QTableWidgetItem(f"{node.computing_power:.2e}")
                self.compute_node_table.setItem(row, 3, item)

                # 开关电容
                item = QTableWidgetItem(f"{node.switching_capacitance:.2e}")
                self.compute_node_table.setItem(row, 4, item)

                # 静态功耗
                item = QTableWidgetItem(f"{node.static_power:.2e}")
                self.compute_node_table.setItem(row, 5, item)

                # 价格
                item = QTableWidgetItem(str(node.price))
                self.compute_node_table.setItem(row, 6, item)

                # 能源混合参数
                item = QTableWidgetItem(str(node.power_mix))
                self.compute_node_table.setItem(row, 7, item)

            # 可用存储
            item = QTableWidgetItem(str(node_state["availableStorage"]))
            self.compute_node_table.setItem(row, 8, item)

            # 任务队列 - 显示任务数量，悬停显示详情
            task_queue = node_state.get("taskQueue", [])
            task_count = len(task_queue)
            item = QTableWidgetItem(f"{task_count}个任务")
            item.setData(Qt.UserRole, task_queue)  # 存储任务详情数据
            self.compute_node_table.setItem(row, 9, item)

        # 调整列宽
        self.compute_node_table.resizeColumnsToContents()
        self.compute_node_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.compute_node_table.horizontalHeader().setStretchLastSection(True)

        # 显示表格
        self.compute_node_table.setVisible(True)

    def force_refresh_network_status(self):
        """强制刷新网络状态信息"""
        if os.path.exists(self.network_status_json):
            try:
                with open(self.network_status_json, 'r') as f:
                    network_status = json.load(f)
                    self.update_network_status_panel(network_status)  # 直接调用更新方法
            except json.JSONDecodeError:
                QMessageBox.critical(self, "错误", "无法解析 network_status.json 文件")
        else:
            QMessageBox.warning(self, "警告", "未找到 network_status.json 文件")

    def configure_delay_matrix_table(self):
        """配置延迟矩阵表格的基本属性"""
        self.delay_matrix_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.delay_matrix_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.delay_matrix_table.setAlternatingRowColors(True)
        # 设置表格样式
        self.delay_matrix_table.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: #f0f0f0; }")
        self.delay_matrix_table.verticalHeader().setStyleSheet("QHeaderView::section { background-color: #f0f0f0; }")
        header = self.delay_matrix_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive) 
        self.delay_matrix_table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.delay_matrix_table.verticalHeader().setDefaultSectionSize(30)  # 行标题宽度
        
        # 水平表头设置最小宽度
        header.setMinimumSectionSize(100)  # 列最小宽度

        def force_set_column_widths():
            # 确保表格有数据列
            if self.delay_matrix_table.columnCount() == 0:
                QTimer.singleShot(100, force_set_column_widths)
                return
                
            # 水平表头
            horizontal_header = self.delay_matrix_table.horizontalHeader()
            base_width = 100  # 基础列宽，可根据需要调整
            for col in range(self.delay_matrix_table.columnCount()):
                width = base_width + 50 if col == 0 else base_width
                horizontal_header.setSectionResizeMode(col, QHeaderView.Fixed)  # 固定宽度
                self.delay_matrix_table.setColumnWidth(col, width)

            horizontal_header.setStretchLastSection(False)
            total_width = sum(self.delay_matrix_table.columnWidth(col) for col in range(self.delay_matrix_table.columnCount()))
            self.delay_matrix_table.setMinimumWidth(total_width + 50) 

        force_set_column_widths()

    def show_monitor_panel(self):
        """显示监控面板"""
        if not hasattr(self, 'monitor_dock') or not self.monitor_dock:
            self.setup_monitor_panel()
        
        self.monitor_dock.show()
        self.update_monitor_menu_state()

    def hide_monitor_panel(self):
        """隐藏监控面板"""
        if hasattr(self, 'monitor_dock') and self.monitor_dock:
            self.monitor_dock.hide()
            self.update_monitor_menu_state()

    def setup_title_bar_menu(self, dock_widget, title_text, close_method):
        """通用方法：为DockWidget设置标题栏菜单"""
        title_bar = dock_widget.titleBarWidget()
        if not title_bar:
            title_bar = QWidget()
            dock_widget.setTitleBarWidget(title_bar)

        # 创建标题栏布局
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)

        # 添加标题标签
        title_label = QLabel(f"      {title_text}     ")
        title_layout.addWidget(title_label)

        # 添加伸缩项，使按钮靠右
        title_layout.addStretch()
        title_layout.addStretch()
        title_layout.addStretch()
        title_layout.addStretch()
        title_layout.addStretch()
        
        # 添加关闭按钮
        close_button = QToolButton()
        close_button.setText("×")
        close_button.setToolTip("关闭")
        close_button.clicked.connect(close_method)
        title_layout.addWidget(close_button)

        # 添加伸缩项，使标题居左，菜单居右
        title_layout.addStretch()

    def configure_dispatch_event_table(self):
        """配置调度事件表格的基本属性"""
        self.dispatch_event_table.setColumnCount(7)
        self.dispatch_event_table.setHorizontalHeaderLabels(["时间戳", "消息类型", "消息ID", "源节点类型", "源节点ID", "目标节点类型", "目标节点ID"])
        self.dispatch_event_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.dispatch_event_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.dispatch_event_table.setAlternatingRowColors(True)
        
        header = self.dispatch_event_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        # 设置列宽
        # self.dispatch_event_table.setColumnWidth(0, 80)
        # self.dispatch_event_table.setColumnWidth(1, 140)
        # self.dispatch_event_table.setColumnWidth(2, 80)
        # self.dispatch_event_table.setColumnWidth(3, 120)
        # self.dispatch_event_table.setColumnWidth(4, 80)
        # self.dispatch_event_table.setColumnWidth(5, 120)
        # self.dispatch_event_table.setColumnWidth(6, 80)

    def toggle_monitor(self, checked):
        """切换监控面板的显示/隐藏状态"""
        if checked:
            self.show_monitor_panel()
        else:
            self.hide_monitor_panel()

    def update_monitor_menu_state(self):
        """更新监控面板菜单项的状态"""
        if hasattr(self, 'show_monitor_action') and self.show_monitor_action:
            self.show_monitor_action.setChecked(self.monitor_dock.isVisible())

    def check_network_status_changes(self):
        """检查网络状态JSON文件变化，处理空文件和解析错误"""
        current_modified = 0.0
        if not os.path.exists(self.network_status_json):
            return

        # 检查文件是否为空
        if os.path.getsize(self.network_status_json) == 0:
            return

        try:
            current_modified = os.path.getmtime(self.network_status_json)
        except OSError:
            return

        # 如果仿真未运行或监控面板不可见，不检查更新
        if not self.run_clicked or not hasattr(self, 'monitor_dock') or not self.monitor_dock.isVisible():
            return

        # 检查文件是否有更新
        if current_modified > self.network_status_json_mtime and current_modified != 0:
            print("检测到网络状态JSON文件更新，刷新监控面板...")
            self.network_status_json_mtime = current_modified

            try:
                with open(self.network_status_json, 'r') as f:
                    # 再次检查文件是否为空（防止在检查后被清空）
                    if os.fstat(f.fileno()).st_size == 0:
                        return

                    network_status = json.load(f)
                    self.update_network_status_panel(network_status)

            except json.JSONDecodeError as e:
                QMessageBox.critical(
                    self,
                    "文件解析错误",
                    f"无法解析 network_status.json 文件:\n{str(e)}\n"
                    f"文件可能已损坏或不完整。"
                )
                return
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "文件读取错误",
                    f"读取 network_status.json 时发生意外错误:\n{str(e)}"
                )
                return

    def check_csv_update(self):
        """检查CSV文件是否有更新"""
        try:
            self.load_csv_events()
        except Exception as e:
            QMessageBox.critical(self, "csv文件监控错误", str(e))
            print(f"csv文件监控错误: {e}")

    def _check_panel_visibility(self):
        """检查面板可见性并更新相关状态"""
        if hasattr(self, 'dispatch_event_dock') and self.dispatch_event_dock:
            self.show_dispatch_event_action.setChecked(self.dispatch_event_dock.isVisible())

    def eventFilter(self, obj, event):
        if obj == self.ui.graphicsView.viewport():
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasFormat("application/x-node-type"):
                    event.acceptProposedAction()
                    return True
            elif event.type() == QEvent.DragMove:
                event.acceptProposedAction()
                return True
            elif event.type() == QEvent.Drop:
                mime_data = event.mimeData()
                if mime_data.hasFormat("application/x-node-type"):
                    node_type = mime_data.data("application/x-node-type").data().decode()
                    scene_pos = self.ui.graphicsView.mapToScene(event.position().toPoint())
                    self.create_dragged_node(node_type, scene_pos)
                    event.acceptProposedAction()
                    return True
                
        # 处理鼠标事件
        if obj == self.ui.graphicsView.viewport():
            if event.type() == QEvent.Type.MouseButtonPress:
                self.mouse_press_event(event)
                if event.button() == Qt.RightButton:
                    scene_pos = self.ui.graphicsView.mapToScene(event.position().toPoint())
                    # items = self.scene.items(scene_pos)
                return super().eventFilter(obj, event)
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self.mouse_release_event(event)
            elif event.type() == QEvent.Type.MouseMove:  # 添加鼠标移动事件处理
                self.mouse_move_event(event)
                return super().eventFilter(obj, event)
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
        if not self.scene_editable_state:
            add_action.setEnabled(False)
        menu.exec(self.ui.listWidget.mapToGlobal(pos))
        
    def add_node(self, list_item):
        # 根据ListWidget的item生成节点
        icon_path = f"icon/{list_item.text().lower().replace(' ', '_')}.png"
        nodetype = self.getNodeType(list_item.text())

        command = AddNodeCommand(self, list_item.text(), nodetype, icon_path)
        self.undo_stack.push(command)
        print(self.typeNumDict)

    def undo(self):
        self.undo_stack.undo()

    def redo(self):
        self.undo_stack.redo()

    def select_all(self):
        for node in self.nodes:
            node.setSelected(True)
        for channel in self.channels:
            channel.setSelected(True)

    def update_network_status_panel(self, network_status):
        """更新矩阵式网络状态表格，正确解析JSON数据"""
        # 清除现有内容
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 创建标题
        matrix_title = QLabel(f"时延矩阵 (触发任务: {network_status['triggeringTaskId']})")
        matrix_title.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.scroll_layout.addWidget(matrix_title)

        # 获取矩阵数据
        delay_matrix = network_status["delayMatrix"]
        user_ids = delay_matrix["userIds"]
        compute_node_ids = delay_matrix["computeNodeIds"]
        delays = delay_matrix["delays"]

        # 创建表格
        table = QTableWidget(len(user_ids) + 1, len(compute_node_ids) + 1)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectItems)
        table.setAlternatingRowColors(True)

        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setVisible(False)

        # 设置表头 - 左上角单元格
        corner_item = QTableWidgetItem("用户节点\\算力节点")
        corner_item.setBackground(QColor(220, 220, 220))
        corner_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(0, 0, corner_item)

        # 设置列标题（算力节点）
        for col, node_id in enumerate(compute_node_ids, 1):
            item = QTableWidgetItem(f"算力节点 {node_id}")
            item.setBackground(QColor(240, 240, 240))
            item.setTextAlignment(Qt.AlignCenter)
            table.setItem(0, col, item)

        # 设置行标题（用户节点）和填充数据
        for row, user_id in enumerate(user_ids, 1):
            # 行标题
            row_item = QTableWidgetItem(f"用户节点 {user_id}")
            row_item.setBackground(QColor(240, 240, 240))
            row_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 0, row_item)

            # 填充延迟数据
            for col, delay in enumerate(delays[row - 1], 1):
                cell_item = QTableWidgetItem(f"{delay:.1f}")
                cell_item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, col, cell_item)

        # 设置表格属性
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setMinimumHeight(200)
        self.scroll_layout.addWidget(table)

        # 添加时间戳和丢包率信息
        info_widget = QWidget()
        info_layout = QHBoxLayout(info_widget)

        timestamp_label = QLabel(f"时间戳: {network_status['timestamp']}")
        loss_info = network_status["packetLoss"]
        loss_label = QLabel(
            f"丢包率: {loss_info['packetLossRate']}% "
            f"(发送: {loss_info['packetsSentSinceLastLog']}, "
            f"丢弃: {loss_info['packetsDroppedSinceLastLog']})"
        )

        info_layout.addWidget(timestamp_label)
        info_layout.addStretch()
        info_layout.addWidget(loss_label)
        self.scroll_layout.addWidget(info_widget)

    def getNodeType(self, nodeName):
        typeDict = {"用户节点": "UserNode", 
                    "算力节点": "ComputingNode", 
                    "用户网关": "UserGateway", 
                    "算力网关": "ComputingGateway", 
                    "算力调度节点": "ComputeScheduleNode",
                    "路由节点": "Router"}
        return typeDict.get(nodeName, None)
        
    def createNewItemByType(self, nodetype, name, index, icon_path):
        if nodetype == "UserNode":
            return UserNode(name, index, icon_path,self)
        elif nodetype == "ComputingNode":
            return ComputingNode(name, index, icon_path,self)
        elif nodetype == "UserGateway":
            return UserGateway(name, index, icon_path,self)
        elif nodetype == "ComputingGateway":
            return ComputingGateway(name, index, icon_path,self)
        elif nodetype == "ComputeScheduleNode":
            return ComputeScheduleNode(name, index, icon_path,self)
        elif nodetype == "Router":
            return Router(name, index, icon_path, self)
        else:
            raise ValueError("错误的节点类型")
    
    def is_channel_new(self, start, end):
        for channel in self.channels:
            if channel.start_item == start and channel.end_item == end:
                QMessageBox.warning(self,"警告","不能重复插入")
                return False
            elif channel.start_item == end and channel.end_item == start:
                QMessageBox.warning(self, "警告", "不能重复插入")
                return False
        return True

    def mouse_press_event(self, event: QMouseEvent):
        if event.modifiers() == Qt.AltModifier:
            scene_pos = self.ui.graphicsView.mapToScene(event.position().toPoint())
            item = self.scene.itemAt(scene_pos, self.ui.graphicsView.transform())

            if isinstance(item, NodeItem):
                self.start_item = item
                # 保存原始边框并设置红色边框
                self.original_pen_start = item.border_pen
                item.border_pen = QPen(QColor(255, 0, 0), 2, Qt.SolidLine)
                item.update()

                # 创建临时连线
                self.temp_line = QGraphicsLineItem()
                self.temp_line.setPen(QPen(QColor(70, 130, 180), 2, Qt.SolidLine, Qt.RoundCap))
                self.scene.addItem(self.temp_line)

                # 设置起点
                start_point = self.calculate_connection_point(item)
                self.temp_line.setLine(QLineF(start_point, scene_pos))

    def mouse_move_event(self, event: QMouseEvent):
        if hasattr(self, 'temp_line') and self.temp_line:
            # 获取鼠标位置
            viewport_pos = event.position().toPoint()
            scene_pos = self.ui.graphicsView.mapToScene(viewport_pos)

            # 更新临时连线
            start_point = self.calculate_connection_point(self.start_item)
            self.temp_line.setLine(QLineF(start_point, scene_pos))

            # 检测当前悬停的节点
            items = self.scene.items(scene_pos)
            # print(len(items))
            hover_node = None
            for item in items:
                if isinstance(item, NodeItem) and item != self.start_item:
                    hover_node = item
                    break
            # 清除之前的高亮节点
            if hasattr(self, 'last_hover_node') and self.last_hover_node and hasattr(self, 'original_pen_end'):
                self.last_hover_node.setSelected(False)
                self.last_hover_node.border_pen = self.original_pen_end  # 恢复蓝色虚线边框
                self.last_hover_node.update()
                del self.last_hover_node

            # 高亮当前悬停的节点
            if hover_node:
                self.original_pen_end = hover_node.border_pen
                hover_node.border_pen = QPen(QColor(255, 0, 0), 2, Qt.SolidLine)
                hover_node.setSelected(True)
                hover_node.update()
                self.last_hover_node = hover_node  # 记录当前悬停节点

    def mouse_release_event(self, event: QMouseEvent):
        if hasattr(self, 'temp_line') and self.temp_line:
            viewport_pos = event.position().toPoint()
            scene_pos = self.ui.graphicsView.mapToScene(viewport_pos)
            items = self.scene.items(scene_pos)
            end_node = None
            for item in items:
                if isinstance(item, NodeItem) and item != self.start_item:
                    end_node = item
                    break

            self.scene.removeItem(self.temp_line)
            del self.temp_line

            # 恢复原始边框
            if hasattr(self, 'start_item'):
                self.start_item.border_pen = self.original_pen_start
                self.start_item.update()
                self.start_item.setSelected(False)

            # 检查是否释放到有效节点上
            if isinstance(end_node, NodeItem) and end_node != self.start_item and self.is_channel_new(self.start_item, end_node):
                # 创建带样式的Channel
                channel_pen = QPen(QColor(70, 130, 180), 2, Qt.SolidLine, Qt.RoundCap)
                command = AddChannelCommand(self, self.start_item, end_node, channel_pen)
                self.undo_stack.push(command)

            if isinstance(end_node, NodeItem) and end_node != self.start_item:
                # 恢复
                if hasattr(self, "original_pen_end"):
                    end_node.border_pen = self.original_pen_end
                    end_node.update()
                    end_node.setSelected(False)
                else:
                    raise RuntimeError("未知错误")

            if hasattr(self, 'start_item'):
                del self.start_item

    def calculate_connection_point(self, node):
        """计算节点与目标点的连接点"""
        node_rect = node.boundingRect()
        node_pos = node.scenePos()
        center = node_pos + QPointF(node_rect.width() / 2, node_rect.height() / 2)
        return center

    def remove_channel(self, channel):
        command = DeleteChannelCommand(self, channel)
        self.undo_stack.push(command)

    def remove_node(self, node):
        command = DeleteNodeCommand(self, node)
        self.undo_stack.push(command)
  
    def generate_config_files(self):
        if (not self.PROJECT_DIR) or (not os.path.exists(self.PROJECT_DIR)):
            QMessageBox.critical(self,'错误',"请检查项目路径配置！")
            return

        try:
            import file_utils
            # 2. 构建目标路径 inet/examples/computing_power_network
            target_dir = self.PROJECT_DIR

            # 3. 处理 network.ned 文件
            ned_path = os.path.join(target_dir, "network.ned")
            nedwriter = file_utils.NEDWriter(ned_path,self.nodes,self.channels,self.PROJECT_NAME)
            nedwriter.write()
            del nedwriter

            # 4. 处理 omnetpp.ini 文件
            ini_path = os.path.join(target_dir, "omnetpp.ini")
            iniwriter = file_utils.INIWriter(ini_path,self.nodes,self.channels,self.PROJECT_NAME)
            iniwriter.write()
            del iniwriter

            # 5. 处理 config.xml 文件
            xml_path = os.path.join(target_dir, "config.xml")
            xmlwriter = file_utils.XMLWriter(xml_path,self.nodes,self.channels)
            xmlwriter.write()
            del xmlwriter

            # 6. 写入任务文件
            taskwriter = file_utils.TaskWriter(self.nodes,self.PROJECT_DIR)
            taskwriter.write()
            del taskwriter

            # 7. 写入拓扑文件
            file_utils.write_network_topology(self.nodes, self.PROJECT_DIR)

        except Exception as e:
            QMessageBox.critical(None, "错误", f"提交过程中出现错误：{str(e)}")
            raise e
    
    # 清除所有节点
    def on_clear(self):
        self.nodes = []
        self.channels = []
        self.typeNumDict = {"UserNode": 0,
                            "ComputingNode": 0,
                            "UserGateway": 0,
                            "ComputingGateway": 0,
                            "ComputeScheduleNode": 0,
                            "Router": 0}
        self.indexDict = {
            "UserNode": 0,
            "ComputingNode": 0,
            "UserGateway": 0,
            "ComputingGateway": 0,
            "ComputeScheduleNode": 0,
            "Router": 0
        }
        self.scene.clear()
        if hasattr(self, "has_played"):
            delattr(self, "has_played")

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
        """
        加载文件
        """
        # 打开文件对话框，获取用户选择的文件路径
        file_path, _ = QFileDialog.getOpenFileName(
            None,  # 父窗口（None 表示顶层窗口）
            "选择要加载的网络数据文件",  # 窗口标题
            "",  # 默认目录（空字符串表示当前目录）
            "Pickle 文件 (*.pickle);;所有文件 (*.*)"  # 过滤文件类型
        )
        try:
            # 用户可能取消选择，因此要检查文件路径是否为空
            if file_path:
                self.load_from_file(file_path)
        except Exception as e:
            QMessageBox.critical(self,'错误！',f'加载网络文件出错：{e}')
            self.on_clear()
    
    def save_to_file(self, filename="network_data.pickle"):
        #保存当前的节点和连线数据到文件
        try:
            with open(filename, "wb") as file:
                nodes_data = [node for node in self.nodes]
                channels_data = [ChannelInfo(channel) for channel in self.channels]
                data = {
                    "nodes": nodes_data,
                    "channels": channels_data,
                    "typeNumDict": self.typeNumDict,
                    "indexDict": self.indexDict,
                }
                pickle.dump(data, file)
                QMessageBox.information(self, '保存成功', f"数据已成功保存到 {filename}")
        except Exception as e:
            QMessageBox.critical(self,'保存失败',f"保存失败: {e}")
            raise e

    def load_from_file(self, filename="network_data.pickle"):
        """从文件中加载节点和连线数据"""
        with open(filename, "rb") as file:
            data = pickle.load(file)
            self.on_clear()  # 清空现有的节点和连线
            node_map = {}
            for node in data["nodes"]:
                x = node.x
                y = node.y
                node.mainwindow = self
                node.setPos(x, y)
                node.delete_self.connect(self.remove_node)
                self.scene.addItem(node)
                self.nodes.append(node)
                typeAndIndex = (node.nodetype, node.index)
                node_map[typeAndIndex] = node
                if node.index > self.indexDict[node.nodetype]:
                    self.indexDict[node.nodetype] = node.index
            for channel_data in data["channels"]:
                start_type = channel_data.start_type
                start_index = channel_data.start_index
                end_type = channel_data.end_type
                end_index = channel_data.end_index
                pen = channel_data.get_pen()
                start_typeAndNode = (start_type, start_index)
                end_typeAndNode = (end_type, end_index)

                if start_typeAndNode in node_map and end_typeAndNode in node_map:
                    start_node = node_map[start_typeAndNode]
                    end_node = node_map[end_typeAndNode]
                    channel = Channel(start_node, end_node, pen, channel_data)
                    self.scene.addItem(channel)
                    self.channels.append(channel)
                    start_node.channelList.unlock()
                    end_node.channelList.unlock()
                    start_node.channelList.append(channel)
                    end_node.channelList.append(channel)
                    start_node.channelList.lock()
                    end_node.channelList.lock()

            self.indexDict = data["indexDict"]
            self.typeNumDict = data["typeNumDict"]
            QMessageBox.information(self,'加载成功',f"数据已成功从 {filename} 加载")

    def type_to_name(self, nodetype):
        nameDict = {"UserNode": "用户节点", 
                    "ComputingNode": "算力节点", 
                    "UserGateway": "用户网关", 
                    "ComputingGateway": "算力网关",
                    "ComputeScheduleNode": "算力调度节点",
                    "Router": "路由节点"}
        return nameDict.get(nodetype, None)

    def on_config(self):
        """显示配置对话框并更新路径"""
        from PathConfig import PathConfigDialog
        dialog = PathConfigDialog(self.OMNETPP_DIR, self.PROJECT_NAME,self)
        if dialog.exec() == QDialog.Accepted:
            paths = dialog.get_config()
            self.OMNETPP_DIR = paths["OMNETPP_DIR"]
            self.PROJECT_DIR = paths["PROJECT_DIR"]
            self.PROJECT_NAME = paths["PROJECT_NAME"]
            self.network_status_json = os.path.join(self.PROJECT_DIR, "network_status.json")
            self.dispatch_events_csv = os.path.join(self.PROJECT_DIR, "dispatch_events.csv")
            self.compute_node_status_json = os.path.join(self.PROJECT_DIR, "compute_node_status.json")
            # 重置文件修改时间
            self.dispatch_events_csv_mtime = 0.0
            self.network_status_json_mtime = 0.0
            self.compute_node_status_json_mtime = 0.0
            # 更新状态栏
            display_name = self.PROJECT_NAME if len(self.PROJECT_NAME) < 30 else (self.PROJECT_NAME[0:30]+"...")
            self.ui.statusBar().showMessage(f"设置OMNet++路径成功，项目名为{display_name}")

            QMessageBox.information(self, "提示", "OMNet++设置成功")

    def on_export(self):
        if not self.PROJECT_DIR:
            QMessageBox.critical(self, "错误", "请先配置项目路径！")
            return
        result_path = Path(self.PROJECT_DIR) / "results.json"
        if result_path.exists():
            from simulation_export import SimulationExportDialog
            dialog = SimulationExportDialog(str(result_path), self)
            dialog.show()
        else:
            QMessageBox.information(None, "提示", "结果文件不存在", QMessageBox.Ok)

class CustomListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 启用拖拽功能（保持你原有的设置）
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setStyleSheet("""
            QListWidget::item {
                height: 40px;  /* 增大项的高度，默认约20px */
                font-size: 12pt; /* 增大字体大小 */
                padding: 5px; /* 增加内边距 */
            }
        """)
        
        self.setIconSize(QSize(32, 32))
    def startDrag(self, supported_actions):
        # 获取当前选中的列表项
        selected_items = self.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        # 获取节点类型
        node_type = item.data(Qt.UserRole)
        
        # 创建MIME数据
        mime_data = QMimeData()
        mime_data.setData("application/x-node-type", node_type.encode())
        
        # 启动拖拽
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        if not item.icon().isNull():
            drag.setPixmap(item.icon().pixmap(32, 32))
            
        # 执行拖拽
        drag.exec(Qt.CopyAction)

if __name__ == "__main__":
    app = QApplication([])
    app.setWindowIcon(QIcon("./icon/算力网络.png"))
    window = UserWindow()
    window.ui.show()
    sys.exit(app.exec())