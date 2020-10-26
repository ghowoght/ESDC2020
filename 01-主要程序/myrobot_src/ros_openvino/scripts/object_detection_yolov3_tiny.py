#!/usr/bin/env python3
# #-*- coding: UTF-8 -*- 

import cv2
import argparse
import sys
import numpy as np
import os.path

import socket
import time
 
confThreshold = 0.5
nmsThreshold = 0.4
inpWidth = 416
inpHeight = 416
 
# classesFile = "./conf/obj.names"
# classes = None
# with open(classesFile, 'rt') as f:
#     classes = f.read().rstrip('\n').split('\n')

# 读取参数
f = open("/home/robot/myrobot/src/ros_openvino/config/model_yolo_tiny_config.txt", 'r')
cfg_path = f.readline().split("\n")[0]
weights_path = f.readline().split("\n")[0]
names_path = f.readline().split("\n")[0]
ff = open(names_path, 'r')
classes = ff.read().split("\n")
ff.close()
PORT = int(f.readline())

f.close()
 
modelConfiguration = cfg_path
# modelWeights = "./backup-tiny-all/yolov3-tiny_21000.weights"
modelWeights = weights_path

# modelConfiguration = "./conf/yolov3.cfg"
# modelWeights = "./yolov3_67000.weights"

net = cv2.dnn.readNetFromDarknet(modelConfiguration, modelWeights)
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_INFERENCE_ENGINE)
# net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_MYRIAD)

def drawPred(classId, conf, left, top, right, bottom):
    cv2.rectangle(frame, (left, top), (right, bottom), (255, 178, 50), 3)
    #print("classId : {}".format(classId))
    label = '%.2f' % conf
    if classes:
        assert (classId < len(classes))
        label = '%s:%s' % (classes[classId], label)
 
    labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    top = max(top, labelSize[1])
    cv2.rectangle(frame, (left, top - round(1.5*labelSize[1])), (left + round(1.5*labelSize[0]), top + baseLine),
                  (255, 255, 255), cv2.FILLED)
    cv2.putText(frame, label, (left, top), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 1)
 
def postprocess(frame, outs):
    frameHeight = frame.shape[0]
    frameWidth = frame.shape[1]
 
    classIds = []
    confidences = []
    boxes = []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            classId = np.argmax(scores)
            confidence = scores[classId]
            if confidence > confThreshold:
                center_x = int(detection[0] * frameWidth)
                center_y = int(detection[1] * frameHeight)
                width = int(detection[2] * frameWidth)
                height = int(detection[3] * frameHeight)
                left = int(center_x - width / 2)
                top = int(center_y - height / 2)
                classIds.append(classId)
                confidences.append(float(confidence))
                boxes.append([left, top, width, height])
 
    indices = cv2.dnn.NMSBoxes(boxes, confidences, confThreshold, nmsThreshold)
    for i in indices:
        i = i[0]
        box = boxes[i]
        left = box[0]
        top = box[1]
        width = box[2]
        height = box[3]
        drawPred(classIds[i], confidences[i], left, top, left + width, top + height)
 
# winName = 'YOLO in OpenCV'
# cv2.namedWindow(winName, cv2.WINDOW_NORMAL)
 
 
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
        
                frame = img

                blob = cv2.dnn.blobFromImage(frame, 1/255, (inpWidth, inpHeight), [0, 0, 0], swapRB=True, crop=False)
                net.setInput(blob)
                outs = net.forward(net.getUnconnectedOutLayersNames())
                # 返回的结果
                obj_result_data = []
                obj_cnt = 0
                obj_result_data.append(str(seq))
                ####################################################
                frameHeight = frame.shape[0]
                frameWidth = frame.shape[1]
            
                classIds = []
                confidences = []
                boxes = []
                for out in outs:
                    for detection in out:
                        scores = detection[5:]
                        classId = np.argmax(scores)
                        confidence = scores[classId]
                        if confidence > confThreshold:
                            center_x = int(detection[0] * frameWidth)
                            center_y = int(detection[1] * frameHeight)
                            width = int(detection[2] * frameWidth)
                            height = int(detection[3] * frameHeight)
                            left = int(center_x - width / 2)
                            top = int(center_y - height / 2)
                            classIds.append(classId)
                            confidences.append(float(confidence))
                            boxes.append([left, top, width, height])
                            # 将检测结果添加到返回列表
                            obj_result_data.append(str(int(classId)))
                            obj_result_data.append(str(left))
                            obj_result_data.append(str(top))
                            obj_result_data.append(str(left + width))
                            obj_result_data.append(str(top + height))
                            obj_cnt = obj_cnt + 1
                            
                obj_result_data.insert(0, str(obj_cnt))
                client_socket.send(bytes(" ".join(obj_result_data), encoding="utf-8"))

                indices = cv2.dnn.NMSBoxes(boxes, confidences, confThreshold, nmsThreshold)
                for i in indices:
                    i = i[0]
                    box = boxes[i]
                    left = box[0]
                    top = box[1]
                    width = box[2]
                    height = box[3]
                    drawPred(classIds[i], confidences[i], left, top, left + width, top + height)

                ###########################################################
                t, _ = net.getPerfProfile()
                # label = 'Inference time: %.2f ms' % (t * 1000.0 / cv2.getTickFrequency())
                # cv2.putText(frame, label, (0, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255))
            
                # cv2.imshow(winName, frame)
except:
    import traceback
    traceback.print_exc()

finally:
    print("\n\nFinished\n\n")