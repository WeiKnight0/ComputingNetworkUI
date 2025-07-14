import sys
import pickle
import base64
import traceback
import weakref
from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsView, 
                              QGraphicsScene, QGraphicsItem, QListWidget, 
                              QMenu, QGraphicsProxyWidget, QLineEdit, 
                              QGraphicsPixmapItem)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import (Qt, QPointF, QRectF, QLineF, QEvent, QObject,
                             Signal, QByteArray, QBuffer, QIODevice, 
                             SignalInstance)
from PySide6.QtGui import QPixmap, QPen, QColor, QTransform, QAction
from io import BytesIO


class NodeItem(QGraphicsItem, QObject):
    delete_self = Signal(object)

    # 记录 pickle.load 期间创建的实例
    #_pickle_instances = weakref.WeakSet()

    def __init__(self, name, nodetype, index, icon_path, firstCreate=True, parent=None):
        super().__init__(parent)
        QObject.__init__(self)  # 确保初始化 QObject

        self.name = name + str(index+1)
        self.nodetype = nodetype
        self.index = index
        self.interface_counter = 0
        self.interface_id_to_object = []
        print(f"创建的类型为：{self.nodetype}")
        print(f"self.index的值为:{self.index}")
        print(f"init时self.id为{id(self)}")
        print("firstCreated的值为：%s" %firstCreate)

        self.icon_path = icon_path
        self.icon = QPixmap(icon_path)
        self.channelList = []

        self.widget = 0

        if firstCreate == True:
            self.ip = '111.111.111.111'
            self.mask = '255.255.255.255'
            self.scale_factor = 1.0  # 初始缩放比例
        else:
            self.setTransform(QTransform().scale(self.scale_factor, self.scale_factor))

        # 创建 QGraphicsPixmapItem 来显示图标
        #self.icon_item = QGraphicsPixmapItem(self.icon, self)
        
        # 设置可移动和可选
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        self.itemChange = self.item_changed
        
        self.init_ui()
        
    def init_ui(self):
        # 添加可编辑的文本框（使用QGraphicsProxyWidget包装QLineEdit）
        self.proxy = QGraphicsProxyWidget(self)
        self.text_edit = QLineEdit(self.name)
        self.text_edit.setStyleSheet("""
            QLineEdit { 
                background: transparent; 
                border: 1px solid gray; 
                max-width: 75px;  /* 限制文本框宽度 */
            }
        """)
        self.text_edit.editingFinished.connect(self.update_name) # 将QLineEdit的内容与名称绑定

        self.proxy.setWidget(self.text_edit)
        self.proxy.setPos(0, self.icon.height() + 5)  # 文本框在图标下方
    
    def getNodeType(self, nodeName):
        typeDict = {"用户节点": "UserNode", 
                    "算力节点": "ComputingNode", 
                    "用户网关": "UserRouter", 
                    "算力网关": "computingRouter", 
                    "调度决策网关": "DecisionRouter", 
                    "路由器": "Router"}
        return typeDict.get(nodeName, None)
    
    def __getstate__(self):
        state = {}

        for key, value in self.__dict__.items():
            print(f"属性为:{key}")
            #value = getattr(self, attr, None)
            if isinstance(value, QObject) or isinstance(value, SignalInstance):
                print(f"🚨 移除不可序列化的 QObject: {key}")
                continue
            
            elif isinstance(value, QPixmap):
                print(f"🖼️ 处理 QPixmap: {key}")
                continue  

            print("value语句赋值正确")
            state[key] = value
            print("state语句执行正确")

        state["x"] = self.scenePos().x()
        state["y"] = self.scenePos().y()
        state["channelList"] = []
        del state["__METAOBJECT__"]

        print("for循环正确执行")

        return state


    def __setstate__(self, state):
        print(f"进入 __setstate__，此时id为{id(self)}，类型为{type(self)}")
        traceback.print_stack()  # 打印调用栈
        for key, value in state.items():
            if key in ("delete_self", "destroyed"):
                print(f"⚠️ 跳过类属性 {key}")
                #setattr(self, key, getattr(self.__class__, key, None))  # 从类属性恢复
                continue

            elif isinstance(value, str) and value.startswith("/9j/"):  # 处理 QPixmap
                print(f"🖼️ 恢复 QPixmap: {key}")
                image_data = base64.b64decode(value)
                byte_array = QByteArray(image_data)
                pixmap = QPixmap()
                pixmap.loadFromData(byte_array, "PNG")
                self.__dict__[key] = pixmap
                continue

            else:
                self.__dict__[key] = value

        print(f"完成赋值时id为{id(self)}")
        name = self.type_to_name(self.nodetype)
        self.__init__(name, self.index, self.icon_path, firstCreate=False)
    
    def type_to_name(self, nodetype):
        nameDict = {"UserNode": "用户节点", 
                    "ComputingNode": "算力节点", 
                    "UserRouter": "用户网关", 
                    "computingRouter": "算力网关", 
                    "DecisionRouter": "调度决策网关", 
                    "Router": "路由器"}
        return nameDict.get(nodetype, None)

    def boundingRect(self):
        # 计算包含图标和文本框的总区域
        return QRectF(0, 0, 
                     max(self.icon.width(), self.text_edit.width()),
                     self.icon.height() + self.text_edit.height() + 5)
    
    def paint(self, painter, option, widget):
        painter.drawPixmap(0, 0, self.icon)
        
    def mouseDoubleClickEvent(self, event):
        # 双击时聚焦到文本框
        self.text_edit.setFocus()
        
    def update_name(self):
        self.name = self.text_edit.text()
    
    def mouseMoveEvent(self, event):
        # 按住 Alt 键时禁用拖拽和缩放
        if event.modifiers() == Qt.AltModifier:
            #print("按住Alt键后被触发")
            return  # 直接返回，不执行任何操作
        
        #print("mouseMoveEvent拖拽大小启动")
        # 按住 Ctrl 拖拽调整大小
        if event.modifiers() == Qt.ControlModifier:
            delta = event.pos() - event.lastPos()
            self.scale_factor += delta.x() * 0.01  # 根据鼠标移动调整缩放比例
            self.setTransform(QTransform().scale(self.scale_factor, self.scale_factor))
        else:
            # 直接拖拽改变位置
            super().mouseMoveEvent(event)
    
    
    def item_changed(self, change, value):
        #print(f"进入item_changed函数,change = {change}")
        # 当节点移动时更新连线
        #print("进入item_changed")
        #print(f"self的id为：{id(self)}")
        #print(f"self.channelList的值：{self.channelList}")
        if (change == QGraphicsItem.ItemPositionChange
             or change == QGraphicsItem.ItemTransformChange) and self.channelList:
            #self.position_changed.emit()  # 位置发生变化，发射信号
            for channel in self.channelList:
                channel.update_position()
        return value
        
    def contextMenuEvent(self, event):
        # 右键菜单
        menu = QMenu()
        
        # "设置"菜单项
        set_node_action = QAction("设置", self.scene())
        set_node_action.triggered.connect(self.show_node_widget)
        menu.addAction(set_node_action)

        # "删除"菜单项
        delete_action = QAction("删除", self.scene())
        delete_action.triggered.connect(self.delete_node)
        menu.addAction(delete_action)

        # 显示菜单
        menu.exec_(event.screenPos())

    # 在不同子类中分别重写该方法
    def show_node_widget(self):
        return

    def delete_node(self):
        # 删除当前节点对象（根据需求删除）
        scene = self.scene()
        if scene:
            scene.removeItem(self)
        print("删除节点")

        for channel in self.channelList[::-1]:
            channel.delete_channel()

        try:
            self.delete_self.emit(self)
        except Exception as e:
            print(f"Error in delete_channel: {e}")
        
        del self
    
    def find_channel_by_another_object(self, object_type, object_id):
        print("进入find_channel函数")
        for channel in self.channelList:
            item = channel.another_point_of_channel(self)
            if item == None:
                print("item为None，程序有误")
            else:
                condition1 = type(item) == object_type
                condition2 = item.index == object_id
                if condition1 and condition2:
                    return channel
    
    def find_interface_tuple_by_channel(self, node):
        for interface_id_to_object in self.interface_id_to_object:
            if interface_id_to_object[1] == type(node) and interface_id_to_object[2] == node.index:
                return interface_id_to_object