#!/usr/bin/env python3
# #-*- coding: UTF-8 -*- 

import socket
import time
import numpy as np
import subprocess
import threading

# ## 关闭ROS master节点
# p = subprocess.Popen("ps -aux | grep /opt/ros/melodic/bin/rosmaster", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
# result = p.stdout.readline().decode('utf-8').split(" ")
# pid = list(filter(None, result))[1]
# import os
# os.system("kill " + pid)

cmds = {"mapping_semantic":"roslaunch xrobot test_mapping_and_semantic.launch", # 构建语义地图
                "navigation":"roslaunch xrobot test_navigation.launch", # 在地图中导航搜寻
                "nav_semantic":"roslaunch xrobot test_nav_and_semantic.launch", # 语义标注
                "stop":"python3 /home/robot/myrobot/src/xrobot/setup/hero_end.py"} # 停止

def server_thread(cmd):
    p = subprocess.Popen(cmds[cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # p.wait()
    # print(p.stdout.read().decode())
    for line in iter(p.stdout.readline, b''):
        print(line.decode())
    p.stdout.close()
    p.wait()

try:
    HOST = '192.168.3.7'
    PORT = 8000
    ADDRESS = (HOST, PORT)
    # 创建一个套接字
    tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 绑定本地ip
    tcpServer.bind(ADDRESS)
    # 开始监听
    tcpServer.listen(5)

    while True:
        print("等待连接……")
        client_socket, client_address = tcpServer.accept()
        print("连接成功！")

        while True:
            data = client_socket.recv(1024)
            if data:
                client_socket.send(b"ok")
                print(data.decode())
                t = threading.Thread(target=server_thread, args=(data.decode(),))
                t.start()
                #p = subprocess.Popen(cmds[data.decode()], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            else:
               print("已断开！")
               break
            
                
except:
    import traceback
    traceback.print_exc()
finally:
    print("\n\nFinished\n\n")