import sys
import pickle
import base64
import traceback
import weakref
from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsView,
                               QGraphicsScene, QGraphicsItem, QListWidget,
                               QMenu, QGraphicsProxyWidget, QLineEdit,
                               QGraphicsPixmapItem, QMessageBox, QDialog)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import (Qt, QPointF, QRectF, QLineF, QEvent, QObject,
                            Signal, QByteArray, QBuffer, QIODevice,
                            SignalInstance)
from PySide6.QtGui import QPixmap, QPen, QColor, QTransform, QAction, QPainterPath
from io import BytesIO
import weakref
from set_ip_and_mask import SetIpAndMask

class ObservableList(list):
    """自定义列表类，任何修改都会触发回调函数"""
    def __init__(self,callback=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._callback = callback
        self._modify_lock = True

    def unlock(self):
        self._modify_lock = False

    def lock(self):
        self._modify_lock = True

    def _notify(self):
        """触发回调（如果存在）"""
        # if hasattr(self, "_modify_lock") and hasattr(self, "_callback"):
        if self._modify_lock and self._callback:
            if callable(self._callback):
                self._callback()

    # 覆盖所有会修改列表的方法
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._notify()

    def __delitem__(self, key):
        super().__delitem__(key)
        self._notify()

    def __iadd__(self, other):
        result = super().__iadd__(other)
        self._notify()
        return result

    def append(self, item):
        super().append(item)
        self._notify()

    def extend(self, items):
        print(type(self))
        super().extend(items)
        self._notify()

    def insert(self, index, item):
        super().insert(index, item)
        self._notify()

    def remove(self, item):
        super().remove(item)
        self._notify()

    def pop(self, index=-1):
        item = super().pop(index)
        self._notify()
        return item

    def clear(self):
        super().clear()
        self._notify()

    def sort(self, **kwargs):
        super().sort(**kwargs)
        self._notify()

    def reverse(self):
        super().reverse()
        self._notify()

    def __setstate__(self, state):
        # 确保属性存在
        self._callback = state.get("_callback", None)
        self._modify_lock = state.get("_modify_lock", True)
        # 恢复列表数据
        self.extend(state.get("data", []))

    def __reduce__(self):
        return (
            self.__class__,  # 要调用的类
            (self._callback, list(self)),  # __init__ 参数
            {"_modify_lock": self._modify_lock}  # 额外属性
        )

class NodeItem(QGraphicsItem, QObject):
    # 定义一个信号，用于在删除节点时发射，传递当前节点对象
    delete_self = Signal(object)

    def __init__(self, name:str, nodetype, index, icon_path, mainwindow, parent=None):
        """
        节点项的构造函数。

        :param name: 节点的类型名称名称
        :param nodetype: 节点的类型
        :param index: 节点的索引
        :param icon_path: 节点图标的路径
        :param parent: 父对象，默认为 None
        """
        # 调用父类 QGraphicsItem 和 QObject 的构造函数
        super().__init__(parent)
        QObject.__init__(self)  # 确保初始化 QObject

        # 为节点生成唯一名称，格式为名称加上索引加 1
        self.name = name + str(index)
        self.nodetype = nodetype
        self.index = index
        # 接口计数器，用于记录接口数量
        self.interface_counter = 0
        # 存储接口 ID 到对象的映射列表
        self.interface_id_to_object = []
        # 主窗口
        self.mainwindow = mainwindow
        self.icon_path = icon_path
        # 加载节点图标
        self.icon = QPixmap(icon_path)
        # 存储与该节点相连的通道列表
        self.channelList = ObservableList(callback=self.update_dicts)
        # 初始化节点的控件，初始值为 0
        self.widget = 0
        # 设置默认的 IP 地址和子网掩码
        self.ip = '111.111.111.111'
        self.mask = '255.255.255.0'
        # 定义节点选中时的边框样式，蓝色虚线边框，线宽为 2
        self.border_pen = QPen(QColor(0, 0, 255), 2, Qt.DashLine)
        # 设置节点可移动
        self.setFlag(QGraphicsItem.ItemIsMovable)
        # 设置节点可选择
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        # 设置节点在几何属性变化时发送通知
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        # 将 itemChange 方法替换为自定义的 item_changed 方法
        self.itemChange = self.item_changed
        # 初始化节点的用户界面
        self.init_ui()

    def init_ui(self):
        """
        初始化节点的用户界面，添加可编辑的文本框。
        """
        # 创建一个 QGraphicsProxyWidget 用于包装 QLineEdit
        self.proxy = QGraphicsProxyWidget(self)
        # 创建一个 QLineEdit 用于显示和编辑节点名称
        self.text_edit = QLineEdit(self.name)
        # 设置 QLineEdit 的样式，背景透明，有灰色边框，最大宽度为 75px
        self.text_edit.setStyleSheet("""
            QLineEdit { 
                background: transparent; 
                max-width: 100px;
            }
        """)
        # 将 QLineEdit 的 editingFinished 信号连接到 update_name 方法，当编辑完成时更新节点名称
        self.text_edit.editingFinished.connect(self.update_name)
        # 将 QLineEdit 设置到 QGraphicsProxyWidget 中
        self.proxy.setWidget(self.text_edit)
        # 将文本框放置在图标下方，垂直偏移为图标高度加 5 像素
        text_x = (self.boundingRect().width() - self.text_edit.width()) / 2
        self.proxy.setPos(text_x, self.icon.height() + 5)

    def getNodeType(self, nodeName):
        """
        根据节点名称获取节点类型。

        :param nodeName: 节点的名称
        :return: 节点的类型，如果未找到则返回 None
        """
        # 定义节点名称到类型的映射字典
        typeDict = {"用户节点": "UserNode",
                    "算力节点": "ComputingNode",
                    "用户网关": "UserGateway",
                    "算力网关": "ComputingGateway",
                    "调度决策网关": "ComputeScheduleNode",
                    "路由器": "Router"}
        return typeDict.get(nodeName, None)

    def __getstate__(self):
        """
        定义节点对象的序列化状态。

        :return: 可序列化的节点状态字典
        """
        state = {}

        for key, value in self.__dict__.items():
            # 跳过不可序列化的 QObject 和 SignalInstance 类型的属性
            if isinstance(value, QObject) or isinstance(value, SignalInstance):
                # 移除不可序列化的类
                continue

            # 跳过 QPixmap 类型的属性，因为它不可直接序列化
            elif isinstance(value, QPixmap) or isinstance(value, QPen):# QPen是我添加的，添加之后报错了
                # 处理 QPixmap 或 QPen
                continue
            # 将可序列化的属性添加到状态字典中
            state[key] = value

        # 记录节点在场景中的 x 坐标
        state["x"] = self.scenePos().x()
        # 记录节点在场景中的 y 坐标
        state["y"] = self.scenePos().y()
        # 清空通道列表，避免序列化时出现问题
        state.pop('channelList')
        # 删除元对象属性，因为它不可序列化
        # del state["__METAOBJECT__"]
        if "__METAOBJECT__" in state.keys():
            state.pop("__METAOBJECT__")
        # print("for循环正确执行")

        return state

    def __setstate__(self, state):
        """
        定义节点对象的反序列化状态。

        :param state: 反序列化的节点状态字典
        """
        nodetype = state["nodetype"]
        name = self.type_to_name(nodetype)
        index = state["index"]
        icon_path = state["icon_path"]
        self.mainwindow = None
        self.__init__(name, index, icon_path, self.mainwindow)
        for key, value in state.items():
            # 跳过类属性，避免覆盖类的信号
            if key in ("delete_self", "destroyed"):
                continue

            # 处理反序列化的 QPixmap
            elif isinstance(value, str) and value.startswith("/9j/"):
                # 解码 Base64 编码的图像数据
                image_data = base64.b64decode(value)
                byte_array = QByteArray(image_data)
                pixmap = QPixmap()
                # 从字节数组加载图像数据到 QPixmap
                pixmap.loadFromData(byte_array, "PNG")
                self.__dict__[key] = pixmap
                continue

            else:
                # 将反序列化的属性赋值给节点对象
                self.__dict__[key] = value

    def shape(self, /):
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def type_to_name(self, nodetype):
        """
        根据节点类型获取节点名称。

        :param nodetype: 节点的类型
        :return: 节点的名称，如果未找到则返回 None
        """
        # 定义节点类型到名称的映射字典
        nameDict = {"UserNode": "用户节点",
                    "ComputingNode": "算力节点",
                    "UserGateway": "用户网关",
                    # "UserRouter": "用户网关",
                    # "ComputingRouter": "算力网关",
                    "ComputingGateway": "算力网关",
                    "ComputeScheduleNode": "调度决策网关",
                    "Router": "路由器"}
        return nameDict.get(nodetype, None)

    def boundingRect(self):
        """确保边界矩形包含整个节点（图标 + 文本）"""
        icon_width = self.icon.width()
        icon_height = self.icon.height()
        text_width = self.text_edit.width()
        text_height = self.text_edit.height()

        # 计算最大宽度和总高度
        max_width = max(icon_width, text_width)
        total_height = icon_height + text_height + 5  # 5 是间距

        return QRectF(0, 0, max_width, total_height)

    def paint(self, painter, option, widget=None):
        """
        绘制节点的图标和选中状态边框。

        :param painter: 绘图工具
        :param option: 绘图选项
        :param widget: 绘图的父控件，默认为 None
        """
        # 绘制图标
        if hasattr(self, 'icon'):
            # 计算图标居中绘制的位置
            icon_x = (self.boundingRect().width() - self.icon.width()) / 2
            painter.drawPixmap(icon_x, 0, self.icon)

        # 绘制选中状态边框
        if self.isSelected():
            rect = self.boundingRect()
            painter.setPen(self.border_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)

    def mouseDoubleClickEvent(self, event):
        """
        处理节点的鼠标双击事件，聚焦到文本框。

        :param event: 鼠标事件
        """
        # 双击时聚焦到文本框
        self.text_edit.setFocus()

    def update_name(self):
        """
        更新节点的名称，将文本框中的内容赋值给节点名称属性。
        """
        self.name = self.text_edit.text()

    def mousePressEvent(self, event):
        """
        处理节点的鼠标按下事件，支持单选和多选操作。

        :param event: 鼠标事件
        """
        # 获取当前场景
        scene = self.scene()

        # 如果按下Ctrl键，进行多选操作
        if event.modifiers() == Qt.ControlModifier:
            # 切换当前节点的选中状态
            self.setSelected(not self.isSelected())
            event.accept()
        else:

            # 清除场景中所有其他节点的选中状态
            if scene:
                for item in scene.items():
                    if item != self and isinstance(item, NodeItem):
                        item.setSelected(False)

            # 选中当前节点
            self.setSelected(True)

            # 调用父类方法处理移动等操作
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        处理节点的鼠标移动事件，支持缩放和移动操作。

        :param event: 鼠标事件
        """
        if event.modifiers() == Qt.AltModifier:
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        处理节点的鼠标释放事件，结束缩放操作。

        :param event: 鼠标事件
        """
        super().mouseReleaseEvent(event)

    def item_changed(self, change, value):
        """
        处理节点的属性变化事件，当节点移动或变换时更新连线。

        :param change: 属性变化类型
        :param value: 变化后的值
        :return: 变化后的值
        """
        if (change == QGraphicsItem.ItemPositionChange
            or change == QGraphicsItem.ItemTransformChange) and self.channelList:
            # self.position_changed.emit()  # 位置发生变化，发射信号
            for channel in self.channelList:
                # 调用通道的 update_position 方法更新连线位置
                channel.update_position()
        return value

    def contextMenuEvent(self, event):
        """
        处理节点的右键菜单事件，显示设置和删除菜单项。

        :param event: 鼠标事件
        """
        # 创建一个右键菜单
        menu = QMenu()

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

    # 在不同子类中分别重写该方法
    def show_node_widget(self):
        dialog = SetIpAndMask(self)
        result = dialog.exec()
        if result == QDialog.Accepted:
            self.on_node_updated()

    def delete_node(self):
        try:
            # 发射 delete_self 信号，通知其他对象节点已删除
            self.delete_self.emit(self)
        except Exception as e:
            print(f"Error in delete_channel: {e}")

    def find_channel_by_another_object(self, object_type, object_id):
        """
        根据对象类型和对象 ID 查找与该节点相连的通道。

        :param object_type: 对象的类型
        :param object_id: 对象的 ID
        :return: 找到的通道，如果未找到则返回 None
        """
        print("进入find_channel函数")
        for channel in self.channelList:
            # 获取通道的另一个端点
            item = channel.another_point_of_channel(self)
            if item == None:
                print("item为None，程序有误")
            else:
                condition1 = type(item) == object_type
                condition2 = item.index == object_id
                if condition1 and condition2:
                    return channel

    def find_interface_tuple_by_channel(self, node):
        """
        根据通道查找对应的接口元组。

        :param node: 通道连接的另一个节点
        :return: 找到的接口元组，如果未找到则返回 None
        """
        for interface_id_to_object in self.interface_id_to_object:
            if interface_id_to_object[1] == type(node) and interface_id_to_object[2] == node.index:
                return interface_id_to_object
            
    def clone(self):
        name = self.type_to_name(self.nodetype)
        # 创建新的节点实例
        new_node = self.__class__(name, self.index, self.icon_path, self.mainwindow)
        new_node.setPos(self.pos())
        # 复制其他属性
        new_node.ip = self.ip
        new_node.mask = self.mask
        return new_node

    def update_dicts(self):
        # Router类特有的函数
        pass

    def on_node_updated(self):
        QMessageBox.information(None,"提示",f"{self.name}设置成功")

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name