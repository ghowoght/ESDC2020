#!/usr/bin/env python3
# #-*- coding: UTF-8 -*- 

import sys, os, cv2, time, heapq, argparse
import numpy as np, math
from openvino.inference_engine import IENetwork, IEPlugin
import multiprocessing as mp
from time import sleep
import threading
import numpy
import socket

yolo_scale_13 = 13
yolo_scale_26 = 26
yolo_scale_52 = 52

classes = 80
coords = 4
num = 3
anchors = [10,13,16,30,33,23,30,61,62,45,59,119,116,90,156,198,373,326]

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

label_text_color = (255, 255, 255)
label_background_color = (125, 175, 75)
box_color = (255, 128, 0)
box_thickness = 1

processes = []

fps = ""
detectfps = ""
framecount = 0
detectframecount = 0
time1 = 0
time2 = 0
lastresults = None

def EntryIndex(side, lcoords, lclasses, location, entry):
    n = int(location / (side * side))
    loc = location % (side * side)
    return int(n * side * side * (lcoords + lclasses + 1) + entry * side * side + loc)


class DetectionObject():
    xmin = 0
    ymin = 0
    xmax = 0
    ymax = 0
    class_id = 0
    confidence = 0.0

    def __init__(self, x, y, h, w, class_id, confidence, h_scale, w_scale):
        self.xmin = int((x - w / 2) * w_scale)
        self.ymin = int((y - h / 2) * h_scale)
        self.xmax = int(self.xmin + w * w_scale)
        self.ymax = int(self.ymin + h * h_scale)
        self.class_id = class_id
        self.confidence = confidence


def IntersectionOverUnion(box_1, box_2):
    width_of_overlap_area = min(box_1.xmax, box_2.xmax) - max(box_1.xmin, box_2.xmin)
    height_of_overlap_area = min(box_1.ymax, box_2.ymax) - max(box_1.ymin, box_2.ymin)
    area_of_overlap = 0.0
    if (width_of_overlap_area < 0.0 or height_of_overlap_area < 0.0):
        area_of_overlap = 0.0
    else:
        area_of_overlap = width_of_overlap_area * height_of_overlap_area
    box_1_area = (box_1.ymax - box_1.ymin)  * (box_1.xmax - box_1.xmin)
    box_2_area = (box_2.ymax - box_2.ymin)  * (box_2.xmax - box_2.xmin)
    area_of_union = box_1_area + box_2_area - area_of_overlap
    retval = 0.0
    if area_of_union <= 0.0:
        retval = 0.0
    else:
        retval = (area_of_overlap / area_of_union)
    return retval


def ParseYOLOV3Output(blob, resized_im_h, resized_im_w, original_im_h, original_im_w, threshold, objects):

    out_blob_h = blob.shape[2]
    out_blob_w = blob.shape[3]

    side = out_blob_h
    anchor_offset = 0

    if side == yolo_scale_13:
        anchor_offset = 2 * 6
    elif side == yolo_scale_26:
        anchor_offset = 2 * 3
    elif side == yolo_scale_52:
        anchor_offset = 2 * 0

    side_square = side * side
    output_blob = blob.flatten()

    for i in range(side_square):
        row = int(i / side)
        col = int(i % side)
        for n in range(num):
            obj_index = EntryIndex(side, coords, classes, n * side * side + i, coords)
            box_index = EntryIndex(side, coords, classes, n * side * side + i, 0)
            scale = output_blob[obj_index]
            if (scale < threshold):
                continue
            x = (col + output_blob[box_index + 0 * side_square]) / side * resized_im_w
            y = (row + output_blob[box_index + 1 * side_square]) / side * resized_im_h
            height = math.exp(output_blob[box_index + 3 * side_square]) * anchors[anchor_offset + 2 * n + 1]
            width = math.exp(output_blob[box_index + 2 * side_square]) * anchors[anchor_offset + 2 * n]
            for j in range(classes):
                class_index = EntryIndex(side, coords, classes, n * side_square + i, coords + 1 + j)
                prob = scale * output_blob[class_index]
                if prob < threshold:
                    continue
                obj = DetectionObject(x, y, height, width, j, prob, (original_im_h / resized_im_h), (original_im_w / resized_im_w))
                objects.append(obj)
    return objects

class ImageData:
    def __init__(self, seq, color_image):
        self.seq = seq
        self.color_image = color_image

class ResultData:
    def __init__(self, seq, objects):
        self.seq = seq
        self.objects = objects
    

def camThread(LABELS, results, frameBuffer, camera_width, camera_height, vidfps):
    global fps
    global detectfps
    global lastresults
    global framecount
    global detectframecount
    global time1
    global time2
    # global cam
    # global window_name

    host = ''
    port = 8080
    address = (host, port)
    # 创建一个套接字
    tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 绑定本地ip
    tcpServer.bind(address)
    # 开始监听
    tcpServer.listen(5)

    # cam = cv2.VideoCapture(0)
    # camera_width = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
    # camera_height = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
    # frame_count = int(cam.get(cv2.CAP_PROP_FRAME_COUNT))
    # window_name = "img"
    # wait_key_time = int(1000 / vidfps)

    # cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    while True:
        print("等待连接……")
        client_socket, client_address = tcpServer.accept()
        print("连接成功！")

        while True:
            # 接收标志数据
            data = client_socket.recv(1024)
            if data:
                # 通知客户端“已收到标志数据，可以发送图像数据”
                client_socket.send(b"ok")
                # 处理标志数据
                flag = data.decode().split(",")
                # 图像字节流数据的总长度
                total = int(flag[0])
                # 图像序号
                seq = int(flag[1])
                # 接收到的数据计数
                cnt = 0
                # 存放接收到的数据
                img_bytes = b""

                while cnt < total:
                    # 当接收到的数据少于数据总长度时，则循环接收图像数据，直到接收完毕
                    data = client_socket.recv(256000)
                    img_bytes += data
                    cnt += len(data)
                    # print("receive:" + str(cnt) + "/" + flag[0])

                # 解析接收到的字节流数据，并显示图像
                img = np.asarray(bytearray(img_bytes), dtype="uint8")
                img = cv2.imdecode(img, cv2.IMREAD_COLOR)

                t1 = time.perf_counter()

                color_image = img

                if frameBuffer.full():
                    frameBuffer.get()

                height = color_image.shape[0]
                width = color_image.shape[1]

                image_data = ImageData(seq, color_image.copy())
                frameBuffer.put(image_data)

                obj_result_data = []
                obj_cnt = 0
                if not results.empty():
                    result = results.get(False)
                    obj_result_data.append(str(result.seq))
                    print("output: " + str(result.seq))
                    objects = result.objects
                    detectframecount += 1

                    
                    for obj in objects:
                        if obj.confidence < 0.2:
                            continue
                        label = obj.class_id
                        confidence = obj.confidence
                        if confidence > 0.2:
                            # label_text = LABELS[label] + " (" + "{:.1f}".format(confidence * 100) + "%)"
                            # cv2.rectangle(color_image, (obj.xmin, obj.ymin), (obj.xmax, obj.ymax), box_color, box_thickness)
                            # cv2.putText(color_image, label_text, (obj.xmin, obj.ymin - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, label_text_color, 1)
                            # print(obj.xmin, obj.ymin)
                            obj_result_data.append(str(obj.class_id))
                            obj_result_data.append(str(obj.xmin))
                            obj_result_data.append(str(obj.ymin))
                            obj_result_data.append(str(obj.xmax))
                            obj_result_data.append(str(obj.ymax))
                            obj_cnt = obj_cnt + 1
                    lastresults = objects
                    # print("--------")
                # else:
                #     if not isinstance(lastresults, type(None)):
                #         for obj in lastresults:
                #             if obj.confidence < 0.2:
                #                 continue
                #             label = obj.class_id
                #             confidence = obj.confidence
                #             # if confidence > 0.2:
                                # label_text = LABELS[label] + " (" + "{:.1f}".format(confidence * 100) + "%)"
                                # cv2.rectangle(color_image, (obj.xmin, obj.ymin), (obj.xmax, obj.ymax), box_color, box_thickness)
                                # cv2.putText(color_image, label_text, (obj.xmin, obj.ymin - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, label_text_color, 1)

                # cv2.putText(color_image, fps,       (width-170,15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (38,0,255), 1, cv2.LINE_AA)
                # cv2.putText(color_image, detectfps, (width-170,30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (38,0,255), 1, cv2.LINE_AA)
                # cv2.imshow(window_name, cv2.resize(color_image, (width, height)))
                # if cv2.waitKey(1)&0xFF == ord('q'):
                #     sys.exit(0)

                # ## Print FPS
                # framecount += 1
                # if framecount >= 15:
                #     fps       = "(Playback) {:.1f} FPS".format(time1/15)
                #     detectfps = "(Detection) {:.1f} FPS".format(detectframecount/time2)
                #     framecount = 0
                #     detectframecount = 0
                #     time1 = 0
                #     time2 = 0
                # t2 = time.perf_counter()
                # elapsedTime = t2-t1
                # time1 += 1/elapsedTime
                # time2 += elapsedTime

                # 通知客户端“已经接收完毕，可以开始下一帧图像的传输”
                obj_result_data.insert(0, str(obj_cnt))
                client_socket.send(bytes(" ".join(obj_result_data), encoding="utf-8"))

            else:
                print("已断开！")
                break
        
            

# l = Search list
# x = Search target value
def searchlist(l, x, notfoundvalue=-1):
    if x in l:
        return l.index(x)
    else:
        return notfoundvalue


def async_infer(ncsworker):

    ncsworker.skip_frame_measurement()

    while True:
        ncsworker.predict_async()


class NcsWorker(object):

    def __init__(self, devid, frameBuffer, results, camera_width, camera_height, number_of_ncs, vidfps):
        self.devid = devid
        self.frameBuffer = frameBuffer
        self.model_xml = "/home/ghowoght/workplace/myrobot/src/ros_openvino/models/Yolov3/FP16/frozen_yolo_v3.xml"
        self.model_bin = "/home/ghowoght/workplace/myrobot/src/ros_openvino/models/Yolov3/FP16/frozen_yolo_v3.bin"
        self.camera_width = camera_width
        self.camera_height = camera_height
        self.m_input_size = 416
        self.threshould = 0.7
        self.num_requests = 4
        self.inferred_request = [0] * self.num_requests
        self.heap_request = []
        self.inferred_cnt = 0
        self.plugin = IEPlugin(device="MYRIAD")
        self.net = IENetwork(model=self.model_xml, weights=self.model_bin)
        self.input_blob = next(iter(self.net.inputs))
        self.exec_net = self.plugin.load(network=self.net, num_requests=self.num_requests)
        self.results = results
        self.number_of_ncs = number_of_ncs
        self.predict_async_time = 800
        self.skip_frame = 0
        self.roop_frame = 0
        self.vidfps = vidfps
        self.new_w = int(camera_width * self.m_input_size/camera_width)
        self.new_h = int(camera_height * self.m_input_size/camera_height)

    def image_preprocessing(self, color_image):
        resized_image = cv2.resize(color_image, (self.new_w, self.new_h), interpolation = cv2.INTER_CUBIC)
        canvas = np.full((self.m_input_size, self.m_input_size, 3), 128)
        canvas[(self.m_input_size-self.new_h)//2:(self.m_input_size-self.new_h)//2 + self.new_h,(self.m_input_size-self.new_w)//2:(self.m_input_size-self.new_w)//2 + self.new_w,  :] = resized_image
        prepimg = canvas
        prepimg = prepimg[np.newaxis, :, :, :]     # Batch size axis add
        prepimg = prepimg.transpose((0, 3, 1, 2))  # NHWC to NCHW
        return prepimg


    def skip_frame_measurement(self):
            surplustime_per_second = (1000 - self.predict_async_time)
            if surplustime_per_second > 0.0:
                frame_per_millisecond = (1000 / self.vidfps)
                total_skip_frame = surplustime_per_second / frame_per_millisecond
                self.skip_frame = int(total_skip_frame / self.num_requests)
            else:
                self.skip_frame = 0


    def predict_async(self):
        try:

            if self.frameBuffer.empty():
                return

            self.roop_frame += 1
            if self.roop_frame <= self.skip_frame:
               self.frameBuffer.get()
               return
            self.roop_frame = 0

            frame = self.frameBuffer.get()
            prepimg = self.image_preprocessing(frame.color_image)
            reqnum = searchlist(self.inferred_request, 0)

            if reqnum > -1:
                self.exec_net.start_async(request_id=reqnum, inputs={self.input_blob: prepimg})
                self.inferred_request[reqnum] = 1
                self.inferred_cnt += 1
                if self.inferred_cnt == sys.maxsize:
                    self.inferred_request = [0] * self.num_requests
                    self.heap_request = []
                    self.inferred_cnt = 0
                heapq.heappush(self.heap_request, (self.inferred_cnt, reqnum))

            cnt, dev = heapq.heappop(self.heap_request)

            if self.exec_net.requests[dev].wait(0) == 0:
                self.exec_net.requests[dev].wait(-1)

                objects = []
                outputs = self.exec_net.requests[dev].outputs
                for output in outputs.values():
                    objects = ParseYOLOV3Output(output, self.new_h, self.new_w, self.camera_height, self.camera_width, self.threshould, objects)

                objlen = len(objects)
                for i in range(objlen):
                    if (objects[i].confidence == 0.0):
                        continue
                    for j in range(i + 1, objlen):
                        if (IntersectionOverUnion(objects[i], objects[j]) >= 0.4):
                            objects[j].confidence = 0
                # 将序列号加入到结果中
                result = ResultData(frame.seq, objects)
                print("input: " + str(frame.seq))
                self.results.put(result)
                self.inferred_request[dev] = 0
            else:
                heapq.heappush(self.heap_request, (cnt, dev))
        except:
            import traceback
            traceback.print_exc()


def inferencer(results, frameBuffer, number_of_ncs, camera_width, camera_height, vidfps):

    # Init infer threads
    threads = []
    for devid in range(number_of_ncs):
        thworker = threading.Thread(target=async_infer, args=(NcsWorker(devid, frameBuffer, results, camera_width, camera_height, number_of_ncs, vidfps),))
        thworker.start()
        threads.append(thworker)

    for th in threads:
        th.join()


if __name__ == '__main__':

    # parser = argparse.ArgumentParser()
    # parser.add_argument('-numncs','--numberofncs',dest='number_of_ncs',type=int,default=1,help='Number of NCS. (Default=1)')
    # args = parser.parse_args()

    number_of_ncs = 2 #args.number_of_ncs
    camera_width = 640
    camera_height = 480
    vidfps = 30

    # # 读取参数
    # f = open("/home/ghowoght/workplace/myrobot/src/ros_openvino/config/model_yolo_config.txt", 'r')
    # xml_path = f.readline().split("\n")[0]
    # bin_path = f.readline().split("\n")[0]
    # label_path = f.readline().split("\n")[0]
    # ff = open(label_path, 'r')
    # LABELS = ff.read().split("\n")
    # PORT = int(f.readline())
    # print(xml_path)
    # print(bin_path)
    # # LABELS = f.readline().split(" ")
    # f.close()

    try:

        mp.set_start_method('forkserver')
        frameBuffer = mp.Queue(10)
        results = mp.Queue()

        # Start streaming
        p = mp.Process(target=camThread, args=(LABELS, results, frameBuffer, camera_width, camera_height, vidfps), daemon=True)
        p.start()
        processes.append(p)

        # Start detection MultiStick
        # Activation of inferencer
        p = mp.Process(target=inferencer, args=(results, frameBuffer, number_of_ncs, camera_width, camera_height, vidfps), daemon=True)
        p.start()
        processes.append(p)

        sleep(number_of_ncs * 7)

        while True:
            sleep(1)

    except:
        import traceback
        traceback.print_exc()
    finally:
        for p in range(len(processes)):
            processes[p].terminate()

        print("\n\nFinished\n\n")