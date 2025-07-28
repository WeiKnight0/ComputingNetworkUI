import weakref
from PySide6.QtWidgets import QGraphicsLineItem, QMenu, QGraphicsItem, QGraphicsSimpleTextItem
from PySide6.QtCore import QLineF, QPointF, QObject
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

class Channel(QGraphicsLineItem, QObject):
    delete_self = Signal(object)  # 发送被删除的对象自身

    def __init__(self, start_item:NodeItem, end_item:NodeItem, channelInfo=None, parent=None):
        super().__init__(parent)
        QObject.__init__(self)  # 确保初始化 QObject
        self.start_item = start_item
        self.end_item = end_item
        if not channelInfo:
            self.bandwidth = 100.0  # 默认带宽
            self.banddelay = 10.0  # 默认时延
            self.start_interface_index = start_item.interface_counter
            self.end_interface_index = end_item.interface_counter
        else:
            for key, value in channelInfo.__dict__.items():
                if key in ("start_type", "start_index", "end_type", "end_index"):
                    continue
                else:
                    setattr(self, key, value)
        
        self.widget = 0
        
        # 设置连线样式
        self.setPen(QPen(QColor(0, 0, 0), 2))

        # ✅ 创建显示接口编号的文本项
        self.start_text = QGraphicsSimpleTextItem(str(self.start_interface_index), self)
        self.end_text = QGraphicsSimpleTextItem(str(self.end_interface_index), self)
        
        # 更新连线位置
        self.update_position()
                
    def update_position(self):
        # 根据节点位置更新连线
        start_pos = self.start_item.scenePos() + QPointF(self.start_item.icon.width()/2 * self.start_item.scale_factor,
                                                        self.start_item.icon.height()/2 * self.start_item.scale_factor)
        end_pos = self.end_item.scenePos()+ QPointF(self.end_item.icon.width()/2 * self.end_item.scale_factor,
                                                        self.end_item.icon.height()/2 * self.end_item.scale_factor)
        self.setLine(QLineF(start_pos, end_pos))

            # ✅ 将文字放在线段上的位置，并稍微偏移
        def point_along_line(start, end, ratio):
            return start + (end - start) * ratio

        
        start_text_pos = point_along_line(start_pos, end_pos, 0.2) + QPointF(0, -10)
        end_text_pos = point_along_line(end_pos, start_pos, 0.2) + QPointF(0, -10)

        # ✅ 设置文本位置（偏移一点避免遮挡）
        self.start_text.setPos(start_text_pos)
        self.end_text.setPos(end_text_pos)


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
        menu.exec_(event.screenPos())

    def show_channel_widget(self):
        # 创建并显示带宽设置对话框
        self.widget = SetChannelWidget(None, self.bandwidth, self.banddelay, self)
        self.widget.ui.show()        
        
        # 将信号与更新带宽方法连接
        self.widget.channel_set.connect(self.update_channel)
        
    def delete_channel(self):
        self.start_item.interface_counter -= 1
        self.end_item.interface_counter -= 1

        print(f"start_item为{self.start_item.name},counter为{self.start_item.interface_counter}")
        print(f"end_item为{self.end_item.name}, counter为{self.end_item.interface_counter}")

        for interface_id_and_object in self.start_item.interface_id_to_object[::-1]:
            if interface_id_and_object[1] == type(self.end_item) and interface_id_and_object[2] == self.end_item.index:
                self.start_item.interface_id_to_object.remove(interface_id_and_object)

            if interface_id_and_object[0] > self.start_interface_index:
                interface_id_and_object[0] -= 1
                print(f"start_item为{self.start_item.name}")
                print(f"对面对象的type为{interface_id_and_object[1]},index为{interface_id_and_object[2]}")
                channel = self.start_item.find_channel_by_another_object\
                    (interface_id_and_object[1], interface_id_and_object[2])
                if channel.start_item == self.start_item:
                    channel.start_text.setText(str(interface_id_and_object[0]))
                else:
                    channel.end_text.setText(str(interface_id_and_object[0]))
            
            
        
        for interface_id_and_object in self.end_item.interface_id_to_object[::-1]:
            if interface_id_and_object[1] == type(self.start_item) and interface_id_and_object[2] == self.start_item.index:
                self.end_item.interface_id_to_object.remove(interface_id_and_object)

            if interface_id_and_object[0] > self.end_interface_index:
                interface_id_and_object[0] -= 1
                print(f"end_item为{self.end_item.name}")
                print(f"对面对象的type为{interface_id_and_object[1]},index为{interface_id_and_object[2]}")
                channel = self.end_item.find_channel_by_another_object\
                    (interface_id_and_object[1], interface_id_and_object[2])
                if channel.start_item == self.end_item:
                    channel.start_text.setText(str(interface_id_and_object[0]))
                else:
                    channel.end_text.setText(str(interface_id_and_object[0]))

        # 删除当前通道对象（根据需求删除）
        self.start_item.channelList.remove(self)
        self.end_item.channelList.remove(self)
        print(f"start为{self.start_item.name}, 列表为{self.start_item.channelList}")
        print(f"end为{self.end_item.name},列表为{self.end_item.channelList}")

        for channel in self.start_item.channelList:
            if channel.start_item == self.start_item and channel.start_interface_index > self.start_interface_index:
                channel.start_interface_index -= 1
            elif channel.end_item == self.start_item and channel.end_interface_index > self.start_interface_index:
                channel.end_interface_index -= 1
        
        for channel in self.end_item.channelList:
            if channel.start_item == self.end_item and channel.start_interface_index > self.end_interface_index:
                channel.start_interface_index -= 1
            elif channel.end_item == self.end_item and channel.end_interface_index > self.end_interface_index:
                channel.end_interface_index -= 1
        
        try:
            self.delete_self.emit(self)
        except Exception as e:
            print(f"Error in delete_channel: {e}")

        scene = self.scene()
        if scene:
            scene.removeItem(self)
        print("删除通道")
        del self

    def update_channel(self, new_bandwidth, new_banddelay):
        if new_bandwidth >= 0 and new_banddelay >= 0:
            self.bandwidth = new_bandwidth
            self.banddelay = new_banddelay
            print(f"通道带宽更新为: {self.bandwidth} Mbps，时延更新为: {self.banddelay} ms")
        else:
            print("更新失败")
        
        self.widget.ui.close()
        widget = self.widget
        print(f"self.widget的地址为：{id(self.widget)}")
        print(f"widget的地址为{id(widget)}")
        self.widget = 0
        del widget
    
    def another_point_of_channel(self, item):
        if item == self.start_item:
            return self.end_item
        elif item == self.end_item:
            return self.start_item
        else:
            return None