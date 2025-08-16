import os
import re
from PySide6.QtWidgets import (QDialog, QGridLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox, QFileDialog,
                               QSpacerItem, QSizePolicy, QFrame)
from PySide6.QtCore import Qt


class PathConfigDialog(QDialog):
    def __init__(self, omnetpp_dir, project_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OMNeT++项目路径配置")
        self.setFixedSize(650, 220)

        self.initial_omnetpp_dir = omnetpp_dir
        self.initial_project_name = project_name

        self.setup_ui()
        self.update_project_path()

    def setup_ui(self):
        main_layout = QGridLayout()
        main_layout.setVerticalSpacing(12)
        main_layout.setHorizontalSpacing(10)

        # 第一行：OMNETPP路径
        self.omnetpp_label = QLabel("OMNETPP路径:")
        self.omnetpp_input = QLineEdit(self.initial_omnetpp_dir)
        self.omnetpp_input.textChanged.connect(self.update_project_path)
        self.omnetpp_browse = QPushButton("浏览...")
        self.omnetpp_browse.setFixedWidth(80)
        self.omnetpp_browse.clicked.connect(self.browse_omnetpp_dir)

        main_layout.addWidget(self.omnetpp_label, 0, 0, Qt.AlignRight)
        main_layout.addWidget(self.omnetpp_input, 0, 1)
        main_layout.addWidget(self.omnetpp_browse, 0, 2)

        # 第二行：项目名称
        self.project_name_label = QLabel("项目名称:")
        self.project_name_input = QLineEdit(self.initial_project_name)
        self.project_name_input.textChanged.connect(self.update_project_path)

        main_layout.addWidget(self.project_name_label, 1, 0, Qt.AlignRight)
        main_layout.addWidget(self.project_name_input, 1, 1, 1, 2)

        # 第三行：项目路径
        self.project_path_label = QLabel("项目路径:")
        self.project_path_display = QLabel()
        self.project_path_display.setWordWrap(True)
        self.project_path_display.setStyleSheet("""
            QLabel {
                color: #555;
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                padding: 3px;
                border-radius: 3px;
            }
        """)
        self.project_path_display.setMinimumHeight(30)
        self.project_path_display.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        main_layout.addWidget(self.project_path_label, 2, 0, Qt.AlignRight | Qt.AlignTop)
        main_layout.addWidget(self.project_path_display, 2, 1, 1, 2)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator, 3, 0, 1, 3)

        # 按钮行 (使用网格布局实现右对齐按钮)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setFixedWidth(80)
        self.cancel_button.clicked.connect(self.reject)

        self.confirm_button = QPushButton("确认")
        self.confirm_button.setFixedWidth(80)
        self.confirm_button.clicked.connect(self.validate_inputs)

        main_layout.addWidget(self.confirm_button, 4, 1, Qt.AlignRight)
        main_layout.addWidget(self.cancel_button, 4, 2)

        # 设置列宽比例
        main_layout.setColumnStretch(0, 1)
        main_layout.setColumnStretch(1, 5)
        main_layout.setColumnStretch(2, 1)

        self.setLayout(main_layout)

    def browse_omnetpp_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择OMNETPP目录", self.omnetpp_input.text()
        )
        if dir_path:
            self.omnetpp_input.setText(dir_path)

    def update_project_path(self):
        """根据当前输入更新项目路径显示"""
        omnetpp_dir = self.omnetpp_input.text().strip()
        project_name = self.project_name_input.text().strip()

        if omnetpp_dir and project_name:
            project_dir = os.path.join(
                omnetpp_dir,
                "samples",
                "inet",
                "examples",
                "computing_power_network",
                project_name
            ).replace('\\','/')
            self.project_path_display.setText(project_dir)
        else:
            self.project_path_display.setText("")

    def validate_inputs(self):
        omnetpp_dir = self.omnetpp_input.text().strip()
        omnetpp_dir = os.path.join(omnetpp_dir,'')
        project_name = self.project_name_input.text().strip()

        # 验证OMNETPP路径
        if not omnetpp_dir:
            QMessageBox.warning(self, "错误", "OMNETPP路径不能为空")
            return

        expected_dir = os.path.join("omnetpp-5.6.2", "")
        if not omnetpp_dir.replace("\\", "/").endswith(expected_dir.replace("\\", "/")):
            QMessageBox.warning(self, "错误", f"OMNETPP路径应该以\"omnetpp-5.6.2\"结尾")
            return

        if not os.path.isdir(omnetpp_dir):
            QMessageBox.warning(self, "错误", "指定的OMNETPP路径不存在")
            return

        # 验证项目名称
        if not project_name:
            QMessageBox.warning(self, "错误", "项目名称不能为空")
            return

        if re.search("[\u4e00-\u9fff]", project_name):
            QMessageBox.warning(self, "错误", "项目名称不能包含中文字符")
            return

        # 生成项目路径
        project_dir = os.path.join(
            omnetpp_dir,
            "samples",
            "inet",
            "examples",
            "computing_power_network",
            project_name
        ).replace('\\','/')

        # 检查项目路径是否存在
        if not os.path.exists(project_dir):
            reply = QMessageBox.question(
                self, "确认",
                f"项目路径不存在:\n{project_dir}\n\n是否要创建该目录?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                try:
                    os.makedirs(project_dir)
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"创建目录失败: {str(e)}")
                    return
            else:
                return

        # 所有验证通过，关闭对话框
        self.accept()

    def get_config(self):
        """返回配置字典"""
        omnetpp_dir = self.omnetpp_input.text().strip()
        project_name = self.project_name_input.text().strip()

        project_dir = os.path.join(
            omnetpp_dir,
            "samples",
            "inet",
            "examples",
            "computing_power_network",
            project_name
        ).replace('\\','/')

        return {
            "OMNETPP_DIR": omnetpp_dir,
            "PROJECT_DIR": project_dir,
            "PROJECT_NAME": project_name
        }


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # 测试时可以传入初始路径
    dialog = PathConfigDialog(
        omnetpp_dir="C:\omnetpp-5.6.2",
        project_name="my_project"
    )

    if dialog.exec() == QDialog.Accepted:
        config = dialog.get_config()
        print("配置信息:", config)
    else:
        print("用户取消了配置")

    # sys.exit(app.exec())