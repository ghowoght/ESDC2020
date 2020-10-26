#!/usr/bin/env python3
# #-*- coding: UTF-8 -*- 

import pyaudio
import wave
import cv2

import SpeechRecognizer
# import SemanticAnalyzer
import SpeechSynthesis

import time
import threading
import numpy as np 
from matplotlib import pyplot as plt
import struct as st
from VAD import VAD

import socket
import time
import numpy as np
import subprocess

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

STATUS_WAITING_WAKE_UP = 0
STATUS_WAITING_FOR_COMMAND = 1
STATUS_WAITING_FOR_CONFIRM = 2
STATUS_WORKING = 3

WAKE_UP_WORDS = "小五小五"
wake_up_words_list = ["小五小五", "想我想我", "下午下午", "小武小武", "笑我笑我"]

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

def excu_server(svr):
    if svr in hero_cmds: # HERO
        send_cmd(svr)
        time.sleep(5)
    if svr in aibox_cmds: # AI-Box
        p = subprocess.Popen(cmds[svr], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in iter(p.stdout.readline, b''):
            print(line.decode())
        p.stdout.close()
        p.wait()
        if svr == "stop":
            # p.wait()
            SpeechSynthesis.speech_synthesis("已停止完毕，很高兴为您服务")


state = STATUS_WAITING_WAKE_UP
play_flag = False # 在进行语音播报时不进行其他操作，相当于一把🔓

CHUNK = 8000
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 3
WAVE_OUTPUT_FILENAME = "output.wav"

p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print("start recording")
last_index = 0
def si_thread(index, frame):
    ## 语音交互线程
    global state, play_flag, last_index
    
    # 语音识别
    sr = SpeechRecognizer.SpeechRecognizer(frame) 
    sr.recognize()
    print(sr.ws.result)
    if play_flag == False and index > last_index:
        
        if state == STATUS_WAITING_WAKE_UP: # 处于等待唤醒状态
            # if sr.ws.result == WAKE_UP_WORDS: # 唤醒词
            if sr.ws.result in wake_up_words_list:
                last_index = index
                state = STATUS_WAITING_FOR_COMMAND
                play_flag = True
                SpeechSynthesis.speech_synthesis("嗯，你好，请问您有什么吩咐")
                play_flag = False
        elif state == STATUS_WAITING_FOR_COMMAND: # 处于等待命令状态
            if sr.ws.result in servers:
                last_index = index
                state = STATUS_WORKING
                play_flag = True
                SpeechSynthesis.speech_synthesis("好的，正在" + sr.ws.result)
                play_flag = False
                
                state = STATUS_WAITING_WAKE_UP
                excu_server(servers_dict[sr.ws.result])

frames = []
cnt = 0
while True:
    if(state != STATUS_WORKING):
        # 读取语音的字节流
        data = stream.read(CHUNK)
        frames.append(data)
        if len(frames) > RECORD_SECONDS * RATE / CHUNK:
            del frames[0]
        
        datas = b''
        for i in range(len(frames)):
            datas = datas + frames[i]

        if len(datas) == RECORD_SECONDS * RATE * 2:
            # 字节流解码
            fmt = "<" + str(RECORD_SECONDS * RATE) + "h"
            data_decode = np.array(st.unpack(fmt, bytes(datas)))
            # print("-------------")
            # 语音端点检测
            isVoice, segments = VAD(data_decode, RATE)
            # print(isVoice)
            # 检测到声音，开启一个语音交互线程
            if isVoice:
                cnt = cnt + 1
                if play_flag == False:
                    t = threading.Thread(target=si_thread, args=(cnt, frames))
                    t.start()

stream.stop_stream()
stream.close()
p.terminate()
print("stop recording")