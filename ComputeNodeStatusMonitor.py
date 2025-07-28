import json
from PySide6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox
from PySide6.QtCore import QTimer, Signal, QObject, QFile, QIODevice
from PySide6.QtUiTools import QUiLoader
# from ui_node_status import Ui_MainWindow  # 假设UI文件转换为ui_node_status.py

class ComputeNodeStatusMonitor(QMainWindow):
    def __init__(self, json_file_path, parent=None):
        super().__init__(parent)
        ui_file_path = "compute_node_status_ui.ui"
        ui_file = QFile(ui_file_path)
        if not ui_file.open(QIODevice.ReadOnly):
            print(f"无法打开UI文件: {ui_file.errorString()}")
            return
        loader = QUiLoader()
        self.ui = loader.load(ui_file)
        ui_file.close()

        if not self.ui:
            raise ValueError(f"无法加载UI文件: {loader.errorString()}")

        self.setCentralWidget(self.ui)
        # 4. 确保UI可见
        self.setWindowTitle(self.ui.windowTitle())
        self.setLayout(self.ui.layout())
        self.resize(self.ui.size())
        self.setSizePolicy(self.ui.sizePolicy())

        self.json_file_path = json_file_path
        self.node_data = []
        self.current_timestamp = 0

        # 初始化UI
        self.init_ui()

        # 连接信号槽
        self.ui.queryButton.clicked.connect(self.query_node_by_id)
        self.ui.refreshButton.clicked.connect(self.read_file)

        # 初始化定时器，每5秒自动刷新数据
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.read_file)
        self.timer.start(5000)

        # 首次读取数据
        self.read_file()


    def init_ui(self):
        """初始化表格"""
        self.ui.nodeTable.setColumnCount(11)
        headers = [
            "节点ID", "网关ID", "IP地址", "子网掩码", "计算类型",
            "计算能力", "可用存储(GB)", "交换容量", "静态功耗(W)",
            "价格(元/秒)", "任务队列长度"
        ]
        self.ui.nodeTable.setHorizontalHeaderLabels(headers)
        self.ui.nodeTable.horizontalHeader().setStretchLastSection(True)

    def read_file(self):
        """读取JSON文件并更新数据"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                new_data = json.load(f)

            if not new_data:
                QMessageBox.warning(self, "警告", "JSON文件为空或格式不正确!")
                return

            # 获取最新时间戳的数据
            latest_data = max(new_data, key=lambda x: x['timestamp'])
            self.node_data = latest_data['nodeStates']
            self.current_timestamp = latest_data['timestamp']

            # 更新表格显示
            self.update_table()

            # 更新状态栏
            self.statusBar().showMessage(f"数据已更新 - 时间戳: {self.current_timestamp}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取文件失败: {str(e)}")

    def update_table(self):
        """更新表格数据"""
        self.ui.nodeTable.setRowCount(len(self.node_data))

        for row, node in enumerate(self.node_data):
            self.ui.nodeTable.setItem(row, 0, QTableWidgetItem(str(node['nodeId'])))
            self.ui.nodeTable.setItem(row, 1, QTableWidgetItem(str(node['gatewayId'])))
            self.ui.nodeTable.setItem(row, 2, QTableWidgetItem(node['ipAddress']))
            self.ui.nodeTable.setItem(row, 3, QTableWidgetItem(node['subnetMask']))
            self.ui.nodeTable.setItem(row, 4, QTableWidgetItem(str(node['computeType'])))
            self.ui.nodeTable.setItem(row, 5, QTableWidgetItem(f"{node['computeCapacity']:.2e}"))
            self.ui.nodeTable.setItem(row, 6, QTableWidgetItem(str(node['availableStorage'])))
            self.ui.nodeTable.setItem(row, 7, QTableWidgetItem(str(node['switchCapacitance'])))
            self.ui.nodeTable.setItem(row, 8, QTableWidgetItem(str(node['staticPower'])))
            self.ui.nodeTable.setItem(row, 9, QTableWidgetItem(str(node['price'])))
            self.ui.nodeTable.setItem(row, 10, QTableWidgetItem(str(len(node['taskQueue']))))

    def getInfoById(self, node_id):
        """根据节点ID获取节点信息"""
        for node in self.node_data:
            if node['nodeId'] == node_id:
                return node
        return None

    def query_node_by_id(self):
        """查询按钮点击事件"""
        node_id_str = self.ui.nodeIdInput.text().strip()
        if not node_id_str:
            QMessageBox.warning(self, "警告", "请输入节点ID!")
            return

        try:
            node_id = int(node_id_str)
        except ValueError:
            QMessageBox.warning(self, "警告", "节点ID必须是整数!")
            return

        node_info = self.getInfoById(node_id)
        if node_info:
            # 格式化显示节点信息
            info_text = f"""节点ID: {node_info['nodeId']}
网关ID: {node_info['gatewayId']}
IP地址: {node_info['ipAddress']}
子网掩码: {node_info['subnetMask']}
计算类型: {node_info['computeType']}
计算能力: {node_info['computeCapacity']:.2e} FLOPS
可用存储: {node_info['availableStorage']} GB
交换容量: {node_info['switchCapacitance']}
静态功耗: {node_info['staticPower']} W
价格: {node_info['price']} 元/秒

任务队列:"""

            for task in node_info['taskQueue']:
                info_text += f"\n  任务ID: {task['taskId']}, 排队时间: {task['queuingTime_s']}秒"

            if not node_info['taskQueue']:
                info_text += "\n  无任务"

            self.ui.nodeDetailText.setPlainText(info_text)
        else:
            QMessageBox.warning(self, "警告", f"未找到ID为 {node_id} 的节点!")


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = ComputeNodeStatusMonitor("compute_node_status.json")
    window.show()
    sys.exit(app.exec())