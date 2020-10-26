#!/usr/bin/env python3
# #-*- coding: UTF-8 -*- 
import numpy as np
from scipy import signal
import matplotlib.animation as animation
import matplotlib.lines as line
import queue
import threading
import pyaudio
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QSizePolicy, QWidget
from PyQt5 import QtCore
import sys
import matplotlib
matplotlib.use("Qt5Agg")
'''导入依赖库'''
import struct as st
import time
from .VAD import VAD
from .SpeechRecognizer import SpeechRecognizer
from .SpeechSynthesis import speech_synthesis
import socket
import subprocess



speech_synthesis("你好，我是小五")

# CHUNK = 1024  # 定义数据流块
# WIDTH = 2
# CHANNELS = 2
# RATE = 16000 # sample 
# CHUNK = 512  # 定义数据流块
# WIDTH = 2
# CHANNELS = 2
# RATE = 16000 # sample 

#######################################################################
'''更改音频流格式'''
CHUNK = 500
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 3

'''参数设置'''
STATUS_WAITING_WAKE_UP = 0
STATUS_WAITING_FOR_COMMAND = 1
STATUS_WAITING_FOR_CONFIRM = 2
STATUS_WORKING = 3
WAKE_UP_WORDS = "小五小五"
wake_up_words_list = ["小五小五", "想我想我", "下午下午", "小武小武", "笑我笑我", "我想我"]
hero_cmds = ["mapping_semantic", "navigation", "nav_semantic", "stop"]
aibox_cmds = ["mapping_semantic", "navigation", "nav_semantic", "stop", "return_origin"]

servers = ["搜寻目标", "构建语义地图", "构建地图", "返回原点", "返回起点", "停止键图", 
                    "停止搜寻", "停止建图", "查询时间", "停止见图", "开始导航", "停止导航"]
servers_dict = {"搜寻目标" : "nav_semantic", 
                                "构建语义地图" : "mapping_semantic", 
                                "构建地图" : "mapping_semantic", 
                                "开始导航" : "navigation", 
                                "返回原点" : "return_origin", 
                                "返回起点" : "return_origin", 
                                "停止搜寻" : "stop", 
                                "停止导航" : "stop", 
                                "停止建图" : "stop", 
                                "停止键图" : "stop", 
                                "停止见图" : "stop", 
                                "查询时间" : ""}
# 命令查询字典 AI-Box端
cmds = {"mapping_semantic":"roslaunch xrobot aibox_mapping_and_semantic.launch", # 构建语义地图
                "navigation":"roslaunch xrobot aibox.launch", # 在地图中定点导航
                "nav_semantic":"roslaunch xrobot aibox_nav_semantic.launch", # 在地图中语义标注
                "return_origin":"python /home/uzei/myrobot/src/xrobot/scripts/ReturnOrigin.py",
                "stop":"python3 /home/uzei/myrobot/src/xrobot/setup/aibox_end.py"} # 停止

def send_cmd(cmd):
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

def excu_server(svr):
    if svr in hero_cmds:
        send_cmd(svr)
        time.sleep(5)
    if svr in aibox_cmds:
        p = subprocess.Popen(cmds[svr], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # p = subprocess.run(cmds[svr], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in iter(p.stdout.readline, b''):
            print(line.decode())
        p.stdout.close()
        p.wait()
        if svr == "stop":
            # p.wait()
            speech_synthesis("已停止完毕，很高兴为您服务")

state = STATUS_WAITING_WAKE_UP
play_flag = False # 在进行语音播报时不进行其他操作，相当于一把🔓
last_index = 0
def si_thread(index, frame):
    ## 语音交互线程
    global state, play_flag, last_index
    
    # 语音识别
    sr = SpeechRecognizer(frame) 
    sr.recognize()
    # print(str(index) + " " + str(last_index) + " " + sr.ws.result)
    print(sr.ws.result)
    if play_flag == False and index > last_index:
        
        if state == STATUS_WAITING_WAKE_UP: # 处于等待唤醒状态
            # if sr.ws.result == WAKE_UP_WORDS: # 唤醒词
            if sr.ws.result in wake_up_words_list:
                last_index = index
                state = STATUS_WAITING_FOR_COMMAND
                play_flag = True
                speech_synthesis("嗯，你好，请问您有什么吩咐")
                play_flag = False
        elif state == STATUS_WAITING_FOR_COMMAND: # 处于等待命令状态
            if sr.ws.result in servers:
                last_index = index
                state = STATUS_WORKING
                play_flag = True
                speech_synthesis("好的，正在" + sr.ws.result)
                # excu_server(servers_dict[sr.ws.result])
                play_flag = False
                
                state = STATUS_WAITING_WAKE_UP
                excu_server(servers_dict[sr.ws.result])
        # print("[INFO][mat]",state)

#######################################################################

class MyMplCanvas(FigureCanvas):
    """FigureCanvas的最终的父类其实是QWidget。"""

    def __init__(self, parent=None, width=5, height=4, dpi=100):

        # 配置中文显示
        # plt.rcParams['font.family'] = ['SimHei']  # 用来正常显示中文标签
        # plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

        # 此处初始化子图一定要在初始化函数之前
        self.fig = plt.figure()
        self.fig.patch.set_alpha(0)
        self.rt_ax = plt.subplot(111, xlim=(0, CHUNK*1), ylim=(-20000, 20000))
        plt.axis('off')

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        '''定义FigureCanvas的尺寸策略，这部分的意思是设置FigureCanvas，使之尽可能的向外填充空间。'''
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


class MatplotlibWidget(QWidget):
    def __init__(self, parent=None):
        super(MatplotlibWidget, self).__init__(parent)
        self.initUi()
        self.initariateV()

    def initUi(self):
        self.layout = QVBoxLayout(self)
        self.mpl = MyMplCanvas(self, width=15, height=15, dpi=100)
        self.layout.addWidget(self.mpl)

    # 初始化成员变量
    def initariateV(self):
        self.p = None
        self.q = queue.Queue()
        self.t = None
        self.ad_rdy_ev = None
        self.stream = None
        self.window = None
        self.ani = None
        self.rt_line = line.Line2D(xdata=[], ydata=[],linewidth=1,color='#FFB6C1')  # 直线对象

        self.rt_x_data = np.arange(0, CHUNK*1, 1)
        self.rt_data = np.full((CHUNK*1, ), 0)
        self.rt_line.set_xdata(self.rt_x_data)  # 初始化横坐标
        self.rt_line.set_ydata(self.rt_data)  # 初始化纵坐标

    # 开始录制触发函数

    def startAudio(self, *args, **kwargs):
        # self.mpl.fig.suptitle('audio wave')
        self.ani = animation.FuncAnimation(
            self.mpl.fig, self.plot_update,
            init_func=self.plot_init,
            frames=1,
            interval=10,
            blit=True)
        # 其实animation方格式法的实质是开启了一个线程更新图像

        # 麦克风开始获取音频
        self.p = pyaudio.PyAudio()
        '''更改音频流格式'''
        # 打开数据流
        # self.stream = self.p.open(
        #     format=pyaudio.paInt16,
        #     channels=CHANNELS,
        #     rate=RATE,
        #     input=True,
        #     output=False,
        #     frames_per_buffer=CHUNK,
        #     stream_callback=self.callback)
        self.stream = self.p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                stream_callback=self.callback)
        self.stream.start_stream()

        # 正态分布数组，与音频数据做相关运算可保证波形图两端固定
        '''单通道*1'''
        self.window = signal.hamming(CHUNK*1)

        # 初始化线程
        self.ad_rdy_ev = threading.Event()  # 线程事件变量
        self.t = threading.Thread(
            target=self.read_audio_thead,
            args=(self.q, self.stream, self.ad_rdy_ev))  # 在线程t中添加函数read_audio_thead
        self.t.start()  # 线程开始运行
        self.mpl.draw()

        # animation的更新函数
    def plot_update(self, i):
        self.rt_line.set_xdata(self.rt_x_data)
        self.rt_line.set_ydata(self.rt_data)
        return self.rt_line,

    # animation的初始化函数
    def plot_init(self):
        self.mpl.rt_ax.add_line(self.rt_line)
        return self.rt_line,

    # pyaudio的回调函数
    def callback(self, in_data, frame_count, time_info, status):
        global ad_rdy_ev
        self.q.put(in_data)
        return (None, pyaudio.paContinue)
    frames = []
    cnt = 0
    def read_audio_thead(self, q, stream, ad_rdy_ev):
        # # 获取队列中的数据
        # while stream.is_active():
        #     self.ad_rdy_ev.wait(timeout=0.05)  # 线程事件，等待0.1s
        #     if not q.empty():
        #         data = q.get()
        #         while not q.empty():  # 将多余的数据扔掉，不然队列会越来越长
        #             q.get()
        #         self.rt_data = np.frombuffer(data, np.dtype('<i2'))
        #         self.rt_data = self.rt_data * self.window   # 这样做的目的是将曲线的两端固定，以免出现曲线整体发生波动
        #     self.ad_rdy_ev.clear()
        while stream.is_active():
            # print("ok")
            if not q.empty():
                data = q.get()
                self.frames.append(data)
                self.cnt = self.cnt + 1

                fmt = "<" + str(CHUNK) + "h"
                self.rt_data = np.array(st.unpack(fmt, bytes(data)), dtype=float)
                self.rt_data = self.rt_data * self.window   # 这样做的目的是将曲线的两端固定，以免出现曲线整体发生波动
                if len(self.frames) > RECORD_SECONDS * RATE / CHUNK:
                    del self.frames[0]
                datas = b''
                frames_new = []
                for i in range(len(self.frames)):
                    datas = datas + self.frames[i]
                    if i % 10 == 0:
                        frames_new.append(self.frames[i])
                    else:
                        frames_new[len(frames_new) - 1] = frames_new[len(frames_new) - 1] + self.frames[i]
                if len(datas) == RECORD_SECONDS * RATE * 2 and self.cnt % 10 == 0:
                    # 字节流解码
                    fmt = "<" + str(RECORD_SECONDS * RATE) + "h"
                    data_decode = np.array(st.unpack(fmt, bytes(datas)))
                    # print("-------------")
                    # 语音端点检测
                    isVoice, segments = VAD(data_decode, RATE)
                    # print(isVoice)
                    # 检测到声音，开启一个语音交互线程
                    if isVoice:
                        # self.cnt = self.cnt + 1
                        if play_flag == False:
                            t = threading.Thread(target=si_thread, args=(self.cnt, frames_new))
                            t.start()


    def endAudio(self):
        # 停止获取音频信息
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        # 清空队列
        while not self.q.empty():
            self.q.get()
        # 重新初始化变量
        self.initariateV()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = MatplotlibWidget()
    ui.startAudio()
    ui.show()
    sys.exit(app.exec_())
