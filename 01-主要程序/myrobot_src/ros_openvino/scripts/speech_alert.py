#!/usr/bin/env python3
# #-*- coding: UTF-8 -*- i
import SpeechSynthesis
import socket

speech_word = {"cola":"可乐", "maid":"果粒橙", "sprite":"雪碧"}

try:
    HOST = ''
    PORT = 9000
    ADDRESS = (HOST, PORT)
    # 创建一个套接字
    tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 绑定本地ip
    tcpServer.bind(ADDRESS)
    # 开始监听
    tcpServer.listen(5)
    while True:
        # print("等待连接……")
        client_socket, client_address = tcpServer.accept()
        # print("连接成功！")
        SpeechSynthesis.speech_synthesis("已连接成功")
        while True:
            # 接收标志数据
            data = client_socket.recv(1024)
            if data:
                if data.decode() == "996":
                    SpeechSynthesis.speech_synthesis("已开始返回")
                    client_socket.send(b"ok")
                    continue
                if data.decode() == "997":
                    SpeechSynthesis.speech_synthesis("已返回完毕")
                    client_socket.send(b"ok")
                    continue
                if data.decode() == "998":
                    SpeechSynthesis.speech_synthesis("已开始搜寻")
                    client_socket.send(b"ok")
                    continue
                if data.decode() == "999":
                    SpeechSynthesis.speech_synthesis("已搜寻完毕")
                    client_socket.send(b"ok")
                    continue
                flag = data.decode().split("\r")[0]
                SpeechSynthesis.speech_synthesis("已发现" + speech_word[flag])
                client_socket.send(b"ok")
            else:
                break
except:
    import traceback
    traceback.print_exc()

finally:

    print("\n\nFinished\n\n")