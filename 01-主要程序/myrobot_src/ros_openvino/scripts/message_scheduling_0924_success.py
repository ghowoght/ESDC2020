#!/usr/bin/env python
# #-*- coding: UTF-8 -*- 
# 消息调度 实现Python3和ROS的通信

#!/usr/bin/env python
import cv2
import rospy
from sensor_msgs.msg import CompressedImage
from sensor_msgs.msg import Image
from sensor_msgs.msg import CameraInfo
from visualization_msgs.msg import Marker
from visualization_msgs.msg import MarkerArray
from geometry_msgs.msg import PointStamped
from tf import TransformListener
import os, sys
import threading
from cv_bridge import CvBridge,CvBridgeError

import time
import socket
import numpy as np
import copy

HOST = ''
PORT = 8080
ADDRESS = (HOST, PORT)
tcpClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# time.sleep(3)
tcpClient.connect(ADDRESS)

LABELS = ('background',
          'aeroplane', 'bicycle', 'bird', 'boat',
          'bottle', 'bus', 'car', 'cat', 'chair',
          'cow', 'diningtable', 'dog', 'horse',
          'motorbike', 'person', 'pottedplant',
          'sheep', 'sofa', 'train', 'tvmonitor')

class Buffer:
    def __init__(self, color_image, depth_image):
        self.color_image = color_image
        self.depth_image = depth_image

from Queue import Queue

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

class Objection:
    def __init__(self, cls_id, x, y, z):
        self.cls_id = cls_id
        self.x = x
        self.y = y
        self.z = z
    def isSameObjection(self, cls_id, x, y, z):
        # 两者标签不同，则必定不是同一目标
        if(self.cls_id != cls_id):
            return False
        # 两者重心距离小于阈值，则认为是同一个物体
        dist = np.sqrt(pow(self.x - x, 2) + pow(self.y - y, 2) + pow(self.z - z, 2))
        if(dist < 0.2):#vector_dist_threshold[self.cls_id]):
            # 如果是同一个物体，则更新当前物体的位置
            return True
        return False
obj_tag_list = []

new_color_flag = False
new_depth_flag = False
NUM_BUFFER = 3
color_buffer = []
def color_callback(data):
    global new_color_flag
    color_buffer.append(data)
    new_color_flag = True
    if(len(color_buffer) > NUM_BUFFER):
        color_buffer.pop(0)

depth_buffer = []
def depth_callback(data):
    global new_depth_flag
    depth_buffer.append(data)
    new_depth_flag = True
    if(len(depth_buffer) > NUM_BUFFER):
        depth_buffer.pop(0)

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
    
# 话题订阅
sub_color = rospy.Subscriber("/camera/color/image_raw/compressed", CompressedImage, callback=color_callback)
sub_depth = rospy.Subscriber("/camera/aligned_depth_to_color/image_raw", Image, callback=depth_callback)
# sub_depth = rospy.Subscriber("/camera/aligned_depth_to_color/image_raw/compressed", CompressedImage, callback=depth_callback)
sub_depth = rospy.Subscriber("/camera/aligned_depth_to_color/camera_info", CameraInfo, callback=info_callback)
# 话题发布
pub_marker = rospy.Publisher("/semantic_tagging/markers", MarkerArray, queue_size=100)
pub_image = rospy.Publisher("/object_detection/output_image", Image, queue_size=10)
markers = MarkerArray()
marker = Marker()

rospy.init_node("message_scheduling_node")

listener = TransformListener()

data_buffer_queue = Queue(100)
cv2.namedWindow("img", cv2.WINDOW_AUTOSIZE)
while not rospy.is_shutdown():
    if(len(color_buffer) > 0 and len(depth_buffer) > 0 and new_color_flag and new_depth_flag):
        new_color_flag = False
        new_depth_flag = False
        start = time.clock()
        ##### 深度图与彩色图进行同步 #####
        color_buffer_copy = color_buffer[:]
        depth_buffer_copy = depth_buffer[:]
        color_image = color_buffer_copy[0]
        depth_image = depth_buffer_copy[0]
        color_buffer_copy.pop(0)
        depth_buffer_copy.pop(0)
        while(abs(depth_image.header.stamp.to_sec() - color_image.header.stamp.to_sec()) > 0.03):
            if(len(color_buffer_copy) == 0 or len(depth_buffer_copy) == 0):
                break
            # 如果深度图比彩色图老，就从队列中取出一张深度图
            if(depth_image.header.stamp.to_sec() - color_image.header.stamp.to_sec() < -0.03):
                depth_image = depth_buffer_copy[0]
                depth_buffer_copy.pop(0)
            elif(depth_image.header.stamp.to_sec() - color_image.header.stamp.to_sec() > 0.03):
                color_image = color_buffer_copy[0]
                color_buffer_copy.pop(0)
        # 如果仍然不同步，则进行下一轮循环
        if(abs(depth_image.header.stamp.to_sec() - color_image.header.stamp.to_sec()) > 0.01):
            continue

        buffer = Buffer(copy.deepcopy(color_image), copy.deepcopy(depth_image))
        
        # 数据缓存区已满，则删除第一个
        if(data_buffer_queue.full()):
            data_buffer_queue.get()
        data_buffer_queue.put(buffer) # 放入缓存

        # 发送图像
        bytedata = color_image.data
        flag_data = str(len(bytedata)) + "," + str(color_image.header.seq)
        tcpClient.send(flag_data)
        data = tcpClient.recv(1024)
        if(b"ok" == data.decode()):
            tcpClient.send(bytedata)
        data = tcpClient.recv(1024)

        ##### 结果解析 #####
        obj_list = []
        results = data.decode().split(" ")
        buffer = data_buffer_queue.get()
        img = np.asarray(bytearray(buffer.color_image.data), dtype="uint8")
        img = cv2.imdecode(img, cv2.IMREAD_COLOR)
        if(results[0] == ''):
            continue
        if(int(results[0]) > 0):
            while(buffer.color_image.header.seq < int(results[1])):
                if(data_buffer_queue.empty()):
                    break
                buffer = data_buffer_queue.get()

            ## 结合深度信息进行分析
            # 转换深度图像话题
            br = CvBridge()
            depth_image = buffer.depth_image
            depth_image = br.imgmsg_to_cv2(depth_image) 
            
            # 结果分析
            for i in range(int(results[0])):
                obj = Detection(results[i * 5 + 2], results[i * 5 + 3], results[i * 5 + 4], results[i * 5 + 5], results[i * 5 + 6])
                cv2.rectangle(img, (obj.xmin, obj.ymin), (obj.xmax, obj.ymax), (255, 128, 0), 1)
                print(LABELS[obj.class_id])

                # 只处理部分结果
                if(LABELS[obj.class_id] != "bottle"):
                    continue
                ###### 深度分析 #####
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
                # 在深度图像上画出边界，并将边界内部填充为0xffff
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
                box_width = avg[0] / fx * (obj.xmax - obj.xmin) / 1000.0
                box_height= avg[0] / fy * (obj.ymax - obj.ymin) / 1000.0
                box_depth = dstd[0]*2.0/1000.0
                print([box_x[0], box_y[0], box_z[0]])

                # 坐标转换 camera_link --> map
                if(box_x > 2):
                    continue
                p = PointStamped() # 相机坐标
                p.header.frame_id = "camera_link"
                p.header.stamp = rospy.Time(0)#buffer.color_image.header.stamp
                p.point.x = box_x[0]
                p.point.y = box_y[0]
                p.point.z = box_z[0]
                # 转换
                pw = listener.transformPoint("map", p) # 世界坐标
                print([pw.point.x, pw.point.y, pw.point.z])

                obj_tagging = Objection(obj.class_id, pw.point.x, pw.point.y, pw.point.z)
                isNewObj = True
                for obj_tagged in obj_tag_list:
                    if obj_tagging.isSameObjection(obj_tagged.cls_id, obj_tagged.x, obj_tagged.y, obj_tagged.z):
                        isNewObj = False
                if(isNewObj):
                    obj_tag_list.append(obj_tagging)
                    # 可视化
                    marker.header.frame_id = "/map"
                    marker.header.stamp = rospy.Time.now()
                    marker.ns=LABELS[obj.class_id] + "_" + str(len(obj_tag_list)); #在标签后添加一个id
                    marker.id = len(obj_tag_list)
                    marker.type = Marker.CUBE
                    marker.action = Marker.ADD
                    marker.pose.position.x = pw.point.x
                    marker.pose.position.y = pw.point.y
                    marker.pose.position.z = pw.point.z
                    marker.pose.orientation.x = 0.0
                    marker.pose.orientation.y = 0.0
                    marker.pose.orientation.z = 0.0
                    marker.pose.orientation.w = 1.0
                    marker.scale.x = 0.2#vector_thickness[obj.cls_id]
                    marker.scale.y =box_width
                    marker.scale.z = box_height
                    marker.color.r = 127/255.0
                    marker.color.g = 0/255.0
                    marker.color.b = 255/255.0
                    marker.color.a = 0.6
                    # global markers
                    markers.markers.append(marker)
                print(len(markers.markers))
                pub_marker.publish(markers)
            
            print("--------")

        bridge = CvBridge()
        pub_image.publish(bridge.cv2_to_imgmsg(img))
        # if(cv2.waitKey(1)&0xFF == ord('q')):
        #     sys.exit(0)
        # cv2.imshow("img", cv2.resize(img, (640, 480)))
        # 清空缓存区
        # color_data = 0
        # depth_data = 0