# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'set_userRouter.ui'
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
from PySide6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(400, 300)
        self.horizontalLayoutWidget_2 = QWidget(Form)
        self.horizontalLayoutWidget_2.setObjectName(u"horizontalLayoutWidget_2")
        self.horizontalLayoutWidget_2.setGeometry(QRect(170, 239, 181, 51))
        self.horizontalLayout_2 = QHBoxLayout(self.horizontalLayoutWidget_2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.confirmButton = QPushButton(self.horizontalLayoutWidget_2)
        self.confirmButton.setObjectName(u"confirmButton")

        self.horizontalLayout_2.addWidget(self.confirmButton)

        self.cancelButton = QPushButton(self.horizontalLayoutWidget_2)
        self.cancelButton.setObjectName(u"cancelButton")

        self.horizontalLayout_2.addWidget(self.cancelButton)

        self.verticalGroupBox = QGroupBox(Form)
        self.verticalGroupBox.setObjectName(u"verticalGroupBox")
        self.verticalGroupBox.setGeometry(QRect(50, 20, 301, 181))
        self.verticalLayout = QVBoxLayout(self.verticalGroupBox)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.ip_label = QLabel(self.verticalGroupBox)
        self.ip_label.setObjectName(u"ip_label")
        font = QFont()
        font.setPointSize(7)
        self.ip_label.setFont(font)

        self.horizontalLayout.addWidget(self.ip_label)

        self.ip_lineEdit_1 = QLineEdit(self.verticalGroupBox)
        self.ip_lineEdit_1.setObjectName(u"ip_lineEdit_1")

        self.horizontalLayout.addWidget(self.ip_lineEdit_1)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.mask_label = QLabel(self.verticalGroupBox)
        self.mask_label.setObjectName(u"mask_label")

        self.horizontalLayout_5.addWidget(self.mask_label)

        self.mask_lineEdit_1 = QLineEdit(self.verticalGroupBox)
        self.mask_lineEdit_1.setObjectName(u"mask_lineEdit_1")

        self.horizontalLayout_5.addWidget(self.mask_lineEdit_1)


        self.verticalLayout.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.ip_label_2 = QLabel(self.verticalGroupBox)
        self.ip_label_2.setObjectName(u"ip_label_2")
        self.ip_label_2.setFont(font)

        self.horizontalLayout_3.addWidget(self.ip_label_2)

        self.ip_lineEdit_2 = QLineEdit(self.verticalGroupBox)
        self.ip_lineEdit_2.setObjectName(u"ip_lineEdit_2")

        self.horizontalLayout_3.addWidget(self.ip_lineEdit_2)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.mask_label_2 = QLabel(self.verticalGroupBox)
        self.mask_label_2.setObjectName(u"mask_label_2")

        self.horizontalLayout_4.addWidget(self.mask_label_2)

        self.mask_lineEdit_2 = QLineEdit(self.verticalGroupBox)
        self.mask_lineEdit_2.setObjectName(u"mask_lineEdit_2")

        self.horizontalLayout_4.addWidget(self.mask_lineEdit_2)


        self.verticalLayout.addLayout(self.horizontalLayout_4)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.confirmButton.setText(QCoreApplication.translate("Form", u"\u786e\u8ba4", None))
        self.cancelButton.setText(QCoreApplication.translate("Form", u"\u53d6\u6d88", None))
        self.ip_label.setText(QCoreApplication.translate("Form", u"\u9762\u5411\u8282\u70b9\u63a5\u53e3\u7684IP\u5730\u5740\uff1a", None))
        self.mask_label.setText(QCoreApplication.translate("Form", u"\u5b50\u7f51\u63a9\u7801\uff1a", None))
        self.ip_label_2.setText(QCoreApplication.translate("Form", u"\u9762\u5411\u5176\u4ed6\u8def\u7531\u5668\u63a5\u53e3\u7684IP\u5730\u5740", None))
        self.mask_label_2.setText(QCoreApplication.translate("Form", u"\u5b50\u7f51\u63a9\u7801\uff1a", None))
    # retranslateUi

