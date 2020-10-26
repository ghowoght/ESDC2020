import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from mainWin_base import Ui_MainWindow
from subWidget.matplotlibwidget.MatplotlibWidget import MatplotlibWidget
from subWidget.timewidget.ShowTimeWidget import DisplayFullTimeWidget
from subWidget.terminal.terminal_lsusb import VisualTerminalLsusb


import styleSheet

import socket

import subprocess
import os
import time
import threading

# class MyMainWindow(Ui_MainWindow):
#     """
#     docstringsi_thread
#     """
#     def __init__(self, mainWindow):
#         super().setupUi(mainWindow)
#         # self.retranslateUi(mainWindow)
#         # self.centralwidget.setStyle(QStyle)

#         # ---------------------------------
#         #   Time
#         # ---------------------------------
#         # self.timeShow=ShowTimeWidget()
#         # self.verticalLayout_audio.addWidget(self.timeShow)


#         # ---------------------------------
#         #   audio widget
#         # ---------------------------------
#         self.audio_widget = MatplotlibWidget()
#         self.audio_widget.startAudio()
#         # self.widget_audio = QtWidgets.QWidget(self.audio_widget)
#         # self.widget_audio.setObjectName("widget_audio")
#         self.verticalLayout_audio.addWidget(self.audio_widget)

#         self.button_startwave.clicked.connect(self.start_audio)
#         self.button_stopwave.clicked.connect(self.stop_audio)


#         # ---------------------------------
#         #   process 
#         # ---------------------------------
#         self.process_build=QProcess()
#         self.button_startprocess.clicked.connect(self.start_process)
#         self.button_startprocess.clicked.connect(self.start_process)


#         self.process_kill=QProcess()
#         self.button_stopprocess.clicked.connect(self.stop_process)

#         # ---------------------------------
#         #   terminal
#         # ---------------------------------
#         self.terminal=VisualTerminalLsusb()
#         self.verticalLayout_2.addWidget(self.terminal)

#     #     self.center()    
#     # def center(self,mainWIn):
#     #     screen=QDesktopWidget().screenGeometry()
#     #     size=self.centralwidget.geometry()
#     #     self.centralwidget.move((screen.width()-size.width())/2,(screen.height()-size.height())/2)


#     """
#         slot
#     """
#     def start_audio(self):
#         self.audio_widget.startAudio()
#     def stop_audio(self):
#         self.audio_widget.endAudio()

#     def start_process(self):       
#         # self.process_build.start('./hello',[])
#         self.process_build.start('whereis python',[])
#         output_btye=self.process_build.readAllStandardOutput().data()
#         # output=str(output_btye, encoding='u8')
#         print("[INFO]","shell kill")
#         print("[PROCESS firefox]",output_btye)
        
#     def stop_process(self):
#         # self.process_build.start('./hello',[])
#         self.process_kill.start('code',[])
#         output_btye=self.process_kill.readAll()
#         output=str(output_btye, encoding='u8')
#         print("[INFO]","shell kill")
#         print("[PROCESS code]",output)


class ShowMainWindow(QWidget):
    def __init__(self):
        super(ShowMainWindow,self).__init__()
        self._initUI()
        self._widget_displayWave.startAudio()
        self._initSignalSlot()
    def __del__(self):
        self._widget_displayWave.endAudio()
        print("[INFO]","delete this object:",self)

    def _initUI(self):
        self._layout_main=QHBoxLayout()

        '''
            _layout_buttonList
        '''
        self._layout_buttonList=QVBoxLayout()        

        # button for Stop Search
        self._button_StopSearch=QPushButton()        
        self._button_StopSearch.setText("关闭机器人")

        # button for Close Robot
        self._button_CloseRobot=QPushButton()        
        self._button_CloseRobot.setText("打开RVIZ")

        # button for Start search
        self._button_StartSearch=QPushButton()        
        self._button_StartSearch.setText("开始搜寻")

        '''
            _layout_displayList
        '''
        self._layout_displayList=QVBoxLayout()

        # display current time
        self._widget_displayTime=DisplayFullTimeWidget()
        

        # display wave from
        self._widget_displayWave=MatplotlibWidget()

        # display voice result
        self._widget_displayVoiceResult=QTextBrowser() 
        self.timer=QTimer()        
                   
        
        '''
            layout management
        '''
        # _layout_buttonList        
        self._layout_buttonList.addWidget(self._button_StopSearch)
        self._layout_buttonList.addStretch(1)
        self._layout_buttonList.addWidget(self._button_CloseRobot)
        self._layout_buttonList.addStretch(1)
        self._layout_buttonList.addWidget(self._button_StartSearch)
        self._layout_buttonList.addStretch(20)

        # _layout_displayList    
        self._layout_displayList.addWidget(self._widget_displayTime)    
        self._layout_displayList.addWidget(self._widget_displayWave)    
        self._layout_displayList.addWidget(self._widget_displayVoiceResult)           

        # _main layout
        self.setLayout(self._layout_main)
        self._layout_main.addLayout(self._layout_buttonList)
        self._layout_main.addLayout(self._layout_displayList)

    def _initSignalSlot(self):
        self.timer.timeout.connect(self._Slot_show_info)
        self.timer.start(100) # timer interval(ms)/frequency(kHz)  
        self._button_StopSearch.clicked.connect(self._Slot_stop_robot)
        self._button_CloseRobot.clicked.connect(self._Slot_open_rviz)
        self._button_StartSearch.clicked.connect(self._Slot_start_search)


    def _Slot_stop_robot(self):
        """
            触发“关闭机器人”按钮后的操作
        """
        # -----------------------------
        #   添加其他操作:
        self.send_cmd("stop")
        print("关闭完成")
        # -----------------------------
        # currentTime=self._widget_displayTime.get_currentTime()
        # tYear = currentTime[0]
        # tTime = currentTime[1]
        # tWeek = currentTime[2]
        # timeDisplay="%s-%s-%s %s:%s:%s %s"%(tYear[0],tYear[1],tYear[2],tTime[0],tTime[1],tTime[2],tWeek)
        # outputInfo =timeDisplay+"\n" \
        #     +"[INFO] stoping searching"
        # self._print_result(outputInfo)

    def _Slot_open_rviz(self):
        """
            触发“打开RVIZ”按钮后的操作
        """
        # -----------------------------
        #   添加其他操作:
        # p = subprocess.Popen("roslaunch xrobot rviz.launch", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # for line in iter(p.stdout.readline, b''):
        #     print(line.decode())
        # p.stdout.close()
        # p.wait()
        t = threading.Thread(target=self.rviz_thread)
        t.start()
        # -----------------------------
        # currentTime=self._widget_displayTime.get_currentTime()
        # tYear = currentTime[0]
        # tTime = currentTime[1]
        # tWeek = currentTime[2]
        # timeDisplay="%s-%s-%s %s:%s:%s %s"%(tYear[0],tYear[1],tYear[2],tTime[0],tTime[1],tTime[2],tWeek)
        # outputInfo =timeDisplay+"\n" \
        #     +"[INFO] closing robot"
        # self._print_result(outputInfo)

    def _Slot_start_search(self):
        """
            触发“start search”按钮后的操作
        """
        # -----------------------------
        #   添加其他操作:
        ## 关闭explore节点
        p = subprocess.Popen("ps -aux | grep explore_lite/explore", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.wait()
        result = p.stdout.readline().decode('utf-8').split(" ")
        pid = list(filter(None, result))[1]
        os.system("kill " + pid)
        time.sleep(1)
        print("explore shutdown ok")
        t = threading.Thread(target=self.search_thread)
        t.start()
        ## 重启explore节点
        # p = subprocess.Popen("roslaunch explore_lite explore_costmap.launch", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # for line in iter(p.stdout.readline, b''):
        #     print(line.decode())
        # p.stdout.close()
        # p.wait()
        # p = subprocess.run("roslaunch explore_lite explore_costmap.launch", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # -----------------------------
        # currentTime=self._widget_displayTime.get_currentTime()
        # tYear = currentTime[0]
        # tTime = currentTime[1]
        # tWeek = currentTime[2]
        # timeDisplay="%s-%s-%s %s:%s:%s %s"%(tYear[0],tYear[1],tYear[2],tTime[0],tTime[1],tTime[2],tWeek)
        # outputInfo =timeDisplay+"\n" \
        #     +"[INFO] start searching"
        # self._print_result(outputInfo)
        
    def _Slot_show_info(self):
        from subWidget.matplotlibwidget.MatplotlibWidget import state
        # print("[INFO]",state)
        outputInfo=""
        if state==0:
            outputInfo='正在等待唤醒'
        elif state==1:
            outputInfo='已唤醒，正在等待命令...'
        else:
            outputInfo=""
        self._print_result(outputInfo)
        


    def _print_result(self,info:str):
        self._widget_displayVoiceResult.setPlainText(info+"\n")
        self._widget_displayVoiceResult.moveCursor(self._widget_displayVoiceResult.textCursor().End)


    """
        Other Function
    """
    def rviz_thread(self):
        p = subprocess.Popen("roslaunch xrobot rviz.launch", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in iter(p.stdout.readline, b''):
            print(line.decode())
        p.stdout.close()
        p.wait()
    def search_thread(self):
        # 重启explore节点
        p = subprocess.Popen("roslaunch explore_lite explore_costmap.launch", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in iter(p.stdout.readline, b''):
            print(line.decode())
        p.stdout.close()
        p.wait()
    def send_cmd(self, cmd):
        ## 发送指令给机器人
        host = '192.168.3.7' # ip
        port = 8000 # 端口号
        address = (host, port)
        tcpClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 创建一个套接字
        tcpClient.connect(address) # 连接机器人

        tcpClient.send(bytes(cmd, encoding="utf-8")) # 发送指令
        data = tcpClient.recv(1024) #接收反馈值
        if data.decode() == b"ok":
            pass
        tcpClient.close() # 关闭连接