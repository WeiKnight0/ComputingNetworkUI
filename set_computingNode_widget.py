from PySide6.QtWidgets import QWidget, QLineEdit, QComboBox, QPushButton, QMessageBox
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Signal

class SetComputingNodeWidget(QWidget):
    # 定义一个信号，用于通知节点已更新
    node_updated = Signal()

    def __init__(self, computing_node, parent=None):
        super().__init__(parent)
        self.computing_node = computing_node
        
        # 加载UI文件
        loader = QUiLoader()
        self.ui = loader.load('set_computingNode.ui')
        self.ui.setWindowTitle(f"{computing_node.name}属性配置")
        
        # 检查UI加载状态
        if not self.ui:
            QMessageBox.critical(self, "错误", "UI文件加载失败，请检查文件路径和格式")
            return

        # 获取UI控件
        self.ip_line_edit = self.find_widget(QLineEdit, 'ipLineEdit')  
        self.mask_line_edit = self.find_widget(QLineEdit, 'maskLineEdit')  
        self.computing_type_comboBox = self.find_widget(QComboBox, 'computingTypeComboBox') 
        self.computing_power_line_edit = self.find_widget(QLineEdit, 'computingPowerLineEdit')  
        self.storage_space_line_edit = self.find_widget(QLineEdit, 'storageSpaceLineEdit')  
        self.switching_capacitance_line_edit = self.find_widget(QLineEdit, 'switchingCapacitanceLineEdit')  
        self.static_power_line_edit = self.find_widget(QLineEdit, 'staticPowerLineEdit')  
        self.price_line_edit = self.find_widget(QLineEdit, 'priceLineEdit')
        self.powermix_line_edit = self.find_widget(QLineEdit, 'powermixLineEdit')
        
        self.confirm_button = self.find_widget(QPushButton, 'confirmButton')
        self.cancel_button = self.find_widget(QPushButton, 'cancelButton')

        # 设置单位提示
        self.set_placeholder_text(self.computing_power_line_edit, "FLOPS")
        self.set_placeholder_text(self.storage_space_line_edit, "GB")
        self.set_placeholder_text(self.switching_capacitance_line_edit, "fF")
        self.set_placeholder_text(self.static_power_line_edit, "nW")
        self.set_placeholder_text(self.price_line_edit, "元/s")

        # 先阻止信号（如果使用 PyQt/PySide）
        if self.computing_type_comboBox:
            self.computing_type_comboBox.blockSignals(True)  # 阻止信号
            self.computing_type_comboBox.clear()  # 清空现有项
            self.computing_type_comboBox.addItem("CPU", 0)
            self.computing_type_comboBox.addItem("GPU", 1)
            # 主动设置默认选中项（例如选中CPU）
            self.computing_type_comboBox.setCurrentIndex(0)
            self.computing_type_comboBox.blockSignals(False)  # 恢复信号

        # 初始化UI值
        self.initialize_ui_values()

        # 连接信号和槽
        if self.confirm_button:
            self.confirm_button.clicked.connect(self.accept_update)
        if self.cancel_button:
            self.cancel_button.clicked.connect(self.reject_update)

    def find_widget(self, widget_type, object_name):
        widget = self.ui.findChild(widget_type, object_name)
        if not widget:
            QMessageBox.warning(self,"警告",f"未找到UI控件 {object_name}")
        return widget

    def set_placeholder_text(self, widget, unit):
        if widget:
            widget.setPlaceholderText(f"单位: {unit}")

    def initialize_ui_values(self):
        if self.ip_line_edit:
            self.ip_line_edit.setText(self.computing_node.ip)
        if self.mask_line_edit:
            self.mask_line_edit.setText(self.computing_node.mask)
        if self.computing_type_comboBox:
            current_type = self.computing_node.computing_type
            if 0 <= current_type < self.computing_type_comboBox.count():
                self.computing_type_comboBox.setCurrentIndex(current_type)
            else:
                # 设置默认值为0 (CPU)
                self.computing_type_comboBox.setCurrentIndex(0)
                print(f"警告: 计算节点类型值 {current_type} 无效，已设为默认值 0")
        
        value_widgets = {
            self.computing_power_line_edit: self.computing_node.computing_power,
            self.storage_space_line_edit: self.computing_node.storage_space,
            self.switching_capacitance_line_edit: self.computing_node.switching_capacitance,
            self.static_power_line_edit: self.computing_node.static_power,
            self.price_line_edit: self.computing_node.price,
            self.powermix_line_edit: self.computing_node.power_mix
        }
        
        for widget, value in value_widgets.items():
            if widget:
                widget.setText(str(value))

    def validate_float_input(self, input_text, field_name):
        """验证浮点型输入"""
        try:
            return float(input_text)
        except ValueError:
            QMessageBox.warning(self, "输入错误", f"{field_name} 必须是数字")
            return None

    def accept_update(self):
        """确认更新节点参数"""
        # 验证IP地址格式
        if self.ip_line_edit:
            ip = self.ip_line_edit.text()
            if not self.validate_ip(ip):
                QMessageBox.warning(self, "输入错误", "IP地址格式不正确")
                return
            self.computing_node.ip = ip

        # 验证子网掩码格式
        if self.mask_line_edit:
            mask = self.mask_line_edit.text()
            if not self.validate_ip(mask):
                QMessageBox.warning(self, "输入错误", "子网掩码格式不正确")
                return
            self.computing_node.mask = mask

        # 更新计算类型
        if self.computing_type_comboBox:
            self.computing_node.computing_type = self.computing_type_comboBox.currentIndex()

        # 更新数值字段
        field_mapping = {
            "计算能力": (self.computing_power_line_edit, "computing_power"),
            "存储空间": (self.storage_space_line_edit, "storage_space"),
            "开关电容": (self.switching_capacitance_line_edit, "switching_capacitance"),
            "静态功耗": (self.static_power_line_edit, "static_power"),
            "价格": (self.price_line_edit, "price"),
            "混合能源参数":(self.powermix_line_edit, "power_mix")
        }

        for field_name, (widget, attr_name) in field_mapping.items():
            if widget:
                value = self.validate_float_input(widget.text(), field_name)
                if value is None:
                    return
                setattr(self.computing_node, attr_name, value)

        # 发射信号，通知主界面已更新
        self.node_updated.emit()
        
        # 关闭当前窗口
        if self.ui:
            self.ui.close()

    def validate_ip(self, ip):
        """简单验证IP地址格式"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        for part in parts:
            if not part.isdigit():
                return False
            num = int(part)
            if num < 0 or num > 255:
                return False
        return True

    def reject_update(self):
        """取消更新"""
        if self.ui:
            self.ui.close()
