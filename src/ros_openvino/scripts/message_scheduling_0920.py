#!/usr/bin/env python
# #-*- coding: UTF-8 -*- 
# 消息调度 实现Python3和ROS的通信

#!/usr/bin/env python
import cv2
import rospy
from sensor_msgs.msg import CompressedImage
from tf import TransformListener
import os, sys
import threading
from cv_bridge import CvBridge,CvBridgeError

import time
import socket
import numpy as np

HOST = ''
PORT = 8080
ADDRESS = (HOST, PORT)
tcpClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpClient.connect(ADDRESS)

LABELS = ("person", "bicycle", "car", "motorbike", "aeroplane",
          "bus", "train", "truck", "boat", "traffic light",
          "fire hydrant", "stop sign", "parking meter", "bench", "bird",
          "cat", "dog", "horse", "sheep", "cow",
          "elephant", "bear", "zebra", "giraffe", "backpack",
          "umbrella", "handbag", "tie", "suitcase", "frisbee",
          "skis", "snowboard", "sports ball", "kite", "baseball bat",
          "baseball glove", "skateboard", "surfboard","tennis racket", "bottle",
          "wine glass", "cup", "fork", "knife", "spoon",
          "bowl", "banana", "apple", "sandwich", "orange",
          "broccoli", "carrot", "hot dog", "pizza", "donut",
          "cake", "chair", "sofa", "pottedplant", "bed",
          "diningtable", "toilet", "tvmonitor", "laptop", "mouse",
          "remote", "keyboard", "cell phone", "microwave", "oven",
          "toaster", "sink", "refrigerator", "book", "clock",
          "vase", "scissors", "teddy bear", "hair drier", "toothbrush")

class Detection:
    xmin = 0
    ymin = 0
    xmax = 0
    ymax = 0
    class_id = 0
    confidence = 0.0

    def __init__(self, class_id, xmin, ymin, xmax, ymax):
        self.xmin = int(xmin)
        self.ymin = int(ymin)
        self.xmax = int(xmax)
        self.ymax = int(ymax)
        self.class_id = int(class_id)

img_data = []
def img_callback(data):
    img_data.append(data)
    

sub = rospy.Subscriber("/camera/color/image_raw/compressed", CompressedImage, callback=img_callback)
rospy.init_node("message_scheduling_node")

listener = TransformListener()

while not rospy.is_shutdown():
    if(len(img_data)):
        start = time.clock()

        # listener.waitForTransform("/map", "/camera_link", rospy.Time(0), rospy.Duration(3.0))
        # transform = listener.lookupTransform("/map", "/camera_link", rospy.Time(0))

        data = img_data.pop()
        bytedata = data.data

        # tt = json.loads(data.header)
        # print(data.header.seq)
        # rospy.loginfo(data.header)

        flag_data = str(len(bytedata)) + "," + str(data.header.seq)

        tcpClient.send(flag_data)

        data = tcpClient.recv(1024)
        if(b"ok" == data.decode()):
            tcpClient.send(bytedata)

        data = tcpClient.recv(1024)
        # print(time.clock() - start)
        # print(data.decode())
        obj_list = []
        results = data.decode().split(" ")
        for i in range(int(results[0])):
            obj_list.append(Detection(results[i + 2], results[i + 3], results[i + 4], results[i + 5], results[i + 6]))
            print(LABELS[obj_list.pop().class_id])
        print("--------")

        img_data = []
    # rospy.spin()