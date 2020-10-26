import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import qdarkstyle

# from mainWindow import MyMainWindow
from mainWindow import ShowMainWindow

# python3 convert-qrc.py && python3 convert-ui.py && python3 run.py 
# class QMainWindow(QMainWindow):
#     def closeEvent(self, event):
#         """
#         重写closeEvent方法，实现dialog窗体关闭时执行一些代码
#         :param event: close()触发的事件
#         :return: None
#         """
#         reply = QtWidgets.QMessageBox.question(self,
#                                                'Confirm',
#                                                "Do you wanna exit？",
#                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
#                                                QtWidgets.QMessageBox.No)
#         if reply == QtWidgets.QMessageBox.Yes:
#             event.accept()
#         else:
#             event.ignore()

# https://blog.csdn.net/u010139869/article/details/79449315
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    form = ShowMainWindow()
    # window = ShowMainWindow(form)
    # window = ShowMainWindow(form)
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
    
    form.show()
    sys.exit(app.exec_())
    # window.audio_widget.endAudio()
