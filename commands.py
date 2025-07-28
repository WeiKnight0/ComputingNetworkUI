from PySide6.QtGui import QUndoCommand
from channel import Channel


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
                self.node_type, self.node_name, index, self.icon_path)

            view_center = self.window.ui.graphicsView.mapToScene(
                self.window.ui.graphicsView.viewport().rect().center())
            self.node.setPos(view_center.x() - self.node.boundingRect().width() / 2,
                             view_center.y() - self.node.boundingRect().height() / 2)

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
                    node.name = self.window.type_to_name(node.nodetype) + str(node.index + 1)
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
                node.name = self.window.type_to_name(node.nodetype) + str(node.index + 1)
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
                [start_item.interface_counter, type(end_item), end_item.index])
            end_item.interface_id_to_object.append(
                [end_item.interface_counter, type(start_item), start_item.index])

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
                [self.start_item.interface_counter, type(self.end_item), self.end_item.index])
            self.end_item.interface_id_to_object.append(
                [self.end_item.interface_counter, type(self.start_item), self.start_item.index])

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
            if interface[1] == type(self.end_item) and interface[2] == self.end_item.index:
                self.start_interface = interface
                break

        for interface in self.end_item.interface_id_to_object:
            if interface[1] == type(self.start_item) and interface[2] == self.start_item.index:
                self.end_interface = interface
                break

        # 从接口列表中移除
        if self.start_interface and self.start_interface in self.start_item.interface_id_to_object:
            self.start_item.interface_id_to_object.remove(self.start_interface)

        if self.end_interface and self.end_interface in self.end_item.interface_id_to_object:
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
        for node in self.clipboard['nodes']:
            new_node = node.clone()
            self.window.scene.addItem(new_node)
            self.window.nodes.append(new_node)
            self.new_nodes.append(new_node)

        # 克隆通道
        for channel in self.clipboard['channels']:
            start_item = next((n for n in self.new_nodes if n.name == channel.start_item.name), None)
            end_item = next((n for n in self.new_nodes if n.name == channel.end_item.name), None)
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
                if interface[1] == type(start_item) and interface[2] == start_item.index:
                    interface_end = interface
                    break

            self.deleted_channels.append({
                'channel': channel,
                'start_item': start_item,
                'end_item': end_item,
                'interface_start': interface_start,
                'interface_end': interface_end
            })

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
                'node': node,
                'node_type': node.nodetype,
                'index': node.index,
                'pos': node.pos(),
                'interface_id_to_object': [list(i) for i in node.interface_id_to_object],
                'interface_counter': node.interface_counter
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
            node = node_info['node']
            node_type = node_info['node_type']
            index = node_info['index']

            # 恢复节点到场景和列表
            self.window.scene.addItem(node)
            self.window.nodes.append(node)
            self.window.typeNumDict[node_type] += 1

            # 恢复接口信息
            node.interface_id_to_object = node_info['interface_id_to_object']
            node.interface_counter = node_info['interface_counter']

            # 恢复索引
            for existing_node in self.window.nodes:
                if existing_node.nodetype == node_type and existing_node.index >= index:
                    existing_node.index += 1

            node.index = index
            node.name = self.window.type_to_name(node_type) + str(node.index + 1)
            node.text_edit.setText(node.name)

        # 恢复链路
        for channel_info in reversed(self.deleted_channels):
            channel = channel_info['channel']
            start_item = channel_info['start_item']
            end_item = channel_info['end_item']
            interface_start = channel_info['interface_start']
            interface_end = channel_info['interface_end']

            # 恢复接口信息
            if interface_start and interface_start not in start_item.interface_id_to_object:
                start_item.interface_id_to_object.append(interface_start)
            if interface_end and interface_end not in end_item.interface_id_to_object:
                end_item.interface_id_to_object.append(interface_end)

            # 恢复链路到场景和列表
            self.window.scene.addItem(channel)
            self.window.channels.append(channel)
            start_item.channelList.append(channel)
            end_item.channelList.append(channel)