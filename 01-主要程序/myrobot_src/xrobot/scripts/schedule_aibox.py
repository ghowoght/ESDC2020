#!/usr/bin/env python3
# #-*- coding: UTF-8 -*- 

import socket
import time
import numpy as np
import subprocess

# 命令查询字典
cmds = {"mapping_semantic":"roslaunch xrobot test_mapping_and_semantic.launch", # 构建语义地图
                "navigation":"roslaunch xrobot test_navigation.launch", # 在地图中导航搜寻
                "nav_semantic":"roslaunch xrobot test_nav_and_semantic.launch", # 语义标注
                "stop":"python3 /home/robot/myrobot/src/xrobot/setup/hero_end.py"} # 停止

# time.sleep(2)


def send_cmd(cmd):
    ## 发送指令给机器人
    host = '192.168.3.7' # ip
    port = 8000 # 端口号
    address = (host, port)
    tcpClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 创建一个套接字
    tcpClient.connect(address) # 连接机器人

    tcpClient.send(cmd) # 发送指令
    data = tcpClient.recv(1024) #接收反馈值
    if data.decode() == b"ok":
        pass
    tcpClient.close() # 关闭连接


send_cmd(b'nav_semantic')

# 暂停10s
time.sleep(10)

send_cmd(b'stop')
