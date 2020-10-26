import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import os
import subprocess


class VisualTerminal(QWidget):
    """
        VisualTerminal
        ===
    """

    def __init__(self, parent=None):
        super(VisualTerminal, self).__init__(parent)

        '''layout'''
        '''布局管理'''
        self.layout_main = QVBoxLayout()  # 全局布局
        self.layout_input = QHBoxLayout()  # 输入框和按钮的布局

        '''display current working path'''
        '''显示当前的工作路径'''
        self.label_pwd = QLabel()  # button for run code
        self.layout_main.addWidget(self.label_pwd)

        '''display terminal returned information'''
        '''显示终端的返回结果'''
        self.edit_info = QTextEdit()  # return terminal
        self.layout_main.addWidget(self.edit_info)
        self.edit_info.setFocusPolicy(Qt.NoFocus)

        '''commond textbox'''
        '''代码输入框'''
        self.edit_cmd_input = QLineEdit()
        self.layout_input.addWidget(self.edit_cmd_input)

        # run button
        # 运行按钮
        self.button_run = QPushButton()
        self.layout_input.addWidget(self.button_run)
        self.button_run.setIcon(QIcon("./qt.png"))
        self.button_run.setText("run")

        self.layout_main.addLayout(self.layout_input)
        self.setLayout(self.layout_main)

        '''
            # signal and slot
        '''
        self.button_run.clicked.connect(self.run_cmd)

        

    def run_cmd(self):

        info_text = "[cwd]  "+os.getcwd()
        self.label_pwd.setText(info_text)

        cmd = self.edit_cmd_input.text()

        # Start
        proc_return = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        result = proc_return.stdout.read().decode('utf-8')

        print(result)
        self.edit_info.setPlainText(result)
        self.edit_cmd_input.clear()
        proc_return.stdout.close()
        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = VisualTerminal()
    form.show()
    sys.exit(app.exec_())
