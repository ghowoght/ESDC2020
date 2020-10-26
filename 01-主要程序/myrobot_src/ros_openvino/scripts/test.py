#!/usr/bin/env python
# #-*- coding: UTF-8 -*- 
import rospy
from visualization_msgs.msg import Marker
import time

rospy.init_node("speech_alert_test_node")
pub_newobj_flag = rospy.Publisher("/object_detection/flag", Marker, queue_size=100)

while not rospy.is_shutdown():
    flag = Marker()
    flag.ns = "maid"
    pub_newobj_flag.publish(flag) # 进行语音提示
    time.sleep(3)

    flag = Marker()
    flag.ns = "sprite"
    pub_newobj_flag.publish(flag) # 进行语音提示
    time.sleep(3)

    flag = Marker()
    flag.ns = "cola"
    pub_newobj_flag.publish(flag) # 进行语音提示
    time.sleep(3)

    flag = Marker()
    flag.id = 998
    pub_newobj_flag.publish(flag) # 进行语音提示
    time.sleep(3)

    flag = Marker()
    flag.id = 999
    pub_newobj_flag.publish(flag) # 进行语音提示
    time.sleep(3)