#!/usr/bin/env python
# #-*- coding: UTF-8 -*- 
# # 构建知识图谱

import rospy
from visualization_msgs.msg import MarkerArray
import json
import numpy as np
from py2neo import *

graph =  Graph("http://localhost:7474",username="neo4j",password="ghowoght")
graph.run("MATCH (n) DETACH DELETE n") # 清空数据库

# 限制条件
prior_conditions = json.load(open("src/ros_openvino/config/my_ontology.json", "r"))
print(prior_conditions.get("obj_avail"))
# print(prior_conditions)


class Objection:
    name = ""
    x = 0.0
    y = 0.0
    z = 0.0
    def __init__(self, name, x, y, z):
        self.name = name
        self.x = x
        self.y = y
        self.z = z
    def distance(self, obj_):
        return np.sqrt(np.power(self.x - obj_.x, 2) + np.power(self.y - obj_.y, 2) + np.power(self.z - obj_.z, 2))
    def get_label(self):
        s = self.name.split("_")
        obj_avail = prior_conditions.get("obj_avail")
        if(s[0] in obj_avail):
            return "obj_avail"
        else:
            return "obj_unavail"

node_cnt = 0
obj_list = []
node_list = []

def callback(data):    
    global node_cnt
    while(node_cnt < len(data.markers)):
        marker = data.markers[node_cnt]
        node_cnt = node_cnt + 1
        rospy.loginfo(marker)
        obj = Objection(marker.ns, marker.pose.position.x, marker.pose.position.y, marker.pose.position.z)
        # 创建节点
        node = Node(obj.get_label(), name=obj.name, x=obj.x, y=obj.y, z=obj.z)
        graph.create(node)
        node_list.append(node)
        obj_list.append(obj)
        for i in range(len(obj_list)):
            if(obj_list[i] != obj):
                # 计算欧氏距离
                distance = obj.distance(obj_list[i])                
                # 添加关系
                relationship = Relationship(node_list[i], "dist", node, distance=distance)
                graph.create(relationship)
                relationship = Relationship(node, "dist", node_list[i], distance=distance)
                graph.create(relationship)
        graph.run("MATCH (n) RETURN n LIMIT 25")



sub = rospy.Subscriber("/semantic_tagging/markers", MarkerArray, callback)
rospy.init_node("kg_construct")

rospy.spin()
