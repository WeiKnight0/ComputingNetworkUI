# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'set_channel.ui'
##
## Created by: Qt User Interface Compiler version 6.8.1
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(400, 300)
        self.horizontalLayoutWidget = QWidget(Form)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayoutWidget.setGeometry(QRect(60, 40, 231, 80))
        self.horizontalLayout = QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.bandwidthLabel = QLabel(self.horizontalLayoutWidget)
        self.bandwidthLabel.setObjectName(u"bandwidthLabel")

        self.horizontalLayout.addWidget(self.bandwidthLabel)

        self.bandwidthLine = QLineEdit(self.horizontalLayoutWidget)
        self.bandwidthLine.setObjectName(u"bandwidthLine")

        self.horizontalLayout.addWidget(self.bandwidthLine)

        self.horizontalLayoutWidget_2 = QWidget(Form)
        self.horizontalLayoutWidget_2.setObjectName(u"horizontalLayoutWidget_2")
        self.horizontalLayoutWidget_2.setGeometry(QRect(210, 239, 161, 51))
        self.horizontalLayout_2 = QHBoxLayout(self.horizontalLayoutWidget_2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.confirmButton = QPushButton(self.horizontalLayoutWidget_2)
        self.confirmButton.setObjectName(u"confirmButton")

        self.horizontalLayout_2.addWidget(self.confirmButton)

        self.cancelButton = QPushButton(self.horizontalLayoutWidget_2)
        self.cancelButton.setObjectName(u"cancelButton")

        self.horizontalLayout_2.addWidget(self.cancelButton)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.bandwidthLabel.setText(QCoreApplication.translate("Form", u"\u8bbe\u7f6e\u5e26\u5bbd\uff1a", None))
        self.confirmButton.setText(QCoreApplication.translate("Form", u"\u786e\u5b9a", None))
        self.cancelButton.setText(QCoreApplication.translate("Form", u"\u53d6\u6d88", None))
    # retranslateUi

