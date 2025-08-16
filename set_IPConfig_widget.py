from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QApplication, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Signal
import sys


class IPConfigWidget(QWidget):
    node_updated = Signal()

    def __init__(self, node=None, parent=None):
        super().__init__(parent)
        self.node = node
        self.ip_fields = []
        self.mask_fields = []

        # 设置窗口标题（根据节点类型动态生成）
        self.set_window_title()

        # 创建主布局
        self.layout = QVBoxLayout(self)

        # 设置整体边距：左、上、右、下
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(15)  # 每一行之间垂直间距

        # 动态添加每行控件（根据channelList中的连接）
        if node is not None:
            for channel in node.channelList:
                # 获取连接的节点
                item = channel.another_point_of_channel(node)
                node_name = item.name
                # 获取该节点的IP和掩码
                ip = node.ip_dict.get(item, "")
                mask = node.mask_dict.get(item, "")

                # 创建水平布局和控件
                h_layout = QHBoxLayout()
                h_layout.setSpacing(20)  # 每一列控件之间的间距

                # 节点名称标签
                label_node = QLabel(f"节点: {node_name}")
                label_node.setMinimumWidth(100)  # 固定宽度避免跳动

                # IP地址输入框
                label_ip = QLabel("IP:")
                ip_edit = QLineEdit()
                ip_edit.setText(ip if ip else "")
                ip_edit.setPlaceholderText("例如：192.168.1.1")

                # 子网掩码输入框
                label_mask = QLabel("子网掩码:")
                mask_edit = QLineEdit()
                mask_edit.setText(mask if mask else "")
                mask_edit.setPlaceholderText("例如：255.255.255.0")

                # 将控件添加到水平布局
                h_layout.addWidget(label_node)
                h_layout.addWidget(label_ip)
                h_layout.addWidget(ip_edit)
                h_layout.addWidget(label_mask)
                h_layout.addWidget(mask_edit)

                # 将水平布局添加到主布局
                self.layout.addLayout(h_layout)

                self.ip_fields.append((item, ip_edit)) 
                self.mask_fields.append((item, mask_edit))

        # 如果没有连接，显示提示
        if node is None or not node.channelList:
            self.layout.addWidget(QLabel("没有连接的设备"))

        # 添加一个弹簧，使按钮保持在底部
        self.layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # 底部按钮栏
        button_layout = QHBoxLayout()
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        submit_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        submit_button.clicked.connect(self.on_submit)
        cancel_button.clicked.connect(self.close)

        button_layout.addWidget(submit_button)
        button_layout.addWidget(cancel_button)

        self.layout.addLayout(button_layout)

    def set_window_title(self):
        """根据节点类型设置窗口标题"""
        # 节点类型到显示名称的映射
        node_type_map = {
            "UserGateway": "用户网关",
            "ComputingGateway": "算力网关",
            "Router": "路由节点",
            # 可以根据需要添加更多节点类型
        }

        # 默认标题
        default_title = "IP地址配置"

        if self.node is None:
            self.setWindowTitle(default_title)
            return

        # 获取节点类型（优先使用nodetype属性，其次使用类名）
        node_type = getattr(self.node, 'nodetype', self.node.__class__.__name__)
        
        # 获取显示名称
        display_name = node_type_map.get(node_type, node_type)
        
        # 设置最终窗口标题
        self.setWindowTitle(f"{display_name}属性配置")

    def on_submit(self):
        if self.node is None:
            self.close()
            return

        # 更新节点的IP和掩码信息
        for (item, ip_edit), (_, mask_edit) in zip(self.ip_fields, self.mask_fields):
            ip = ip_edit.text()
            mask = mask_edit.text()

            # 更新节点的字典
            self.node.ip_dict[item] = ip
            self.node.mask_dict[item] = mask

        self.node_updated.emit()
        self.close()