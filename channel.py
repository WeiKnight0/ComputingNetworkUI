import weakref
from PySide6.QtWidgets import QGraphicsLineItem, QMenu, QGraphicsItem, QGraphicsSimpleTextItem
from PySide6.QtCore import Qt, QLineF, QPointF, QObject
from PySide6.QtGui import QPen, QColor, QAction
from PySide6 import QtWidgets
from PySide6.QtCore import Signal, Slot
from nodeItem import NodeItem
from set_channel_widget import SetChannelWidget

class ChannelInfo:
    def __init__(self, channel):
        self.start_type = channel.start_item.nodetype
        self.start_index = channel.start_item.index
        self.end_type = channel.end_item.nodetype
        self.end_index = channel.end_item.index
        self.bandwidth = channel.bandwidth 
        self.banddelay = channel.banddelay
        self.start_interface_index = channel.start_interface_index
        self.end_interface_index = channel.end_interface_index
        self.pen_dict = self._pen_to_dict(channel.pen())

    def _pen_to_dict(self, pen: QPen) -> dict:
        return {
            "color": pen.color().name(),  # 颜色转为十六进制字符串（如 "#FF0000"）
            "width": pen.width(),  # 线宽（整数）
            "style": pen.style().value,  # 关键修改：获取枚举的整数值
            "cap_style": pen.capStyle().value,
            "join_style": pen.joinStyle().value
        }

    def get_pen(self) -> QPen:
        pen_dict = self.pen_dict
        pen = QPen()
        pen.setColor(QColor(pen_dict["color"]))  # 从字符串恢复颜色
        pen.setWidth(pen_dict["width"])
        pen.setStyle(Qt.PenStyle(pen_dict["style"]))  # 恢复线型
        pen.setCapStyle(Qt.PenCapStyle(pen_dict["cap_style"]))
        pen.setJoinStyle(Qt.PenJoinStyle(pen_dict["join_style"]))
        return pen

class Channel(QGraphicsLineItem, QObject):
    delete_self = Signal(object)  # 发送被删除的对象自身

    def __init__(self, start_item, end_item, pen=None, channelInfo=None, parent=None):
        super().__init__(parent)
        QObject.__init__(self)  # 确保初始化 QObject
        self.start_item = start_item
        self.end_item = end_item
        if not channelInfo:
            self.bandwidth = 100.0  # 默认带宽
            self.banddelay = 10.0  # 默认时延
            self.start_interface_index = start_item.interface_counter
            self.end_interface_index = end_item.interface_counter
        elif isinstance(channelInfo, ChannelInfo):
            for key, value in channelInfo.__dict__.items():
                if key in ("start_type", "start_index", "end_type", "end_index"):
                    continue
                else:
                    setattr(self, key, value)
        
        self.widget = 0
        self.original_pen = None  # 存储原始笔样式
        # 设置连线样式
        if pen is not None:
            self.setPen(pen)
        else:
            self.setPen(QPen(QColor(70, 130, 180), 2, Qt.SolidLine, Qt.RoundCap))

        self.setZValue(10)  # 确保连线在节点下方
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)  # 抗锯齿

        # 更新连线位置
        self.update_position()
                
    def update_position(self):
        """更新连线位置，使用更精确的连接点计算"""
        line = QLineF(self.start_item.scenePos(), self.end_item.scenePos())
        start_point = self.calculate_connection_point(self.start_item)
        end_point = self.calculate_connection_point(self.end_item)
        self.setLine(QLineF(start_point, end_point))

    def calculate_connection_point(self, node):
        """计算节点与目标点的连接点"""
        node_rect = node.boundingRect()
        node_pos = node.scenePos()
        center = node_pos + QPointF(node_rect.width() / 2, node_rect.height() / 2)
        return center

    def itemChaFnge(self, change, value):
        # 当选中状态改变时
        if change == QGraphicsItem.ItemSelectedChange:
            if value:  # 被选中
                self.original_pen = self.pen()  # 保存原始笔样式
                self.setPen(QPen(Qt.red, self.original_pen.width(), self.original_pen.style()))
            else:  # 取消选中
                if self.original_pen:
                    self.setPen(self.original_pen)
        return super().itemChange(change, value)

    def __getstate__(self):
        return {
            "bandwidth": self.bandwidth,
            "banddelay": self.banddelay,
            "start_name": self.start_item.name if self.start_item else None,
            "end_name": self.end_item.name if self.end_item else None,
            "start_interface_index": self.start_interface_index if self.start_interface_index != 0 else None,
            "end_interface_index": self.end_interface_index if self.end_interface_index != 0 else None
        }

    def __setstate__(self, state):
        for key, value in state.items():
                if key in ("start_name", "end_name"):
                    continue
                else:
                    self.__dict__[key] = value

    def item_changed(self, change, value):
        #print(f"进入item_changed函数,change = {change}")
        # 当节点移动时更新连线
        if change == QGraphicsItem.ItemPositionChange or change == QGraphicsItem.ItemTransformChange:
            self.update_position()
        return value

            
    def contextMenuEvent(self, event):
        if not self.isSelected():
            self.original_pen = self.pen()
            self.setPen(QPen(Qt.red, self.original_pen.width(), self.original_pen.style()))
        # 右键菜单
        menu = QMenu()
        
        # "设置"菜单项
        update_channel_action = QAction("设置", self.scene())
        update_channel_action.triggered.connect(self.show_channel_widget)
        menu.addAction(update_channel_action)

        # "删除"菜单项
        delete_action = QAction("删除", self.scene())
        delete_action.triggered.connect(self.delete_channel)
        menu.addAction(delete_action)

        # 显示菜单
        menu.exec(event.screenPos())

        # 恢复原始笔样式（如果不是通过选中状态改变的）
        if not self.isSelected() and self.original_pen:
            self.setPen(self.original_pen)

    def show_channel_widget(self):
        # 创建并显示带宽设置对话框
        self.widget = SetChannelWidget(None, self.bandwidth, self.banddelay, self)
        self.widget.ui.show()        
        
        # 将信号与更新带宽方法连接
        self.widget.channel_set.connect(self.update_channel)
        
    def delete_channel(self):
        try:
            self.delete_self.emit(self)
        except Exception as e:
            print(f"Error in delete_channel: {e}")


    def update_channel(self, new_bandwidth, new_banddelay):
        if new_bandwidth >= 0 and new_banddelay >= 0:
            self.bandwidth = new_bandwidth
            self.banddelay = new_banddelay
            print(f"通道带宽更新为: {self.bandwidth} Mbps，时延更新为: {self.banddelay} ms")
        else:
            print("更新失败")
        
        self.widget.ui.close()
        widget = self.widget
        # print(f"self.widget的地址为：{id(self.widget)}")
        # print(f"widget的地址为{id(widget)}")
        self.widget = 0
        del widget
    
    def another_point_of_channel(self, item):
        if item == self.start_item:
            return self.end_item
        elif item == self.end_item:
            return self.start_item
        else:
            return None

    def __str__(self):
        return f"{self.start_item}<-d={self.banddelay},w={self.bandwidth}->{self.end_item}"

    def __repr__(self):
        return str(self)