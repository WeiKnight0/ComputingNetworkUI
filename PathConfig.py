from PySide6.QtWidgets import (QDialog, QFileDialog, QMessageBox, QLabel)
from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
import os
from pathlib import Path


class PathConfigDialog(QDialog):
    def __init__(self, initial_omnetpp_dir="", initial_project_dir="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("路径配置")

        # 加载UI文件
        self.ui = None
        self.load_ui()
        self.setWindowTitle(self.ui.windowTitle())
        self.setLayout(self.ui.layout())
        self.resize(self.ui.size())
        self.setSizePolicy(self.ui.sizePolicy())

        # 设置初始值
        self.ui.omnetppDirInput.setText(initial_omnetpp_dir)
        self.ui.projectDirInput.setText(initial_project_dir)

        # 连接信号槽
        self.ui.buttonBox.accepted.connect(self.validate_and_accept)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.ui.browseOmnetButton.clicked.connect(self.browse_omnet_dir)
        self.ui.browseProjectButton.clicked.connect(self.browse_project_dir)

    def load_ui(self):
        """加载UI文件"""
        ui_file = QFile("config_dialog.ui")
        if not ui_file.open(QFile.ReadOnly):
            raise IOError(f"无法加载UI文件: {ui_file.errorString()}")

        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        ui_file.close()

    def browse_omnet_dir(self):
        """浏览OMNETPP目录"""
        current_dir = self.ui.omnetppDirInput.text() or os.path.expanduser("~")
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择OMNET++目录", current_dir)
        if dir_path:
            self.ui.omnetppDirInput.setText(dir_path)

    def browse_project_dir(self):
        """浏览项目目录"""
        current_dir = self.ui.projectDirInput.text() or os.path.expanduser("~")
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择项目目录", current_dir)
        if dir_path:
            self.ui.projectDirInput.setText(dir_path)

    def validate_and_accept(self):
        """验证输入并接受对话框"""
        omnet_dir = self.ui.omnetppDirInput.text()
        project_dir = self.ui.projectDirInput.text()

        # 简单的路径验证
        if omnet_dir and not os.path.exists(omnet_dir):
            QMessageBox.warning(self, "路径无效", "OMNETPP_DIR路径不存在！")
            return

        if project_dir and not os.path.exists(project_dir):
            QMessageBox.warning(self, "路径无效", "PROJECT_DIR路径不存在！")
            return

        def is_subpath_and_relative(path1, path2):
            path1 = Path(path1).resolve()
            path2 = Path(path2).resolve()
            try:
                is_subpath = path1 in path2.parents or path1 == path2
                if is_subpath:
                    # 计算相对路径
                    relative_path = path2.relative_to(path1)
                    return (True, f"./{relative_path}")
                else:
                    return (False, "Path2 is not a subpath of Path1")
            except ValueError:
                return (False, "Path2 is not a subpath of Path1")

        if is_subpath_and_relative(omnet_dir, project_dir)[0]:
            self.accept()
        else:
            QMessageBox.warning(self, "路径无效", "路径不和规范！")



    def get_paths(self):
        """获取配置的路径"""
        return {
            "OMNETPP_DIR": self.ui.omnetppDirInput.text(),
            "PROJECT_DIR": self.ui.projectDirInput.text()
        }