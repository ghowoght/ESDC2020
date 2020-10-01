#!/usr/bin/env python
# #-*- coding: UTF-8 -*- 
# 消息调度 实现Python3和ROS的通信

#!/usr/bin/env python
import cv2
import rospy
from sensor_msgs.msg import CompressedImage
from sensor_msgs.msg import Image
from sensor_msgs.msg import CameraInfo
from tf import TransformListener
import os, sys
import threading
from cv_bridge import CvBridge,CvBridgeError

import time
import socket
import numpy as np
# import pyrealsense2 as rs

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

class Buffer:
    def __init__(self, color_image, depth_image):
        self.color_image = color_image
        self.depth_image = depth_image

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

color_data = []
def color_callback(data):
    color_data.append(data)

depth_data = []
def depth_callback(data):
    depth_data.append(data)

fx = 1
fy = 1
cx = 1
cy = 1
def info_callback(info_msg):
    global fx, fy, cx, cy
    fx = info_msg.K[0]
    fy = info_msg.K[4]
    cx = info_msg.K[2]
    cy = info_msg.K[5]
    

sub_color = rospy.Subscriber("/camera/color/image_raw/compressed", CompressedImage, callback=color_callback)
sub_depth = rospy.Subscriber("/camera/aligned_depth_to_color/image_raw", Image, callback=depth_callback)
# sub_depth = rospy.Subscriber("/camera/aligned_depth_to_color/image_raw/compressed", CompressedImage, callback=depth_callback)
sub_depth = rospy.Subscriber("/camera/aligned_depth_to_color/camera_info", CameraInfo, callback=info_callback)

rospy.init_node("message_scheduling_node")

listener = TransformListener()

# 数据缓存，用图像序列号进行索引
data_buffer_dict = {}
cv2.namedWindow("img", cv2.WINDOW_AUTOSIZE)
while not rospy.is_shutdown():
    if(len(color_data) > 0 and len(depth_data) > 0):
        
        start = time.clock()

        # listener.waitForTransform("/map", "/camera_link", rospy.Time(0), rospy.Duration(3.0))
        # transform = listener.lookupTransform("/map", "/camera_link", rospy.Time(0))

        # print([len(color_data), len(depth_data)])
        # color_image = color_data.pop()
        # depth_image = depth_data.pop()
        
        color_image = color_data[len(color_data) - 1]
        depth_image = depth_data[len(depth_data) - 1]
        buffer = Buffer(color_image, depth_image)
        
        # print(rospy.Time.now().to_sec())
        if(abs(depth_image.header.stamp.to_sec() - color_image.header.stamp.to_sec()) > 0.03):
            continue
        print(depth_image.header.stamp.to_sec() - color_image.header.stamp.to_sec())

        data_buffer_dict[str(color_image.header.seq)] = buffer

        # 发送图像
        bytedata = color_image.data
        flag_data = str(len(bytedata)) + "," + str(color_image.header.seq)

        tcpClient.send(flag_data)

        data = tcpClient.recv(1024)
        if(b"ok" == data.decode()):
            tcpClient.send(bytedata)

        data = tcpClient.recv(1024)

        # 结果解析
        obj_list = []
        results = data.decode().split(" ")
        if(int(results[0]) > 0):

            buffer = data_buffer_dict[str(results[1])]
            img = np.asarray(bytearray(buffer.color_image.data), dtype="uint8")
            img = cv2.imdecode(img, cv2.IMREAD_COLOR)

            ## 结合深度信息进行分析
            # 转换深度图像话题
            br = CvBridge()
            depth_image = buffer.depth_image
            depth_image = br.imgmsg_to_cv2(depth_image) 
            # depth_image = br.compressed_imgmsg_to_cv2(depth_image) 
            # depth_image = np.asarray(depth_image, dtype="uint16")
            # depth_image = br.imgmsg_to_cv2(depth_image) 
            # depth_image_bytes_u8 = np.asarray(bytearray(depth_image_bytes), dtype="uint8")
            # depth_image = cv2.imdecode(depth_image_bytes_u8, cv2.IMREAD_UNCHANGED)
            # depth_image = depth_image.astype(np.uint16)
            
            # 删除已访问的数据
            del data_buffer_dict[str(results[1])]

            # 结果分析
            for i in range(int(results[0])):
                obj = Detection(results[i * 5 + 2], results[i * 5 + 3], results[i * 5 + 4], results[i * 5 + 5], results[i * 5 + 6])
                cv2.rectangle(img, (obj.xmin, obj.ymin), (obj.xmax, obj.ymax), (255, 128, 0), 1)
                # print(LABELS[obj.class_id])

                if(LABELS[obj.class_id] != "bottle"):
                    continue

                # 截取目标物区域
                subdepthP = depth_image[obj.ymin: obj.ymax, obj.xmin: obj.xmax]
                if(subdepthP.size == 0):
                    continue
                subdepth_full = np.uint16(subdepthP)
                subdepth = np.asarray(subdepthP, dtype="uint16")
                # 16位转化为8位
                subdepth = cv2.convertScaleAbs(subdepth_full, alpha=0.0390625)
                # 求平均值
                m=cv2.mean(subdepth)
                # 阈值化
                ret, subdepth = cv2.threshold(subdepth, thresh=m[0] * 2.0, maxval=100, type=4)
                # 提取边界
                subdepth, contours, hierarchy = cv2.findContours(subdepth ,cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                # 在在深度图像上画出边界，并将边界内部填充为0xffff
                subdepth = cv2.drawContours(subdepth, contours, -1, 0xffff, thickness=cv2.FILLED)
                # 转换回16位的二值化图像，这样目标所在区的值全部为0xffff
                subdepth = np.asarray(subdepth, dtype="uint16")
                subdepth = subdepth + subdepth * 256
                # 将原始深度图像与二值化图像按位与
                subdepth_full = cv2.bitwise_and(subdepth,subdepth_full)
                # 标记目标所在的位置
                mask = np.array(subdepth_full!=0, dtype="uint8")
                # 求目标像素的平均值
                avg, dstd = cv2.meanStdDev(subdepth_full, mask=mask)
                # 计算结果
                box_x = avg[0] / 1000.0
                box_y = -(((obj.xmax + obj.xmin) / 2.0) - cx) / fx * avg[0] / 1000.0
                box_z = -(((obj.ymax + obj.ymin) / 2.0) - cy) / fy * avg[0] / 1000.0
                print([box_x[0], box_y[0], box_z[0]])
                
            cv2.imshow("img", cv2.resize(img, (640, 480)))
            if cv2.waitKey(1)&0xFF == ord('q'):
                sys.exit(0)
            print("--------")

        # 清空缓存区
        color_data = []
        depth_data = []