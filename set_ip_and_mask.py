from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel,
    QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
import re

class SetIpAndMask(QDialog):
    def __init__(self, node, parent=None):
        super().__init__(parent)
        self.node = node
        self.setWindowTitle(f"{node.name}-设置窗口")
        self.setup_ui()
        self.setMinimumSize(400, 200)

    def setup_ui(self):
        # 主布局
        main_layout = QVBoxLayout()

        # IP地址输入部分
        ip_layout = QHBoxLayout()
        ip_label = QLabel("IP地址:")
        self.ip_edit = QLineEdit()
        if hasattr(self.node, 'ip'):
            self.ip_edit.setText(self.node.ip)
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(self.ip_edit)

        # 子网掩码输入部分
        mask_layout = QHBoxLayout()
        mask_label = QLabel("子网掩码:")
        self.mask_edit = QLineEdit()
        if hasattr(self.node, 'mask'):
            self.mask_edit.setText(self.node.mask)
        mask_layout.addWidget(mask_label)
        mask_layout.addWidget(self.mask_edit)

        # 按钮部分
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.confirm_btn = QPushButton("确认")
        self.cancel_btn = QPushButton("取消")
        button_layout.addWidget(self.confirm_btn)
        button_layout.addWidget(self.cancel_btn)

        # 添加到主布局
        main_layout.addLayout(ip_layout)
        main_layout.addLayout(mask_layout)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # 连接信号
        self.cancel_btn.clicked.connect(self.reject)
        self.confirm_btn.clicked.connect(self.validate_and_accept)

    def validate_ip(self, ip_str):
        """验证IP地址格式"""
        pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        return re.match(pattern, ip_str) is not None

    def validate_mask(self, mask_str):
        """验证子网掩码格式"""
        # 先验证是否是标准IP格式
        if not self.validate_ip(mask_str):
            return False

        # 转换为二进制字符串验证是否连续1
        binary_str = ''
        for octet in mask_str.split('.'):
            binary_str += bin(int(octet))[2:].zfill(8)

        # 检查是否是连续的1后跟连续的0
        found_zero = False
        for bit in binary_str:
            if bit == '0':
                found_zero = True
            elif found_zero and bit == '1':
                return False
        return True

    def validate_and_accept(self):
        """验证输入并接受"""
        ip = self.ip_edit.text().strip()
        mask = self.mask_edit.text().strip()

        if not ip or not mask:
            QMessageBox.warning(self, "警告", "IP地址和子网掩码不能为空")
            return

        if not self.validate_ip(ip):
            QMessageBox.warning(self, "警告", "IP地址格式不正确")
            return

        if not self.validate_mask(mask):
            QMessageBox.warning(self, "警告", "子网掩码格式不正确")
            return

        # 设置节点属性
        self.node.ip = ip
        self.node.mask = mask

        self.accept()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    # 测试用的NodeItem类
    class NodeItem:
        def __init__(self):
            self.name = "测试节点"
            self.ip = "192.168.1.1"
            self.mask = "255.255.255.0"

    # 创建应用和测试节点
    app = QApplication(sys.argv)
    test_node = NodeItem()

    # 创建并显示窗口
    window = SetIpAndMask(test_node)
    if window.exec() == QDialog.Accepted:
        print(f"设置成功 - IP: {test_node.ip}, Mask: {test_node.mask}")
    else:
        print("用户取消了设置")

    sys.exit(app.exec())