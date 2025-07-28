from PySide6.QtWidgets import QDialog, QLineEdit, QPushButton
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from PySide6.QtCore import Signal

class SetChannelWidget(QDialog):
    # 自定义信号，用于返回更新后的带宽
    channel_set = Signal(float, float)

    def __init__(self, parent=None, current_bandwidth=None, current_banddelay=None, channel=None):
        super().__init__(parent)

        # 加载UI文件
        print("加载UI")
        loader = QUiLoader()
        self.ui = loader.load('set_channel.ui')

        print("UI Loaded:", self.ui)
        if not self.ui:
            print("UI 加载失败，请检查文件路径或格式")

        # 获取UI控件
        self.bandwidthLineEdit = self.ui.findChild(QLineEdit, 'bandwidthLine')
        self.banddelayLineEdit = self.ui.findChild(QLineEdit, 'banddelayLine')
        self.confirmButton = self.ui.findChild(QPushButton, 'confirmButton')
        self.cancelButton = self.ui.findChild(QPushButton, 'cancelButton')
        
        # 设置当前带宽（如果有的话）
        if current_bandwidth is not None:
            self.bandwidthLineEdit.setText(str(current_bandwidth))

        if current_banddelay is not None:
            self.banddelayLineEdit.setText(str(current_banddelay))

        self.channel = channel

        # 连接按钮事件
        self.confirmButton.clicked.connect(self.accept_update)
        self.cancelButton.clicked.connect(self.reject_update)

    def accept_update(self):
        # 获取带宽的输入值
        bandwidth = self.bandwidthLineEdit.text().strip()
        banddelay = self.banddelayLineEdit.text().strip()

        def is_valid_number(s):
            try:
                float(s)
                return True
            except ValueError:
                return False

        if is_valid_number(bandwidth) and is_valid_number(banddelay):
            self.bandwidth = float(bandwidth)
            self.banddelay = float(banddelay)
            print(f"带宽设置为: {self.bandwidth} Mbps, 时延设置为：{self.banddelay} ms")
            self.channel.bandwidth = self.bandwidth
            self.channel.banddelay = self.banddelay
            self.channel_set.emit(self.bandwidth, self.banddelay)
            self.accept()
        else:
            print("请输入有效值！")

    def reject_update(self):
        # 取消操作
        print("取消带宽设置")
        self.bandwidth = -1
        self.banddelay = -1
        self.channel_set.emit(self.bandwidth, self.banddelay)
        self.reject()
