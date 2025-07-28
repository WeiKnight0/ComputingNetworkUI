from PySide6.QtWidgets import QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Signal
from set_task_widget import SetTaskWidget

class SetUserNodeWidget(QWidget):
    # 定义一个信号，用于在原来的类中验证更新
    node_updated = Signal()

    def __init__(self, user_node, parent=None):
        super().__init__(parent)
        self.user_node = user_node  
        self.task_widget = None  
                
        # 加载UI文件
        loader = QUiLoader()
        self.ui = loader.load('set_userNode.ui')  # 加载UI界面

        if not self.ui:
            print("UI 加载失败，请检查文件路径或格式")

        # 获取UI控件
        self.ip_line_edit = self.ui.findChild(QLineEdit, 'ip_lineEdit')  # 获取IP输入框
        self.mask_line_edit = self.ui.findChild(QLineEdit, 'mask_lineEdit')  # 获取子网掩码输入框
        self.task_highest_line_edit = self.ui.findChild(QLineEdit, 'highest_limit_lineEdit')  # 获取任务上限输入框
        self.task_lowest_line_edit = self.ui.findChild(QLineEdit, 'lowest_limit_lineEdit')  # 获取任务下限输入框
        
        self.confirm_button = self.ui.findChild(QPushButton, 'confirmButton')
        self.cancel_button = self.ui.findChild(QPushButton, 'cancelButton')
        self.task_setting_button = self.ui.findChild(QPushButton, 'task_queueButton')

        # 设置当前的值
        self.ip_line_edit.setText(user_node.ip)
        self.mask_line_edit.setText(user_node.mask)
        self.task_highest_line_edit.setText(str(user_node.task_highest_limit))
        self.task_lowest_line_edit.setText(str(user_node.task_lowest_limit))
        
        # 连接信号和槽
        self.confirm_button.clicked.connect(lambda:self.accept_update(user_node))
        self.cancel_button.clicked.connect(self.reject_update)
        self.task_setting_button.clicked.connect(self.open_task_setting_window)


    # 设置自动配置IP框的选中
    def update_ip_mask_fields(self):
        # 如果选中了自动配置IP，则禁用IP和子网掩码输入框
        if self.radio_button.isChecked():
            self.ip_line_edit.setDisabled(True)
            self.mask_line_edit.setDisabled(True)
        else:
            self.ip_line_edit.setEnabled(True)
            self.mask_line_edit.setEnabled(True)

    def accept_update(self, user_node):
        # 获取输入框的值并更新UserNode的属性
        user_node.ip = self.ip_line_edit.text()
        user_node.mask = self.mask_line_edit.text()
        user_node.task_highest_limit = float(self.task_highest_line_edit.text())
        user_node.task_lowest_limit = float(self.task_lowest_line_edit.text())

        print(f"更新成功: IP={user_node.ip}, Mask={user_node.mask}, "
              f"Task High Limit={user_node.task_highest_limit}, Task Low Limit={user_node.task_lowest_limit}")
        
        # 发射信号，通知主界面已更新
        self.node_updated.emit()

        # 关闭当前窗口
        self.ui.close()

    def reject_update(self):
        # 取消操作
        print("取消设置")
        self.ui.close()

    def open_task_setting_window(self):
        if not self.task_widget or not self.task_widget.isVisible():
            self.task_widget = SetTaskWidget(self.user_node)
            self.task_widget.show()
            self.task_widget.task_updated.connect(self.on_task_updated)

    def on_task_updated(self):
        print("任务队列已更新")