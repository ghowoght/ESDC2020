#!/usr/bin/env python
# #-*- coding: UTF-8 -*- 

# import rospy
# from geometry_msgs.msg import Twist
# from std_msgs.msg import String
# import os, sys
# import  tty, termios
# import threading

# pub = rospy.Publisher("cmd_vel", Twist)
# rospy.init_node("remote_ctrl")
# rate = rospy.Rate(rospy.get_param("-hz", 20))

# cmd = Twist()
# cmd.linear.x = 0.0
# cmd.linear.y = 0.0
# cmd.angular.z = 0.0

# key = 0

# def keyboard_task():
#     while True:
#         tty.setraw(sys.stdin.fileno())  
#         ch = sys.stdin.read( 1 )  
#         if ch == "w":
#             cmd.linear.x = 0.2
#             cmd.linear.y = 0
#             cmd.angular.z = 0
#         elif ch == "s":
#             cmd.linear.x = -0.2
#             cmd.linear.y = 0
#             cmd.angular.z = 0
#         elif ch == "a":
#             cmd.linear.x = 0
#             cmd.linear.y = 0
#             cmd.angular.z = 0.5
#         elif ch == "d":
#             cmd.linear.x = 0
#             cmd.linear.y = 0
#             cmd.angular.z = -0.5
#         elif ch == "q":
#             key = -1
#             break
#         else:
#             cmd.linear.x = 0
#             cmd.linear.y = 0
#             cmd.angular.z = 0

# def ros_pub_task():
#     while not rospy.is_shutdown():    
#         if key == -1:
#             break
#         rospy.loginfo(str( cmd.linear.x) + " " + str(cmd.linear.y) + " " + str(cmd.angular.z))
#         pub.publish(cmd)
#         rate.sleep()

# t1 = threading.Thread(target=keyboard_task)
# t2 = threading.Thread(target=ros_pub_task)

# t1.start()
# t2.start()

import rospy
from geometry_msgs.msg import Twist
from std_msgs.msg import String
import os, sys
import  tty, termios
import threading
# import openvino
# import cv2
# print(cv2.__version__)

pub = rospy.Publisher("cmd_vel", Twist)
rospy.init_node("remote_ctrl")
rate = rospy.Rate(rospy.get_param("-hz", 20))

cmd = Twist()
cmd.linear.x = 0.0
cmd.linear.y = 0.0
cmd.angular.z = 0.0

while not rospy.is_shutdown():    
    tty.setraw(sys.stdin.fileno())  
    ch = sys.stdin.read( 1 )  
    if ch == "w":
        cmd.linear.x = 0.2
        cmd.linear.y = 0
        cmd.angular.z = 0
    elif ch == "s":
        cmd.linear.x = -0.2
        cmd.linear.y = 0
        cmd.angular.z = 0
    elif ch == "a":
        cmd.linear.x = 0
        cmd.linear.y = 0
        cmd.angular.z = 0.5
    elif ch == "d":
        cmd.linear.x = 0
        cmd.linear.y = 0
        cmd.angular.z = -0.5
    elif ch == "q":
        break
    else:
        cmd.linear.x = 0
        cmd.linear.y = 0
        cmd.angular.z = 0
    rospy.loginfo(str( cmd.linear.x) + " " + str(cmd.linear.y) + " " + str(cmd.angular.z) + "\r\n")
    pub.publish(cmd)
    rate.sleep()
