from PySide6.QtWidgets import (QWidget, QLineEdit, QPushButton, QVBoxLayout, 
                              QHBoxLayout, QLabel, QComboBox, QDateTimeEdit, 
                              QMessageBox, QTableWidget, QTableWidgetItem, QGridLayout,
                              QHeaderView, QFrame, QAbstractItemView)
from PySide6.QtCore import Signal, QDateTime, Qt

class SetTaskWidget(QWidget):
    task_updated = Signal()

    def __init__(self, user_node, parent=None):
        super().__init__(parent)
        self.user_node = user_node
        self.init_ui()
        self.load_tasks()

    def init_ui(self):
        # 设置窗口标题
        self.setWindowTitle(f"用户节点 {self.user_node.index + 1} - 任务设定")
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # === 任务表单区域 ===
        form_group = QFrame()
        form_group.setFrameShape(QFrame.StyledPanel)
        form_layout = QGridLayout(form_group)
        form_layout.setColumnStretch(0, 1)
        form_layout.setColumnStretch(1, 3)
        
        # 任务产生的时刻
        form_layout.addWidget(QLabel("任务产生的时刻:"), 0, 0, Qt.AlignRight)
        self.time_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.time_edit.setDisplayFormat("HH:mm:ss")
        form_layout.addWidget(self.time_edit, 0, 1)
        
        # 所需算力类型
        form_layout.addWidget(QLabel("所需算力类型:"), 1, 0, Qt.AlignRight)
        self.computing_type_combo = QComboBox()
        self.computing_type_combo.addItem("CPU", 0)
        self.computing_type_combo.addItem("GPU", 1)
        form_layout.addWidget(self.computing_type_combo, 1, 1)
        
        # 任务所需存储空间
        form_layout.addWidget(QLabel("任务所需存储空间 (GB):"), 2, 0, Qt.AlignRight)
        self.storage_space_edit = QLineEdit()
        form_layout.addWidget(self.storage_space_edit, 2, 1)
        
        # 任务计算量
        form_layout.addWidget(QLabel("任务计算量 (10^8 Cycles):"), 3, 0, Qt.AlignRight)
        self.computing_amount_edit = QLineEdit()
        form_layout.addWidget(self.computing_amount_edit, 3, 1)
        
        # 任务传输量
        form_layout.addWidget(QLabel("任务传输量 (GB):"), 4, 0, Qt.AlignRight)
        self.transfer_amount_edit = QLineEdit()
        form_layout.addWidget(self.transfer_amount_edit, 4, 1)
        
        # 最大时延要求
        form_layout.addWidget(QLabel("最大时延要求 (s):"), 5, 0, Qt.AlignRight)
        self.latency_edit = QLineEdit()
        form_layout.addWidget(self.latency_edit, 5, 1)
        
        # 预算
        form_layout.addWidget(QLabel("预算 (元):"), 6, 0, Qt.AlignRight)
        self.budget_edit = QLineEdit()
        form_layout.addWidget(self.budget_edit, 6, 1)
        
        main_layout.addWidget(QLabel("添加新任务:"))
        main_layout.addWidget(form_group)
        
        # === 按钮区域 ===
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.add_button = QPushButton("添加任务")
        self.add_button.clicked.connect(self.accept_update)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject_update)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.add_button)
        btn_layout.addWidget(self.cancel_button)
        main_layout.addLayout(btn_layout)
        
        # === 任务列表区域 ===
        main_layout.addWidget(QLabel("已添加任务:"))
        
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(8)
        self.task_table.setHorizontalHeaderLabels([
            "任务编号", "产生时刻", "算力类型", "存储空间(GB)", 
            "计算量(10^8 Cycles)", "传输量(GB)", "最大时延(s)", "预算(元)"
        ])
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.task_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        main_layout.addWidget(self.task_table)
        
        # === 删除按钮 ===
        delete_layout = QHBoxLayout()
        self.delete_button = QPushButton("删除选中任务")
        self.delete_button.clicked.connect(self.delete_task)
        delete_layout.addStretch()
        delete_layout.addWidget(self.delete_button)
        main_layout.addLayout(delete_layout)
        
        # 调整窗口大小
        self.resize(800, 600)

    def load_tasks(self):
        """加载并显示用户节点的所有任务"""
        self.task_table.setRowCount(len(self.user_node.task_queue))
        
        for row, task in enumerate(self.user_node.task_queue):
            self.task_table.setItem(row, 0, QTableWidgetItem(str(task["任务编号"])))
            self.task_table.setItem(row, 1, QTableWidgetItem(task["任务产生的时刻"]))
            self.task_table.setItem(row, 2, QTableWidgetItem("CPU" if task["所需算力类型"] == 0 else "GPU"))
            self.task_table.setItem(row, 3, QTableWidgetItem(f"{task['任务所需存储空间']:.2f}"))
            self.task_table.setItem(row, 4, QTableWidgetItem(f"{task['任务计算量']:.2f}"))
            self.task_table.setItem(row, 5, QTableWidgetItem(f"{task['任务传输量']:.2f}"))
            self.task_table.setItem(row, 6, QTableWidgetItem(f"{task['最大时延要求']:.2f}"))
            self.task_table.setItem(row, 7, QTableWidgetItem(f"{task['预算']:.2f}"))

    def accept_update(self):
        # 输入验证... (保持原有验证逻辑不变)
        
        # 获取输入并创建新任务
        task_info = {
            "任务编号": len(self.user_node.task_queue) + 1,
            "所属用户节点编号": self.user_node.index + 1,
            "任务产生的时刻": self.time_edit.dateTime().toString("HH:mm:ss"),
            "所需算力类型": self.computing_type_combo.currentData(),
            "任务所需存储空间": float(self.storage_space_edit.text()),
            "任务计算量": float(self.computing_amount_edit.text()),
            "任务传输量": float(self.transfer_amount_edit.text()),
            "最大时延要求": float(self.latency_edit.text()),
            "预算": float(self.budget_edit.text())
        }
        
        # 添加任务到队列
        self.user_node.add_task(task_info)
        
        # 更新表格显示
        self.load_tasks()
        
        # 清空输入框
        self.storage_space_edit.clear()
        self.computing_amount_edit.clear()
        self.transfer_amount_edit.clear()
        self.latency_edit.clear()
        self.budget_edit.clear()
        
        # 显示成功消息
        QMessageBox.information(self, "成功", f"任务 {task_info['任务编号']} 添加成功")
        
        # 发射更新信号
        self.task_updated.emit()

    def delete_task(self):
        """删除选中的任务"""
        selected_rows = sorted(set(index.row() for index in self.task_table.selectedIndexes()), reverse=True)
        
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的任务")
            return
            
        if QMessageBox.question(self, "确认删除", f"确定要删除选中的 {len(selected_rows)} 个任务吗?") != QMessageBox.Yes:
            return
            
        # 从后往前删除，避免索引变化
        for row in selected_rows:
            task_id = int(self.task_table.item(row, 0).text())
            # 找到对应任务并删除
            for i, task in enumerate(self.user_node.task_queue):
                if task["任务编号"] == task_id:
                    del self.user_node.task_queue[i]
                    break
        
        # 重新编号剩余任务
        for i, task in enumerate(self.user_node.task_queue):
            task["任务编号"] = i + 1
            
        # 更新表格
        self.load_tasks()
        
        # 发射更新信号
        self.task_updated.emit()
        
        QMessageBox.information(self, "成功", "任务删除成功")

    def reject_update(self):
        self.close()    