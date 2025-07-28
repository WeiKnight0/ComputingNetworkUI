# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'simulation_export_ui.ui'
##
## Created by: Qt User Interface Compiler version 6.8.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QFormLayout, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea,
    QSizePolicy, QSpacerItem, QTabWidget, QVBoxLayout,
    QWidget)

class Ui_SimulationExportDialog(object):
    def setupUi(self, SimulationExportDialog):
        if not SimulationExportDialog.objectName():
            SimulationExportDialog.setObjectName(u"SimulationExportDialog")
        SimulationExportDialog.resize(700, 800)
        SimulationExportDialog.setWindowFlags(Qt.Window|Qt.WindowCloseButtonHint|Qt.WindowMinimizeButtonHint)
        self.verticalLayout = QVBoxLayout(SimulationExportDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.scrollArea = QScrollArea(SimulationExportDialog)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.globalInfoGroup = QGroupBox(self.scrollAreaWidgetContents)
        self.globalInfoGroup.setObjectName(u"globalInfoGroup")
        self.formLayout = QFormLayout(self.globalInfoGroup)
        self.formLayout.setObjectName(u"formLayout")
        self.taskThroughputCheck = QCheckBox(self.globalInfoGroup)
        self.taskThroughputCheck.setObjectName(u"taskThroughputCheck")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.taskThroughputCheck)

        self.taskThroughputLabel = QLabel(self.globalInfoGroup)
        self.taskThroughputLabel.setObjectName(u"taskThroughputLabel")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.taskThroughputLabel)

        self.taskThroughputDesc = QLabel(self.globalInfoGroup)
        self.taskThroughputDesc.setObjectName(u"taskThroughputDesc")
        self.taskThroughputDesc.setWordWrap(True)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.taskThroughputDesc)


        self.verticalLayout_2.addWidget(self.globalInfoGroup)

        self.computeNodeGroup = QGroupBox(self.scrollAreaWidgetContents)
        self.computeNodeGroup.setObjectName(u"computeNodeGroup")
        self.verticalLayout_3 = QVBoxLayout(self.computeNodeGroup)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.computeNodeTabs = QTabWidget(self.computeNodeGroup)
        self.computeNodeTabs.setObjectName(u"computeNodeTabs")
        self.computeNodeTabs.setDocumentMode(False)

        self.verticalLayout_3.addWidget(self.computeNodeTabs)


        self.verticalLayout_2.addWidget(self.computeNodeGroup)

        self.taskInfoGroup = QGroupBox(self.scrollAreaWidgetContents)
        self.taskInfoGroup.setObjectName(u"taskInfoGroup")
        self.verticalLayout_4 = QVBoxLayout(self.taskInfoGroup)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.taskInfoTabs = QTabWidget(self.taskInfoGroup)
        self.taskInfoTabs.setObjectName(u"taskInfoTabs")
        self.taskInfoTabs.setDocumentMode(False)

        self.verticalLayout_4.addWidget(self.taskInfoTabs)


        self.verticalLayout_2.addWidget(self.taskInfoGroup)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout.addWidget(self.scrollArea)

        self.exportOptionsGroup = QGroupBox(SimulationExportDialog)
        self.exportOptionsGroup.setObjectName(u"exportOptionsGroup")
        self.gridLayout = QGridLayout(self.exportOptionsGroup)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label = QLabel(self.exportOptionsGroup)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.formatCombo = QComboBox(self.exportOptionsGroup)
        self.formatCombo.addItem("")
        self.formatCombo.addItem("")
        self.formatCombo.setObjectName(u"formatCombo")

        self.gridLayout.addWidget(self.formatCombo, 0, 1, 1, 1)

        self.label_2 = QLabel(self.exportOptionsGroup)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)

        self.pathEdit = QLineEdit(self.exportOptionsGroup)
        self.pathEdit.setObjectName(u"pathEdit")

        self.gridLayout.addWidget(self.pathEdit, 1, 1, 1, 1)

        self.browseButton = QPushButton(self.exportOptionsGroup)
        self.browseButton.setObjectName(u"browseButton")

        self.gridLayout.addWidget(self.browseButton, 1, 2, 1, 1)


        self.verticalLayout.addWidget(self.exportOptionsGroup)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.cancelButton = QPushButton(SimulationExportDialog)
        self.cancelButton.setObjectName(u"cancelButton")

        self.horizontalLayout.addWidget(self.cancelButton)

        self.exportButton = QPushButton(SimulationExportDialog)
        self.exportButton.setObjectName(u"exportButton")

        self.horizontalLayout.addWidget(self.exportButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(SimulationExportDialog)
        self.cancelButton.clicked.connect(SimulationExportDialog.reject)

        QMetaObject.connectSlotsByName(SimulationExportDialog)
    # setupUi

    def retranslateUi(self, SimulationExportDialog):
        SimulationExportDialog.setWindowTitle(QCoreApplication.translate("SimulationExportDialog", u"\u4eff\u771f\u7ed3\u679c\u5bfc\u51fa", None))
        self.globalInfoGroup.setTitle(QCoreApplication.translate("SimulationExportDialog", u"\u5168\u5c40\u6307\u6807", None))
        self.taskThroughputCheck.setText("")
        self.taskThroughputLabel.setText(QCoreApplication.translate("SimulationExportDialog", u"\u4efb\u52a1\u541e\u5410\u91cf: -", None))
        self.taskThroughputDesc.setText(QCoreApplication.translate("SimulationExportDialog", u"\u63cf\u8ff0\u4fe1\u606f", None))
        self.computeNodeGroup.setTitle(QCoreApplication.translate("SimulationExportDialog", u"\u8ba1\u7b97\u8282\u70b9\u6307\u6807", None))
        self.taskInfoGroup.setTitle(QCoreApplication.translate("SimulationExportDialog", u"\u4efb\u52a1\u6307\u6807", None))
        self.exportOptionsGroup.setTitle(QCoreApplication.translate("SimulationExportDialog", u"\u5bfc\u51fa\u9009\u9879", None))
        self.label.setText(QCoreApplication.translate("SimulationExportDialog", u"\u5bfc\u51fa\u683c\u5f0f:", None))
        self.formatCombo.setItemText(0, QCoreApplication.translate("SimulationExportDialog", u"CSV (.csv)", None))
        self.formatCombo.setItemText(1, QCoreApplication.translate("SimulationExportDialog", u"Excel (.xlsx)", None))

        self.label_2.setText(QCoreApplication.translate("SimulationExportDialog", u"\u5bfc\u51fa\u8def\u5f84:", None))
        self.browseButton.setText(QCoreApplication.translate("SimulationExportDialog", u"\u6d4f\u89c8...", None))
        self.cancelButton.setText(QCoreApplication.translate("SimulationExportDialog", u"\u53d6\u6d88", None))
        self.exportButton.setText(QCoreApplication.translate("SimulationExportDialog", u"\u5bfc\u51fa", None))
    # retranslateUi

