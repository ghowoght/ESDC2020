#!/usr/bin/env python3
# #-*- coding: UTF-8 -*- 

import subprocess
import time
import os

## 关闭hero_message_scheduling节点
p = subprocess.Popen("ps -aux | grep scripts/hero_message_scheduling.py", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
p.wait()
result = p.stdout.readline().decode('utf-8').split(" ")
pid = list(filter(None, result))[1]
os.system("kill " + pid)

time.sleep(2)

## 关闭ROS master节点
p = subprocess.Popen("ps -aux | grep /opt/ros/melodic/bin/rosmaster", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
p.wait()
result = p.stdout.readline().decode('utf-8').split(" ")
pid = list(filter(None, result))[1]
os.system("kill " + pid)

