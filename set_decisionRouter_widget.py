# 修改 set_decisionRouter_widget.py 文件
from PySide6.QtWidgets import (QWidget, QLineEdit, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QLabel, QSpacerItem, QSizePolicy, 
                             QComboBox, QTabWidget, QFrame, QFormLayout)
from PySide6.QtCore import Signal

class SetNodeConfigWidget(QWidget):
    node_updated = Signal()

    def __init__(self, node, parent=None):
        super().__init__(parent)
        self.node = node
        self.node_type = node.__class__.__name__
        
        self.setWindowTitle(f"算力调度节点属性配置")
        self.resize(600, 400)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        # 根据节点类型显示不同的配置界面
        self.create_config_layout()
        
        # 添加按钮布局
        self.create_button_layout()
        
        # 确保主布局设置到窗口
        self.setLayout(self.main_layout)

    def create_config_layout(self):
        # 创建配置区域
        config_frame = QFrame()
        config_frame.setFrameShape(QFrame.StyledPanel)
        config_layout = QVBoxLayout(config_frame)
        
        # 根据节点类型设置不同的配置界面
        if self.node_type in ["UserGateway", "ComputingGateway", "Router"]:
            # 这些节点类型需要根据接口数量动态生成IP配置
            self.create_interface_ip_layout(config_layout)
        elif self.node_type == "ComputeScheduleNode":
            # 决策路由器使用固定IP配置
            self.create_fixed_ip_layout(config_layout)
        else:
            # 默认配置界面
            default_label = QLabel("未定义的节点类型配置")
            config_layout.addWidget(default_label)
            print(f"警告: 未定义的节点类型 {self.node_type}")
        
        # 将配置框架添加到主布局
        self.main_layout.addWidget(config_frame)

    def create_interface_ip_layout(self, parent_layout):
        # 获取接口数量
        interface_count = self.node.interface_counter if hasattr(self.node, 'interface_counter') else 1
        
        # 创建标签页布局
        tab_widget = QTabWidget()
        
        # 为每个接口创建一个标签页
        self.ip_edits = []
        self.mask_edits = []
        
        for i in range(1, interface_count + 1):
            tab = QWidget()
            tab_layout = QFormLayout(tab)
            
            # IP地址输入框
            ip_label = QLabel("IP地址:")
            ip_edit = QLineEdit()
            if hasattr(self.node, 'ip_list') and len(self.node.ip_list) > i-1:
                ip_edit.setText(self.node.ip_list[i-1])
            else:
                ip_edit.setPlaceholderText(f"接口{i} IP地址")
            ip_edit.setToolTip("格式: xxx.xxx.xxx.xxx")
            
            # 子网掩码输入框
            mask_label = QLabel("子网掩码:")
            mask_edit = QLineEdit()
            if hasattr(self.node, 'mask_list') and len(self.node.mask_list) > i-1:
                mask_edit.setText(self.node.mask_list[i-1])
            else:
                mask_edit.setPlaceholderText(f"接口{i} 子网掩码")
            mask_edit.setToolTip("格式: xxx.xxx.xxx.xxx")
            
            tab_layout.addRow(ip_label, ip_edit)
            tab_layout.addRow(mask_label, mask_edit)
            
            tab_widget.addTab(tab, f"接口 {i}")
            
            self.ip_edits.append(ip_edit)
            self.mask_edits.append(mask_edit)
        
        # 将标签页添加到父布局
        parent_layout.addWidget(tab_widget)

    def create_fixed_ip_layout(self, parent_layout):
        # 固定IP配置布局
        form_layout = QFormLayout()
        
        # IP地址输入框
        ip_label = QLabel("IP地址:")
        self.ip_edit = QLineEdit()
        if hasattr(self.node, 'ip'):
            self.ip_edit.setText(self.node.ip)
        else:
            self.ip_edit.setPlaceholderText("例如: 192.168.1.1")
        self.ip_edit.setToolTip("格式: xxx.xxx.xxx.xxx")
        
        # 子网掩码输入框
        mask_label = QLabel("子网掩码:")
        self.mask_edit = QLineEdit()
        if hasattr(self.node, 'mask'):
            self.mask_edit.setText(self.node.mask)
        else:
            self.mask_edit.setPlaceholderText("例如: 255.255.255.0")
        self.mask_edit.setToolTip("格式: xxx.xxx.xxx.xxx")
        
        form_layout.addRow(ip_label, self.ip_edit)
        form_layout.addRow(mask_label, self.mask_edit)
        
        
        # 将表单布局添加到父布局
        parent_layout.addLayout(form_layout)

    def create_button_layout(self):
        # 创建按钮布局
        button_layout = QHBoxLayout()
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        submit_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        
        submit_button.setMinimumSize(100, 30)
        cancel_button.setMinimumSize(100, 30)
        
        submit_button.clicked.connect(self.submit)
        cancel_button.clicked.connect(self.close)
        
        button_layout.addWidget(submit_button)
        button_layout.addWidget(cancel_button)
        
        # 将按钮布局添加到主布局
        self.main_layout.addLayout(button_layout)

    def submit(self):
        # 根据节点类型保存不同的配置
        if self.node_type in ["UserGateway", "ComputingGateway", "Router"]:
            # 保存接口IP配置
            self.node.ip_list = [edit.text() for edit in self.ip_edits]
            self.node.mask_list = [edit.text() for edit in self.mask_edits]
            print(f"保存 {self.node_type} 接口配置: {self.node.ip_list}, {self.node.mask_list}")
        elif self.node_type == "ComputeScheduleNode":
            # 保存固定IP配置
            self.node.ip = self.ip_edit.text()
            self.node.mask = self.mask_edit.text()
            print(f"保存 ComputeScheduleNode 配置: {self.node.ip}, {self.node.mask}")
        else:
            print(f"警告: 未定义的节点类型 {self.node_type}，无法保存配置")
        
        # 发送更新信号并关闭窗口
        self.node_updated.emit()
        self.close()
