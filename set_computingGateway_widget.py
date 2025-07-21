from PySide6.QtWidgets import QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Signal

class SetComputingGatewayWidget(QWidget):
    # 定义一个信号，用于传递更新后的带宽值
    node_updated = Signal()

    def __init__(self, computing_gateway, parent=None):
        super().__init__(parent)
        
        # 保存传递进来的computingNode实例
        self.computing_gateway = computing_gateway
        
        # 加载UI文件
        loader = QUiLoader()
        self.ui = loader.load('set_computingGateway.ui')  # 加载UI界面

        if not self.ui:
            print("UI 加载失败，请检查文件路径或格式")

        # 获取UI控件
        self.ip_line_edit_1 = self.ui.findChild(QLineEdit, 'ip_lineEdit_1')  # 获取IP输入框
        self.mask_line_edit_1 = self.ui.findChild(QLineEdit, 'mask_lineEdit_1')  # 获取子网掩码输入框

        self.ip_line_edit_2 = self.ui.findChild(QLineEdit, 'ip_lineEdit_2')  # 获取IP输入框
        self.mask_line_edit_2 = self.ui.findChild(QLineEdit, 'mask_lineEdit_2')  # 获取子网掩码输入框
        
        self.confirm_button = self.ui.findChild(QPushButton, 'confirmButton')
        self.cancel_button = self.ui.findChild(QPushButton, 'cancelButton')

        # 设置当前的值
        self.ip_line_edit_1.setText(self.computing_gateway.ip)
        self.mask_line_edit_1.setText(self.computing_gateway.mask)

        self.ip_line_edit_2.setText(self.computing_gateway.ip_2)
        self.mask_line_edit_2.setText(self.computing_gateway.mask_2)


        # 连接信号和槽
        self.confirm_button.clicked.connect(self.accept_update)
        self.cancel_button.clicked.connect(self.reject_update)

    def accept_update(self):
        # 获取输入框的值并更新computingNode的属性
        self.computing_gateway.ip = self.ip_line_edit_1.text()
        self.computing_gateway.mask = self.mask_line_edit_1.text()

        self.computing_gateway.ip_2 = self.ip_line_edit_2.text()
        self.computing_gateway.mask_2 = self.mask_line_edit_2.text()

        print(f"更新成功: IP={self.computing_gateway.ip}, Mask={self.computing_gateway.mask}")
        
        # 发射信号，通知主界面已更新
        self.node_updated.emit()

        # 关闭当前窗口
        self.ui.close()

    def reject_update(self):
        # 取消操作
        print("取消设置")
        self.ui.close()
