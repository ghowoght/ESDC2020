#!/usr/bin/env python
# #-*- coding: UTF-8 -*- 

import rospy
from actionlib import SimpleActionClient
from actionlib import SimpleGoalState
from move_base_msgs.msg import MoveBaseAction
from move_base_msgs.msg import MoveBaseGoal
from geometry_msgs.msg import Pose
import time
from visualization_msgs.msg import Marker

import subprocess
import os

## 关闭explore节点
p = subprocess.Popen("ps -aux | grep explore_lite/explore", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
p.wait()
result = p.stdout.readline().decode('utf-8').split(" ")
pid = list(filter(None, result))[1]
os.system("kill " + pid)
time.sleep(1)
print("explore shutdown ok")

## 关闭search节点
p = subprocess.Popen("ps -aux | grep /scripts/TargetSearch.py", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
p.wait()
result = p.stdout.readline().decode('utf-8').split(" ")
pid = list(filter(None, result))[1]
os.system("kill " + pid)
time.sleep(1)
print("search shutdown ok")

p = Pose()
p.position.x = 0
p.position.y = 0
p.position.z = 0
p.orientation.z = 0
p.orientation.w = 1

rospy.init_node("return_origin_node")

pub_newobj_flag = rospy.Publisher("/object_detection/flag",  Marker, queue_size=10) # 语音提示

ac = SimpleActionClient("move_base", MoveBaseAction)
rospy.loginfo("waiting for the move base server")
ac.wait_for_server(rospy.Duration(5))
rospy.loginfo("conected to move base server")

# 语音通知正在返回
m = Marker()
m.id = 996
pub_newobj_flag.publish(m)
time.sleep(3)

goal = MoveBaseGoal()
goal.target_pose.header.frame_id = "map"
goal.target_pose.header.stamp = rospy.Time(0)
goal.target_pose.pose = p
rospy.loginfo("sending goal")
# rospy.loginfo(goal)
ac.send_goal(goal)
rospy.loginfo("waiting for results")

if ac.wait_for_result():
    pass
    # rospy.loginfo("reach goal!" + str(i))
rospy.loginfo("search complete!")
# 语音通知返回完毕
m = Marker()
m.id = 997
pub_newobj_flag.publish(m)
# while not rospy.is_shutdown():
#     pass