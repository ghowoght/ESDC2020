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
rospy.init_node("target_search_node")

pub_newobj_flag = rospy.Publisher("/object_detection/flag",  Marker, queue_size=10) # 语音提示

# 位置：x, y, z 姿态：z, w
pose_array = [[0, 0, 0, 0, 1], # 原点
                            [7.7, -3.4, 0, -0.707, 0.707], 
                            [7.7, -3.4, 0, 0, 1], 
                            [7.7, -3.4, 0, 0.707, 0.707], 
                            [7.7, -3.4, 0, 1, 0], 
                            [-1.45, -3.4, 0, 1, 0],
                            [-1.45, -3.4, 0, -0.707, 0.707],
                            [-1.45, -3.4, 0, 0, 1],
                            [-1.45, -3.4, 0, 0.707, 0.707],
                            [-2.9, -0.2, 0, 0, 1],
                            [-2.9, -0.2, 0, -0.707, 0.707],
                            [-2.9, -0.2, 0, 1, 0],
                            [8, 0.2, 0, 0, 1],
                            [8, 0.2, 0, -0.707, 0.707],
                            [8, 0.2, 0, 1, 0],
                            [0, 0, 0, 1, 0], # 原点
                            [0, 0, 0, 0, 1] # 原点
                            ]
pose_list = []
for i in range(len(pose_array)):
    p = Pose()
    p.position.x = pose_array[i][0]
    p.position.y = pose_array[i][1]
    p.position.z = pose_array[i][2]
    p.orientation.z = pose_array[i][3]
    p.orientation.w = pose_array[i][4]
    pose_list.append(p)

rospy.init_node("target_search_node")
ac = SimpleActionClient("move_base", MoveBaseAction)
rospy.loginfo("waiting for the move base server")
ac.wait_for_server(rospy.Duration(5))
rospy.loginfo("conected to move base server")
time.sleep(3)
# 语音通知开始搜寻
m = Marker()
m.id = 998
pub_newobj_flag.publish(m)
for i in range(len(pose_list)):
    goal = MoveBaseGoal()
    goal.target_pose.header.frame_id = "map"
    goal.target_pose.header.stamp = rospy.Time(0)
    goal.target_pose.pose = pose_list[i]
    rospy.loginfo("sending goal")
    # rospy.loginfo(goal)
    ac.send_goal(goal)
    rospy.loginfo("waiting for results")

    if ac.wait_for_result():
        rospy.loginfo("reach goal!" + str(i))
rospy.loginfo("search complete!")
# 语音通知导航完毕
m = Marker()
m.id = 999
pub_newobj_flag.publish(m)
# while not rospy.is_shutdown():
#     pass