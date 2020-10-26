import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import os
import subprocess
from pprint import pprint


class VisualTerminalLsusb(QWidget):
    """
        VisualTerminalLsusb
        ===
    """

    def __init__(self, parent=None):
        super(VisualTerminalLsusb, self).__init__(parent)

        '''layout'''
        '''布局管理'''
        layout_main = QVBoxLayout()  # 全局布局
        layout_input = QHBoxLayout()  # 输入框和按钮的布局

        '''display current working path'''
        '''显示当前的工作路径'''
        self.label_pwd = QLabel()  # button for run code
        layout_main.addWidget(self.label_pwd)

        '''display terminal returned information'''
        '''显示终端的返回结果'''
        self.edit_info = QTextEdit()  # return terminal
        layout_main.addWidget(self.edit_info)
        self.edit_info.setFocusPolicy(Qt.NoFocus)


        '''
            run button
            运行按钮
        '''
        self.button_run = QPushButton()
        layout_input.addWidget(self.button_run)
        self.button_run.setIcon(QIcon("./qt.png"))
        self.button_run.setText("run")

        layout_main.addLayout(layout_input)
        self.setLayout(layout_main)

        '''
            signal and slot
        '''
        self.button_run.clicked.connect(self.run_cmd)


    def run_cmd(self):
        '''
            Slot
            -----            
        '''
        info_text = "[cwd]  "+os.getcwd()
        self.label_pwd.setText(info_text)

        cmd = "lsusb"

        # Start
        proc_return = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        result = proc_return.stdout.read().decode('utf-8')
        self.edit_info.setPlainText(result)
        proc_return.stdout.close()

        print(result)
        list_result=result.split('\n')
        pprint(list_result)        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = VisualTerminalLsusb()
    with open("./terminal.qss",'r') as fQss:
        form.setStyleSheet(fQss.read())
    form.show()
    sys.exit(app.exec_())

