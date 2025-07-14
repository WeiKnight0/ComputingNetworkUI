# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'design_window.ui'
##
## Created by: Qt User Interface Compiler version 6.8.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QGraphicsView, QHBoxLayout, QListWidget,
    QListWidgetItem, QMainWindow, QMenu, QMenuBar,
    QSizePolicy, QStatusBar, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        self.actionsubmit = QAction(MainWindow)
        self.actionsubmit.setObjectName(u"actionsubmit")
        self.actionclear = QAction(MainWindow)
        self.actionclear.setObjectName(u"actionclear")
        self.actionsave = QAction(MainWindow)
        self.actionsave.setObjectName(u"actionsave")
        self.actionload = QAction(MainWindow)
        self.actionload.setObjectName(u"actionload")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.graphicsView = QGraphicsView(self.centralwidget)
        self.graphicsView.setObjectName(u"graphicsView")
        self.graphicsView.setAutoFillBackground(True)
        self.graphicsView.setStyleSheet(u"background-color: rgb(255, 255, 255);")
        brush = QBrush(QColor(0, 0, 0, 255))
        brush.setStyle(Qt.NoBrush)
        self.graphicsView.setBackgroundBrush(brush)
        brush1 = QBrush(QColor(0, 0, 0, 255))
        brush1.setStyle(Qt.NoBrush)
        self.graphicsView.setForegroundBrush(brush1)

        self.horizontalLayout.addWidget(self.graphicsView)

        self.listWidget = QListWidget(self.centralwidget)
        icon = QIcon()
        icon.addFile(u"icon/\u7528\u6237\u8282\u70b9.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        __qlistwidgetitem = QListWidgetItem(self.listWidget)
        __qlistwidgetitem.setIcon(icon);
        icon1 = QIcon()
        icon1.addFile(u"icon/\u7b97\u529b\u8282\u70b9.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        __qlistwidgetitem1 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem1.setIcon(icon1);
        icon2 = QIcon()
        icon2.addFile(u"icon/\u7528\u6237\u7f51\u5173.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        __qlistwidgetitem2 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem2.setIcon(icon2);
        icon3 = QIcon()
        icon3.addFile(u"icon/\u7b97\u529b\u7f51\u5173.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        __qlistwidgetitem3 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem3.setIcon(icon3);
        icon4 = QIcon()
        icon4.addFile(u"icon/\u8c03\u5ea6\u51b3\u7b56\u7f51\u5173.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        __qlistwidgetitem4 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem4.setIcon(icon4);
        icon5 = QIcon()
        icon5.addFile(u"icon/\u8def\u7531\u5668.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        __qlistwidgetitem5 = QListWidgetItem(self.listWidget)
        __qlistwidgetitem5.setIcon(icon5);
        self.listWidget.setObjectName(u"listWidget")
        self.listWidget.setMinimumSize(QSize(150, 0))
        self.listWidget.setMaximumSize(QSize(200, 16777215))

        self.horizontalLayout.addWidget(self.listWidget)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 21))
        self.menu = QMenu(self.menubar)
        self.menu.setObjectName(u"menu")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menu.menuAction())
        self.menu.addAction(self.actionsubmit)
        self.menu.addAction(self.actionclear)
        self.menu.addAction(self.actionsave)
        self.menu.addAction(self.actionload)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionsubmit.setText(QCoreApplication.translate("MainWindow", u"\u63d0\u4ea4", None))
        self.actionclear.setText(QCoreApplication.translate("MainWindow", u"\u6e05\u9664", None))
        self.actionsave.setText(QCoreApplication.translate("MainWindow", u"\u4fdd\u5b58\u7f51\u7edc", None))
        self.actionload.setText(QCoreApplication.translate("MainWindow", u"\u52a0\u8f7d\u7f51\u7edc", None))

        __sortingEnabled = self.listWidget.isSortingEnabled()
        self.listWidget.setSortingEnabled(False)
        ___qlistwidgetitem = self.listWidget.item(0)
        ___qlistwidgetitem.setText(QCoreApplication.translate("MainWindow", u"\u7528\u6237\u8282\u70b9", None));
        ___qlistwidgetitem1 = self.listWidget.item(1)
        ___qlistwidgetitem1.setText(QCoreApplication.translate("MainWindow", u"\u7b97\u529b\u8282\u70b9", None));
        ___qlistwidgetitem2 = self.listWidget.item(2)
        ___qlistwidgetitem2.setText(QCoreApplication.translate("MainWindow", u"\u7528\u6237\u7f51\u5173", None));
        ___qlistwidgetitem3 = self.listWidget.item(3)
        ___qlistwidgetitem3.setText(QCoreApplication.translate("MainWindow", u"\u7b97\u529b\u7f51\u5173", None));
        ___qlistwidgetitem4 = self.listWidget.item(4)
        ___qlistwidgetitem4.setText(QCoreApplication.translate("MainWindow", u"\u8c03\u5ea6\u51b3\u7b56\u7f51\u5173", None));
        ___qlistwidgetitem5 = self.listWidget.item(5)
        ___qlistwidgetitem5.setText(QCoreApplication.translate("MainWindow", u"\u8def\u7531\u5668", None));
        self.listWidget.setSortingEnabled(__sortingEnabled)

        self.menu.setTitle(QCoreApplication.translate("MainWindow", u"\u5f00\u59cb", None))
    # retranslateUi

