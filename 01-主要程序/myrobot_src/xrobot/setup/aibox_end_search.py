#!/usr/bin/env python3
# #-*- coding: UTF-8 -*- 

import subprocess
import time
import os

## 关闭aibox_speech_alert节点
p = subprocess.Popen("ps -aux | grep scripts/aibox_speech_alert.py", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
p.wait()
result = p.stdout.readline().decode('utf-8').split(" ")
pid = list(filter(None, result))[1]
os.system("kill " + pid)
time.sleep(1)
print("speech alert shutdown ok")

## 关闭RVIZ节点
p = subprocess.Popen("ps -aux | grep rviz/xrobot.rviz", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
p.wait()
result = p.stdout.readline().decode('utf-8').split(" ")
pid = list(filter(None, result))[1]
os.system("kill " + pid)
time.sleep(1)
print("rviz shutdown ok")

## 关闭search节点
p = subprocess.Popen("ps -aux | grep /scripts/TargetSearch.py", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
p.wait()
result = p.stdout.readline().decode('utf-8').split(" ")
pid = list(filter(None, result))[1]
os.system("kill " + pid)
time.sleep(2)
print("explore search ok")

## 关闭speech_alert的Python3服务端
p = subprocess.Popen("ps -aux | grep scripts/speech_alert", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
p.wait()
result = p.stdout.readline().decode('utf-8').split(" ")
pid = list(filter(None, result))[1]
os.system("kill " + pid)
print("shutdown ok")