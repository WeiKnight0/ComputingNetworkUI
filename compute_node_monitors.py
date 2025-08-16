import json
from pathlib import Path
from typing import Optional, Union, List


class ComputeNodeStatusReader:
    """
    Compute Node Status JSON 文件读取器

    功能：
    1. 从JSON文件读取计算节点状态数据
    2. 提供获取全部节点状态的方法
    3. 提供按节点ID获取特定节点状态的方法
    """

    def __init__(self, json_file_path:Optional[str]):
        """
        初始化读取器

        参数:
            json_file_path (str): JSON文件路径
        """
        self.json_file_path = json_file_path
        self._load_data()

    def _load_data(self):
        """内部方法：加载JSON数据"""
        if self.json_file_path is None:
            return
        try:
            with open(self.json_file_path, 'r') as file:
                self.data = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"文件 {self.json_file_path} 未找到")
        except json.JSONDecodeError:
            raise ValueError(f"文件 {self.json_file_path} 不是有效的JSON格式")

    def get_node_status(self):
        """
        获取所有节点状态

        返回:
            dict: 包含时间戳和所有节点状态的字典
        """
        return self.data.copy()

    def get_node_status_by_id(self, node_id):
        """
        按节点ID获取特定节点状态

        参数:
            node_id (int): 要查询的节点ID

        返回:
            dict: 包含时间戳和匹配节点状态的字典，结构如下:
                {
                    "timestamp": float,
                    "nodeStates": [dict]  # 只包含匹配的节点
                }

        异常:
            ValueError: 如果找不到指定节点ID
        """
        matched_nodes = [node for node in self.data["nodeStates"] if node["nodeId"] == node_id]

        if not matched_nodes:
            raise ValueError(f"节点ID {node_id} 未找到")

        return {
            "timestamp": self.data["timestamp"],
            "nodeStates": matched_nodes
        }

    def update(self, new_file_path:Optional[Union[str,Path]]=None):
        if new_file_path:
            if isinstance(new_file_path,Union[str,Path]):
                self.json_file_path = str(new_file_path)
        self._load_data()


from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QToolTip
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QCursor
from typing import Optional


class ComputeNodePropertyWindow(QDialog):
    """显示单个计算节点所有属性的窗口"""

    update_requested = Signal(int)  # 当请求更新数据时发射的信号

    def __init__(self, node, json_path: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.node = node
        self.reader = ComputeNodeStatusReader(json_path)
        self.setWindowTitle(f"节点 {node.index} 属性详情")
        self.setMinimumSize(600, 500)

        self.init_ui()
        self.load_data()

    def init_ui(self):
        """初始化UI界面"""
        layout = QVBoxLayout()

        # 基本信息标签
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.info_label)

        # 主属性表格（显示所有指标）
        self.main_table = QTableWidget()
        self.main_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.main_table.setColumnCount(2)
        self.main_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.main_table.horizontalHeader().setVisible(False)
        self.main_table.verticalHeader().setVisible(False)
        self.main_table.setAlternatingRowColors(True)
        self.main_table.setShowGrid(False)
        self.main_table.setMouseTracking(True)
        self.main_table.cellEntered.connect(self.handle_cell_hover)
        layout.addWidget(self.main_table)

        self.setLayout(layout)

    def handle_cell_hover(self, row: int, col: int):
        """处理表格单元格悬停事件"""
        item = self.main_table.item(row, 0)
        if item and item.text() == "任务队列":
            self.show_task_queue_tooltip()

    def show_task_queue_tooltip(self):
        """显示任务队列的悬停提示"""
        if not hasattr(self, '_current_tasks'):
            return

        if self._current_tasks is []:
            QToolTip.showText(QCursor.pos(), "当前没有任务")
            return
        elif self._current_tasks is None:
            QToolTip.showText(QCursor.pos(), "暂无数据")
            return

        tooltip = "任务队列详情:\n\n"
        tooltip += "\n".join(
            f"• 任务ID: {task['taskId']} (排队: {task['queuingTime']}s)"
            for task in self._current_tasks
        )
        QToolTip.showText(QCursor.pos(), tooltip)

    def load_data(self):
        """加载并显示所有节点数据"""
        # 显示基本信息标题
        self.info_label.setText(
            f"节点ID: {self.node.index} | "
            f"类型: {'GPU' if self.node.computing_type == 1 else 'CPU'} | "
            f"存储: {self.node.storage_space}GB"
        )

        # 准备所有要显示的属性
        properties = self.collect_all_properties()
        self.main_table.setRowCount(len(properties))

        # 填充表格数据
        for row, (name, value) in enumerate(properties):
            # 第一列：属性名
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.main_table.setItem(row, 0, name_item)

            # 第二列：属性值
            value_item = QTableWidgetItem(str(value))
            value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)

            # 特殊处理任务队列显示
            if name == "任务队列":
                if self._current_tasks is not None:
                    task_count = len(self._current_tasks) if hasattr(self, '_current_tasks') else 0
                    value_item.setText(f"{task_count}个任务 (悬停查看详情)")
                    value_item.setData(Qt.UserRole, self._current_tasks)  # 存储完整数据
                    value_item.setToolTip("鼠标悬停查看任务详情")
                else:
                    value_item.setText(value)
            self.main_table.setItem(row, 1, value_item)

    def collect_all_properties(self) -> List[tuple]:
        """收集所有要显示的属性（节点属性+JSON状态）"""
        properties = []

        # 节点静态属性
        properties.extend([
            ("算力类型", "GPU" if self.node.computing_type == 1 else "CPU"),
            ("存储空间 (GB)", self.node.storage_space),
            ("计算能力 (FLOPS)", f"{self.node.computing_power:.2e}"),
            ("开关电容 (fF)", f"{self.node.switching_capacitance:.2e}"),
            ("静态功耗 (nW)", f"{self.node.static_power:.2e}"),
            ("价格 (元/秒)", self.node.price),
            ("能源混合参数", self.node.power_mix),
        ])

        # 从JSON加载动态状态
        # 更新时间
        try:
            status = self.reader.get_node_status_by_id(self.node.index)
            node_state = status["nodeStates"][0]
            self._current_tasks = node_state.get("taskQueue", [])

            properties.extend([
                ("可用存储 (GB)", node_state.get("availableStorage", -1)),
                ("最后更新时间 (s)", status["timestamp"]),
                ("任务队列", self._current_tasks),  # 特殊处理
            ])
        except Exception as e:
            print(f"加载状态失败: {e}")
            self._current_tasks = None
            properties.extend(
                (
                    ("可用存储 (GB)", "暂无数据"),
                    ("最后更新时间 (s)", "暂无数据"),
                    ("任务队列", "暂无数据")
                )
            )  # 空任务队列

        return properties

    def update_data(self, new_json_path: Optional[str] = None):
        """更新显示的数据"""
        if new_json_path:
            self.reader.update(new_json_path)
        self.load_data()