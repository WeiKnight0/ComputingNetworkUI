import json
from typing import Dict, Union, Optional
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtUiTools import QUiLoader
from result_output import export_simulation_results

class SimulationExportDialog(QDialog):
    def __init__(self, json_path: str, parent=None):
        super().__init__(parent)
        self.json_path = json_path
        self.json_data = self.load_json_data()
        if self.json_data is None:
            return

        # Load UI file
        loader = QUiLoader()
        ui_file = Path(__file__).parent / "simulation_export_ui.ui"
        self.ui = loader.load(str(ui_file), self)

        self.setup_ui()
        self.setup_connections()

    def load_json_data(self) -> Optional[dict]:
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            QMessageBox.critical(
                self, "错误", f"无法加载JSON文件: {str(e)}"
            )
            return None

    def setup_ui(self):
        # Setup global info
        self.setup_global_info()

        # Setup compute node info
        self.setup_compute_node_info()

        # Setup task info
        self.setup_task_info()

        # setup_ui
        self.setWindowTitle(self.ui.windowTitle())
        self.setLayout(self.ui.layout())
        # Remove setFixedSize and use resize instead
        self.resize(self.ui.size())
        self.setModal(True)

        # 设置表格
        tables = [self.ui.globalTable, self.ui.nodesTable, self.ui.tasksTable]
        for table in tables:
            table:QTableWidget
            header = table.horizontalHeader()
            table.resizeRowsToContents()  # 自动调整行高以适应内容
            header.setSectionResizeMode(QHeaderView.Stretch)

    def setup_global_info(self):
        if "globalInfo" not in self.json_data:
            return

        global_info = self.json_data["globalInfo"]
        table = self.ui.globalTable
        table.setRowCount(len(global_info))
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["指标", "值", "描述"])

        # Translation mapping for global info
        global_translations = {
            "taskThroughput": "任务吞吐量"
        }

        for row, (key, data) in enumerate(global_info.items()):
            translated_key = global_translations.get(key, key)
            table.setItem(row, 0, QTableWidgetItem(translated_key))
            table.setItem(row, 1, QTableWidgetItem(str(data.get("value", ""))))
            table.setItem(row, 2, QTableWidgetItem(data.get("description", "")))

        table.resizeColumnsToContents()

    def setup_compute_node_info(self):
        if "computeNodeInfo" not in self.json_data:
            return

        nodes_info = self.json_data["computeNodeInfo"]
        if not nodes_info:
            return

        # Get all possible metrics from the first node
        first_node = nodes_info[0]
        metrics = []

        # Collect all metrics from loadBalancingMetrics
        lb_metrics = first_node.get("loadBalancingMetrics", {})
        for metric in lb_metrics.keys():
            metrics.append(("loadBalancingMetrics", metric))

        # Add other top-level metrics
        for key in first_node.keys():
            if key not in ["computeNodeId", "loadBalancingMetrics"] and isinstance(first_node[key], dict):
                metrics.append((key, None))

        # Setup table
        table = self.ui.nodesTable
        table.setRowCount(len(nodes_info))
        table.setColumnCount(1 + len(metrics))  # 1 for node ID

        # Translation mapping for node info
        node_translations = {
            "computeNodeId": "节点ID",
            "averageUtilization": "平均利用率",
            "totalAssignedTasks": "分配任务总数",
            "totalProcessedLoad": "处理总负载",
            "energyConsumption": "能耗",
            "loadBalancingMetrics": "负载均衡指标"
        }

        # Set headers
        headers = ["节点ID"]
        for metric in metrics:
            if metric[1] is None:
                headers.append(node_translations.get(metric[0], metric[0]))
            else:
                headers.append(node_translations.get(metric[1], metric[1]))
        table.setHorizontalHeaderLabels(headers)

        # Fill data
        for row, node in enumerate(nodes_info):
            table.setItem(row, 0, QTableWidgetItem(str(node["computeNodeId"])))

            for col, (category, metric) in enumerate(metrics, start=1):
                if metric is None:
                    # Top-level metric
                    value = node.get(category, {}).get("value", "")
                else:
                    # Nested metric
                    value = node.get(category, {}).get(metric, {}).get("value", "")
                table.setItem(row, col, QTableWidgetItem(str(value)))

        table.resizeColumnsToContents()

    def setup_task_info(self):
        if "taskInfo" not in self.json_data:
            return

        tasks_info = self.json_data["taskInfo"]
        if not tasks_info:
            return

        # Translation mapping for task info
        task_translations = {
            "taskId": "任务ID",
            "userNodeId": "用户节点ID",
            "status": "状态",
            "computeNodeId": "算力节点ID",
            "endToEndDelay": "端到端时延",
            "computationTime": "计算时间",
            "cost": "成本",
            "delayDistribution": "延迟分布"
        }

        # Define basic info columns
        basic_info = ["taskId", "userNodeId", "status", "computeNodeId"]
        translated_basic_info = [task_translations.get(col, col) for col in basic_info]

        # Define metrics columns
        metrics = [
            ("delayDistribution", "endToEndDelay"),
            ("delayDistribution", "computationTime"),
            ("cost", None)
        ]
        translated_metrics = [task_translations.get(metric[1], metric[1]) if metric[1] else task_translations.get(metric[0], metric[0]) for metric in metrics]

        # Setup table
        table = self.ui.tasksTable
        table.setRowCount(len(tasks_info))
        table.setColumnCount(len(basic_info) + len(metrics))

        # Set headers
        headers = translated_basic_info.copy()
        headers.extend(translated_metrics)
        table.setHorizontalHeaderLabels(headers)

        # Status translation
        status_translation = {
            "COMPLETED": "已完成",
            "UNCOMPLETED": "未完成"
        }

        # Fill data
        for row, task in enumerate(tasks_info):
            # Basic info
            for col, key in enumerate(basic_info):
                value = task.get(key, "")
                if value is None:
                    value = ""
                # Translate status
                if key == "status":
                    value = status_translation.get(value, value)
                table.setItem(row, col, QTableWidgetItem(str(value)))

            # Metrics
            for col, (category, metric) in enumerate(metrics, start=len(basic_info)):
                if metric is None:
                    # Top-level metric (e.g. cost)
                    value = task.get(category, {}).get("value", "")
                else:
                    # Nested metric (e.g. delayDistribution items)
                    category_data = task.get(category)
                    if category_data is None:
                        value = ""
                    else:
                        value = category_data.get(metric, {}).get("value", "")
                table.setItem(row, col, QTableWidgetItem(str(value)))

        table.resizeColumnsToContents()

    def setup_connections(self):
        self.ui.exportButton.clicked.connect(self.on_export)
        self.ui.cancelButton.clicked.connect(self.reject)
        self.ui.browseButton.clicked.connect(self.on_browse)  # 新增浏览按钮连接

    def on_browse(self):
        """处理浏览按钮点击事件"""
        # 获取当前选择的文件类型
        file_type = self.ui.fileTypeComboBox.currentText()
        file_filter = file_type

        # 打开文件选择对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择导出文件路径",
            "",
            file_filter,
            file_filter.split("(")[-1].rstrip(")")
        )

        if file_path:
            self.ui.outputPathLineEdit.setText(file_path)

    def on_export(self):
        """处理导出按钮点击事件"""
        # 获取导出选项
        export_options = self.get_export_options()

        # 获取输出路径
        output_path = self.ui.outputPathLineEdit.text().strip()
        if not output_path:
            QMessageBox.warning(self, "警告", "请先选择输出文件路径")
            return

        # 确保文件扩展名与选择的类型匹配
        file_type = self.ui.fileTypeComboBox.currentText()
        if "CSV" in file_type and not output_path.endswith('.csv'):
            output_path += '.csv'
        elif "Excel" in file_type and not output_path.endswith('.xlsx'):
            output_path += '.xlsx'

        try:
            # 调用导出函数
            export_simulation_results(
                json_path=self.json_path,
                export_config=export_options,
                output_path=output_path
            )

            QMessageBox.information(
                self, "成功", f"结果已成功导出到: {output_path}"
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self, "错误", f"导出失败: {str(e)}"
            )

    def get_export_options(self) -> Dict[str, Union[bool, Dict]]:
        """Get export options from the current UI state"""
        export_options = {
            "globalInfo": self.ui.globalExportCheckBox.isChecked(),
            "computeNodeInfo": {
                "enabled": self.ui.nodesExportCheckBox.isChecked(),
                "metrics": {
                    "loadBalancingMetrics": [],
                    "energyConsumption": self.ui.nodeEnergyConsumptionCheckBox.isChecked()
                }
            },
            "taskInfo": {
                "enabled": self.ui.tasksExportCheckBox.isChecked(),
                "metrics": {
                    "delayDistribution": [],
                    "cost": self.ui.taskCostCheckBox.isChecked()
                }
            }
        }

        # Add load balancing metrics
        if self.ui.nodeAvgUtilCheckBox.isChecked():
            export_options["computeNodeInfo"]["metrics"]["loadBalancingMetrics"].append("averageUtilization")
        if self.ui.nodeAssignedTasksCheckBox.isChecked():
            export_options["computeNodeInfo"]["metrics"]["loadBalancingMetrics"].append("totalAssignedTasks")
        if self.ui.nodeProcessedLoadCheckBox.isChecked():
            export_options["computeNodeInfo"]["metrics"]["loadBalancingMetrics"].append("totalProcessedLoad")

        # Add delay distribution metrics
        if self.ui.taskEndToEndDelayCheckBox.isChecked():
            export_options["taskInfo"]["metrics"]["delayDistribution"].append("endToEndDelay")
        if self.ui.taskComputationTimeCheckBox.isChecked():
            export_options["taskInfo"]["metrics"]["delayDistribution"].append("computationTime")

        return export_options

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # For testing, you can pass a JSON file path as argument
    json_path = "results.json"

    dialog = SimulationExportDialog(json_path)
    dialog.exec()
    # sys.exit(app.exec())