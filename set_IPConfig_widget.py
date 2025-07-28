from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QApplication, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Signal
import sys

class IPConfigWidget(QWidget):
    # 定义一个信号，用于在原来的类中验证更新
    node_updated = Signal()

    def __init__(self, router=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("配置IP地址")
        self.connected_ports = router.interface_counter if router != None else 3

        self.ip_fields = []
        self.mask_fields = []

        self.router = router

        self.layout = QVBoxLayout(self)

        # 设置整体边距：左、上、右、下
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(15)  # 每一行之间垂直间距

        # 动态添加每行控件（仅限 connected_ports 数量）
        for i in range(1, self.connected_ports + 1):
            h_layout = QHBoxLayout()
            h_layout.setSpacing(20)  # 每一列控件之间的间距

            label_ip = QLabel(f"接口{i} IP:")
            ip_edit = QLineEdit()
            if len(router.ip_list) >= i:
                ip_text = router.ip_list[i-1]
            else:
                ip_text = "192.168.1." + str(i)
            ip_edit.setText(ip_text)
            ip_edit.setPlaceholderText("例如：192.168.1.1")

            label_mask = QLabel("子网掩码:")
            mask_edit = QLineEdit()
            if len(router.mask_list) >= i:
                mask_text = router.mask_list[i-1]
            else:
                mask_text = "255.255.255.0"
            mask_edit.setText(mask_text)
            mask_edit.setPlaceholderText("例如：255.255.255.0")

            h_layout.addWidget(label_ip)
            h_layout.addWidget(ip_edit)
            h_layout.addWidget(label_mask)
            h_layout.addWidget(mask_edit)

            self.layout.addLayout(h_layout)

            self.ip_fields.append(ip_edit)
            self.mask_fields.append(mask_edit)

        # 底部按钮栏
        button_layout = QHBoxLayout()
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        submit_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        submit_button.clicked.connect(lambda:self.submit(router))
        cancel_button.clicked.connect(self.close)

        button_layout.addWidget(submit_button)
        button_layout.addWidget(cancel_button)

        self.layout.addLayout(button_layout)

    def submit(self, router):
        print("✅ 提交IP配置：")
        for i in range(self.connected_ports):
            ip = self.ip_fields[i].text()
            mask = self.mask_fields[i].text()
            print(f"接口{i+1}: IP = {ip}, Mask = {mask}")
            if len(self.router.ip_list) < i+1:
                router.ip_list.append(ip)
                router.mask_list.append(mask)
            else:
                router.ip_list[i] = ip
                router.mask_list[i] = mask

        self.node_updated.emit()
        self.close()
        del self

# 测试运行
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = IPConfigWidget()
    win.show()
    sys.exit(app.exec_())
