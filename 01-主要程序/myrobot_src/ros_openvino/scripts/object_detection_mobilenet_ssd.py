#!/usr/bin/env python3
# #-*- coding: UTF-8 -*- 
import sys
import numpy as np
import cv2
from os import system
import io, time
from os.path import isfile, join
import re

import socket

fps = ""
detectfps = ""
framecount = 0
detectframecount = 0
time1 = 0
time2 = 0

LABELS = ('background',
          'aeroplane', 'bicycle', 'bird', 'boat',
          'bottle', 'bus', 'car', 'cat', 'chair',
          'cow', 'diningtable', 'dog', 'horse',
          'motorbike', 'person', 'pottedplant',
          'sheep', 'sofa', 'train', 'tvmonitor')

camera_width = 640
camera_height = 480

# 读取参数
f = open("/home/ghowoght/workplace/myrobot/src/ros_openvino/config/model_01_config.txt", 'r')
xml_path = f.readline().split("\n")[0]
bin_path = f.readline().split("\n")[0]
PORT = int(f.readline())
print(xml_path)
print(bin_path)
# LABELS = f.readline().split(" ")
f.close()

net = cv2.dnn.readNet(xml_path, bin_path)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_MYRIAD)

try:
    HOST = ''
    # PORT = 8080
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
            t1 = time.perf_counter()
            # 接收标志数据
            data = client_socket.recv(1024)
            if data:
                # 通知客户端“已收到标志数据，可以发送图像数据”
                client_socket.send(b"ok")
                # 处理标志数据
                flag = data.decode().split(",")
                # 图像字节流数据的总长度
                total = int(flag[0])
                # 图像序号
                seq = int(flag[1])
                # 接收到的数据计数
                cnt = 0
                # 存放接收到的数据
                img_bytes = b""

                while cnt < total:
                    # 当接收到的数据少于数据总长度时，则循环接收图像数据，直到接收完毕
                    data = client_socket.recv(256000)
                    img_bytes += data
                    cnt += len(data)

                # 解析接收到的字节流数据，并显示图像
                img = np.asarray(bytearray(img_bytes), dtype="uint8")
                img = cv2.imdecode(img, cv2.IMREAD_COLOR)
        
                color_image = img

                height = color_image.shape[0]
                width = color_image.shape[1]

                blob = cv2.dnn.blobFromImage(color_image, 0.007843, size=(300, 300), mean=(127.5,127.5,127.5), swapRB=False, crop=False)
                net.setInput(blob)
                out = net.forward()
                out = out.flatten()
                # 返回的结果
                obj_result_data = []
                obj_cnt = 0
                obj_result_data.append(str(seq))
                for box_index in range(100):
                    if out[box_index + 1] == 0.0:
                        break
                    base_index = box_index * 7
                    if (not np.isfinite(out[base_index]) or
                        not np.isfinite(out[base_index + 1]) or
                        not np.isfinite(out[base_index + 2]) or
                        not np.isfinite(out[base_index + 3]) or
                        not np.isfinite(out[base_index + 4]) or
                        not np.isfinite(out[base_index + 5]) or
                        not np.isfinite(out[base_index + 6])):
                        continue

                    if box_index == 0:
                        detectframecount += 1

                    x1 = max(0, int(out[base_index + 3] * height))
                    y1 = max(0, int(out[base_index + 4] * width))
                    x2 = min(height, int(out[base_index + 5] * height))
                    y2 = min(width, int(out[base_index + 6] * width))

                    object_info_overlay = out[base_index:base_index + 7]

                    min_score_percent = 60
                    source_image_width = width
                    source_image_height = height

                    base_index = 0
                    class_id = object_info_overlay[base_index + 1]
                    percentage = int(object_info_overlay[base_index + 2] * 100)
                    if (percentage <= min_score_percent):
                        continue

                    box_left = int(object_info_overlay[base_index + 3] * source_image_width)
                    box_top = int(object_info_overlay[base_index + 4] * source_image_height)
                    box_right = int(object_info_overlay[base_index + 5] * source_image_width)
                    box_bottom = int(object_info_overlay[base_index + 6] * source_image_height)
                    label_text = LABELS[int(class_id)] + " (" + str(percentage) + "%)"

                    # 将检测结果添加到返回列表
                    obj_result_data.append(str(int(class_id)))
                    obj_result_data.append(str(box_left))
                    obj_result_data.append(str(box_top))
                    obj_result_data.append(str(box_right))
                    obj_result_data.append(str(box_bottom))
                    obj_cnt = obj_cnt + 1

                    # box_color = (255, 128, 0)
                    # box_thickness = 1
                    # cv2.rectangle(color_image, (box_left, box_top), (box_right, box_bottom), box_color, box_thickness)

                    # label_background_color = (125, 175, 75)
                    # label_text_color = (255, 255, 255)

                    # label_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                    # label_left = box_left
                    # label_top = box_top - label_size[1]
                    # if (label_top < 1):
                    #     label_top = 1
                    # label_right = label_left + label_size[0]
                    # label_bottom = label_top + label_size[1]
                    # cv2.rectangle(color_image, (label_left - 1, label_top - 1), (label_right + 1, label_bottom + 1), label_background_color, -1)
                    # cv2.putText(color_image, label_text, (label_left, label_bottom), cv2.FONT_HERSHEY_SIMPLEX, 0.5, label_text_color, 1)

                # cv2.putText(color_image, fps,       (width-170,15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (38,0,255), 1, cv2.LINE_AA)
                # cv2.putText(color_image, detectfps, (width-170,30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (38,0,255), 1, cv2.LINE_AA)

                # cv2.namedWindow('img', cv2.WINDOW_AUTOSIZE)
                # cv2.imshow('img', cv2.resize(color_image, (width, height)))

                # if cv2.waitKey(1)&0xFF == ord('q'):
                #     break

                # FPS calculation
                # framecount += 1
                # if framecount >= 15:
                #     fps       = "(Playback) {:.1f} FPS".format(time1/15)
                #     detectfps = "(Detection) {:.1f} FPS".format(detectframecount/time2)
                #     framecount = 0
                #     detectframecount = 0
                #     time1 = 0
                #     time2 = 0
                # t2 = time.perf_counter()
                # elapsedTime = t2-t1
                # time1 += 1/elapsedTime
                # time2 += elapsedTime

                # 通知客户端“已经接收完毕，可以开始下一帧图像的传输”
                obj_result_data.insert(0, str(obj_cnt))
                client_socket.send(bytes(" ".join(obj_result_data), encoding="utf-8"))
            else:
                print("已断开！")
                break

except:
    import traceback
    traceback.print_exc()

finally:

    print("\n\nFinished\n\n")

