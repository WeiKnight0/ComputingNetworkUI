import json
import os
from pathlib import Path
from typing import Dict, List

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (QDialog, QFileDialog, QMessageBox, QCheckBox,
                               QLabel, QVBoxLayout, QWidget, QFormLayout)
from PySide6.QtCore import Qt, QFile, QIODevice

from result_output import export_simulation_results


class SimulationExportDialog(QDialog):
    def __init__(self, json_path: str, parent=None):
        super().__init__(parent)

        # 1. 确保UI文件路径正确
        ui_path = Path(__file__).parent / "simulation_export_ui.ui"
        if not ui_path.exists():
            raise FileNotFoundError(f"UI文件未找到: {ui_path}")

        # 2. 正确打开文件
        ui_file = QFile(str(ui_path))
        if not ui_file.open(QIODevice.ReadOnly):
            raise IOError(f"无法打开UI文件: {ui_file.errorString()}")

        # 3. 加载UI
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)  # 设置self为父窗口
        ui_file.close()
        # self.ui

        if not self.ui:
            raise RuntimeError("加载UI失败")

        # 4. 确保UI可见
        self.ui.setWindowTitle("仿真结果导出")
        self.setWindowTitle(self.ui.windowTitle())
        self.setLayout(self.ui.layout())
        self.resize(self.ui.size())
        self.setSizePolicy(self.ui.sizePolicy())

        # 模态化
        self.setModal(True)

        # 5. 连接信号槽等初始化代码
        self.json_path = json_path
        self.setup_connections()

        # 设置默认路径
        default_dir = str(Path(json_path).parent)
        default_name = str(Path(json_path).stem) + "_export.csv"
        self.ui.pathEdit.setText(str(Path(default_dir) / default_name))

        # 加载并显示数据
        self.load_and_display_data()

    def setup_connections(self):
        """设置信号与槽的连接"""
        self.ui.browseButton.clicked.connect(self.browse_output_path)
        self.ui.exportButton.clicked.connect(self.export_data)
        self.ui.cancelButton.clicked.connect(self.reject)
        self.ui.formatCombo.currentIndexChanged.connect(self.update_file_extension)

    def load_and_display_data(self):
        """加载并显示数据"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.json_data = json.load(f)

            # 显示全局指标
            self.display_global_info()

            # 显示计算节点指标
            self.display_compute_node_info()

            # 显示任务指标
            self.display_task_info()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载JSON文件: {str(e)}")
            self.json_data = None

    def display_global_info(self):
        """显示全局指标"""
        if not self.json_data.get('globalInfo'):
            self.ui.globalInfoGroup.setVisible(False)
            return

        global_info = self.json_data['globalInfo']

        if 'taskThroughput' in global_info:
            metric = global_info['taskThroughput']
            self.ui.taskThroughputLabel.setText(
                f"任务吞吐量: {metric['value']} 任务数/秒"
            )
            self.ui.taskThroughputDesc.setText(metric['description'])
            self.ui.taskThroughputCheck.setChecked(True)
        else:
            self.ui.taskThroughputCheck.setVisible(False)
            self.ui.taskThroughputLabel.setText("任务吞吐量: 无数据")
            self.ui.taskThroughputDesc.setText("")

    def display_compute_node_info(self):
        """显示计算节点指标"""
        if not self.json_data.get('computeNodeInfo'):
            self.ui.computeNodeGroup.setVisible(False)
            return

        for node in self.json_data['computeNodeInfo']:
            tab = QWidget()
            layout = QFormLayout()
            tab.setLayout(layout)

            node_id = node.get('computeNodeId', '未知')
            self.ui.computeNodeTabs.addTab(tab, f"节点 {node_id}")

            # 负载均衡指标
            if 'loadBalancingMetrics' in node:
                lb_metrics = node['loadBalancingMetrics']
                self.add_metric_row(layout, "平均利用率", lb_metrics.get('averageUtilization'))
                self.add_metric_row(layout, "已分配任务数", lb_metrics.get('totalAssignedTasks'))
                self.add_metric_row(layout, "已处理计算量", lb_metrics.get('totalProcessedLoad'))

            # 能耗指标
            if 'energyConsumption' in node:
                self.add_metric_row(layout, "能耗", node.get('energyConsumption'))

    def display_task_info(self):
        """显示任务指标"""
        if not self.json_data.get('taskInfo'):
            self.ui.taskInfoGroup.setVisible(False)
            return

        for task in self.json_data['taskInfo']:
            tab = QWidget()
            layout = QFormLayout()
            tab.setLayout(layout)

            task_id = task.get('taskId', '未知')
            user_node = task.get('userNodeId', '未知')
            self.ui.taskInfoTabs.addTab(tab, f"任务 {task_id} (用户{user_node})")

            # 基本任务信息
            self.add_metric_row(layout, "状态", {"value": task.get('status'), "description": "任务状态"})
            self.add_metric_row(layout, "计算节点",
                                {"value": task.get('computeNodeId'), "description": "处理任务的节点ID"})

            # 延迟分布
            if task.get('delayDistribution'):
                delay_dist = task['delayDistribution']
                self.add_metric_row(layout, "端到端延迟", delay_dist.get('endToEndDelay'))
                self.add_metric_row(layout, "计算时间", delay_dist.get('computationTime'))

            # 成本
            if 'cost' in task:
                self.add_metric_row(layout, "成本", task.get('cost'))

    def add_metric_row(self, layout: QFormLayout, name: str, metric: dict):
        """添加指标行到布局"""
        if not metric:
            return

        checkbox = QCheckBox()
        value = metric.get('value', '无数据')
        desc = metric.get('description', '')

        value_label = QLabel(f"{name}: {value}")
        desc_label = QLabel(desc)
        desc_label.setWordWrap(True)

        layout.addRow(checkbox, value_label)
        layout.addRow(None, desc_label)

        # 默认选中
        checkbox.setChecked(True)

        return checkbox

    def browse_output_path(self):
        """浏览输出路径"""
        current_path = self.ui.pathEdit.text()
        if not current_path:
            current_path = str(Path(self.json_path).parent)

        selected_format = self.ui.formatCombo.currentText()
        if "Excel" in selected_format:
            file_filter = "Excel Files (*.xlsx);;All Files (*)"
            default_ext = ".xlsx"
        else:
            file_filter = "CSV Files (*.csv);;All Files (*)"
            default_ext = ".csv"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择导出路径",
            current_path,
            file_filter
        )

        if file_path:
            if not file_path.lower().endswith(default_ext):
                file_path += default_ext
            self.ui.pathEdit.setText(file_path)

    def update_file_extension(self):
        """根据选择的格式更新文件扩展名"""
        current_path = self.ui.pathEdit.text()
        if not current_path:
            return

        selected_format = self.ui.formatCombo.currentText()
        if "Excel" in selected_format:
            new_ext = ".xlsx"
        else:
            new_ext = ".csv"

        base_path = current_path
        while True:
            name, ext = os.path.splitext(base_path)
            if not ext:
                break
            base_path = name

        new_path = base_path + new_ext
        self.ui.pathEdit.setText(new_path)

    def get_export_config(self) -> Dict:
        """获取导出配置"""
        config = {
            "globalInfo": {
                "taskThroughput": self.ui.taskThroughputCheck.isChecked()
            },
            "computeNodeInfo": [],
            "taskInfo": []
        }

        # 获取计算节点指标选择状态 (简化处理，实际应用中需要更复杂的逻辑)
        for i in range(self.ui.computeNodeTabs.count()):
            tab = self.ui.computeNodeTabs.widget(i)
            node_config = {
                "loadBalancingMetrics": {
                    "averageUtilization": True,
                    "totalAssignedTasks": True,
                    "totalProcessedLoad": True
                },
                "energyConsumption": True
            }
            config["computeNodeInfo"].append(node_config)

        # 获取任务指标选择状态 (简化处理)
        for i in range(self.ui.taskInfoTabs.count()):
            tab = self.ui.taskInfoTabs.widget(i)
            task_config = {
                "status": True,
                "delayDistribution": {
                    "endToEndDelay": True,
                    "computationTime": True
                },
                "cost": True
            }
            config["taskInfo"].append(task_config)

        return config

    def export_data(self):
        """执行导出操作"""
        output_path = self.ui.pathEdit.text()
        if not output_path:
            QMessageBox.warning(self, "警告", "请指定导出路径")
            return

        export_config = self.get_export_config()
        export_format = 'excel' if "Excel" in self.ui.formatCombo.currentText() else 'csv'

        try:
            export_simulation_results(
                json_path=self.json_path,
                export_config=export_config,
                output_path=output_path,
                format=export_format
            )

            QMessageBox.information(self, "成功", f"数据已成功导出到:\n{output_path}")
            # self.accept()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # 示例JSON路径
    example_json = "results.json"
    if not Path(example_json).exists():
        raise RuntimeError("文件不存在")

    dialog = SimulationExportDialog(example_json)
    dialog.exec()
    print("结束")