#!/usr/bin/env python
# #-*- coding: UTF-8 -*- 

import rospy
from visualization_msgs.msg import Marker
import socket
import time

host = ''
port = 9000
address = (host, port)
tcpClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
time.sleep(1)
tcpClient.connect(address)

# tcpClient.send("可乐")
# data = tcpClient.recv(1024)
# if(b"ok" == data.decode()):
#     pass

def flag_callback(data):
    if(data.id != 0):
        tcpClient.send(str(data.id))
    else:
        tcpClient.send(data.ns)
    data = tcpClient.recv(1024)
    
    if(b"ok" == data.decode()):
        pass

rospy.init_node("speech_alert_node")
sub_color = rospy.Subscriber("/object_detection/flag", Marker, callback=flag_callback)
rospy.spin()