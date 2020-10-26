#include <iostream>
#include <string>
#include <sstream>
#include <fstream>
#include <queue>
using namespace std;

#include<eigen3/Eigen/Core>
#include<eigen3/Eigen/Geometry>

#include "ros/ros.h"
#include "std_msgs/String.h"

#include "geometry_msgs/PoseStamped.h"

#include <tf/transform_broadcaster.h>
#include <tf/transform_listener.h>

#include <ros_openvino/Object.h>
#include <ros_openvino/Objects.h>
#include <ros_openvino/ObjectBox.h>
#include <ros_openvino/ObjectBoxList.h>

#include <math.h>

#include <visualization_msgs/Marker.h>
#include <visualization_msgs/MarkerArray.h>

ros_openvino::ObjectBoxList obj_now;
ros_openvino::ObjectBoxList obj_next;
bool flag_od_result_available = false;

void od_callback(ros_openvino::ObjectBoxList objects)
{
    if(!flag_od_result_available)
    {
        obj_now = objects;
        flag_od_result_available = true;
    } 
}

std::string labels_path;
std::string colors_path;

// string labels[] = {"background",
//           "aeroplane", "bicycle", "bird", "boat",
//           "bottle", "bus", "car", "cat", "chair",
//           "cow", "diningtable", "dog", "horse",
//           "motorbike", "person", "pottedplant",
//           "sheep", "sofa", "train", "tvmonitor"};

// string colors[] = { "BAA1D5",
//                                     "DC00A6"
//                                     "6625D1",
//                                     "F9F871",
//                                     "008CFF",
//                                     "006E53",
//                                     "CCFFFF",
//                                     "BF0000",
//                                     "FFBF46",
//                                     "FF5500",
//                                     "FFFFFF",
//                                     "808080",
//                                     "00FF00",
//                                     "A50096",
//                                     "008CFF",
//                                     "009BF9",
//                                     "00BD9B",
//                                     "B1A8B9",
//                                     "8D3D00",
//                                     "FF7C4F",
//                                     "FF2675"};
float dist_threshold[] = {0, 0, 0, 0, 0, 0.2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.6};

class Objection
{
public:
    string label;
    int cls_id;
    float x;
    float y;
    float z;
    Objection(string label_, int cls_id_, float x_, float y_, float z_):label(label_), x(x_), y(y_), z(z_){}

    bool isSameObjection(int cls_id_, float x_, float y_, float z_)
    {
        if(cls_id == cls_id_)
        {
            return false;
        }
        // 两者重心距离小于阈值，则认为是同一个物体
        float dist = sqrt(pow(x - x_, 2) + pow(y - y_, 2) + pow(z - z_, 2));
        if(dist < dist_threshold[cls_id])
        {
            // 如果是同一个物体，则更新当前物体的位置
            /**……**/
            return true;
        }
        return false;
    }

};
vector<Objection> obj_tag_list;

//Couple of hex in string format to uint value (FF->255)
uint8_t hexToUint8(std::string s){
    unsigned int x;
    std::stringstream ss;
    ss<<std::hex<<s;
    ss>>x;
    return x;
}


int main(int argc, char** argv)
{
    ros::init(argc, argv, "semantic_tagging");
    ros::NodeHandle nh;
	ros::Subscriber sub_pose = nh.subscribe("/object_detection/box_list", 10, od_callback);
    // 可视化
    ros::Publisher marker_pub = nh.advertise<visualization_msgs::MarkerArray>("/semantic_tagging/markers", 1);

    // 监听tf
    tf::TransformListener listener;
    tf::StampedTransform transform;

    ros::Rate rate(10.0);

    vector<Objection> objs_list; // 目标列表，存放各个目标在世界坐标系下的坐标

    visualization_msgs::Marker marker;
    visualization_msgs::MarkerArray markers;

    if (nh.getParam("/semantic_tagging/labels", labels_path)){
        ROS_INFO("Model Labels: %s", labels_path.c_str());
    }

    if (nh.getParam("/semantic_tagging/colors", colors_path)){
        ROS_INFO("Model Colors: %s", colors_path.c_str());
    }

try{
    std::vector<std::string> vector_labels;
    std::ifstream inputFileLabel(labels_path);
    std::copy(std::istream_iterator<std::string>(inputFileLabel),std::istream_iterator<std::string>(),std::back_inserter(vector_labels));
}
catch(exception ex)
{
    cout << ex.what() << endl;
}
    std::vector<std::string> vector_colors;
    std::ifstream inputFileColor(colors_path);
    std::copy(std::istream_iterator<std::string>(inputFileColor),std::istream_iterator<std::string>(),std::back_inserter(vector_colors));

    while(ros::ok())
    {
        try
        {
            listener.waitForTransform("/map", "/camera_link", ros::Time(0), ros::Duration(3.0));
            listener.lookupTransform("/map", "/camera_link", ros::Time(0), transform);
        }
        catch(tf::TransformException &ex)
        {
            ROS_ERROR("%s", ex.what());
            ros::Duration(1.0).sleep();
            continue;
        }

        
        if(flag_od_result_available)
        {
            ros_openvino::ObjectBoxList obj_list = obj_now;
            if(!obj_list.objectboxes.empty())
                ROS_INFO("%d target detected, the database has %d targets", obj_list.objectboxes.size(), obj_tag_list.size());
            
            while(!obj_list.objectboxes.empty())
            {
                Eigen::Quaterniond q(transform.getRotation().x(), transform.getRotation().y(), transform.getRotation().z(), transform.getRotation().w());
                Eigen::Vector3d t(transform.getOrigin().x(), transform.getOrigin().y(), transform.getOrigin().z());
                ros_openvino::ObjectBox obj = obj_list.objectboxes.back();

                // 目标物的相机坐标
                geometry_msgs::PointStamped p;
                p.header.frame_id = "camera_link";
                p.header.stamp = ros::Time();
                p.point.x = obj.x;
                p.point.y = obj.y;
                p.point.z = obj.z;
                
                // 目标物的世界坐标
                geometry_msgs::PointStamped pw;

                try
                {
                    // 相机坐标转换为世界坐标
                    listener.transformPoint("map", p, pw);

                    // 打印转换结果
                    ROS_INFO("camera_link: (%.2f, %.2f. %.2f) -----> map: (%.2f, %.2f, %.2f) at time %.2f", p.point.x, p.point.y, p.point.z, pw.point.x, pw.point.y, pw.point.z, pw.header.stamp.toSec());
                }
                catch(tf::TransformException& ex)
                {
                    ROS_ERROR("%s", ex.what());
                }

                // 添加到目标物列表
                if(obj.cls_id == 5 || obj.cls_id == 20)
                {
                    Objection temp(obj.label, obj.cls_id, pw.point.x, pw.point.y, pw.point.z);
                    bool isNewObj = true;
                    for(int i = 0; i < obj_tag_list.size(); i++)
                    {
                        if(obj_tag_list[i].isSameObjection(obj.cls_id, pw.point.x, pw.point.y, pw.point.z))
                        {
                            isNewObj = false;
                        }
                    }
                    cout << obj.cls_id << endl;
                    if(isNewObj)
                    {
                        ROS_INFO("Add 1 new target: %s", obj.label.c_str());
                        obj_tag_list.push_back(temp);

                        // 可视化
                        marker.header.frame_id = "/map";
                        marker.header.stamp = ros::Time::now();

                        stringstream ss;
                        ss << obj_tag_list.size();

                        marker.ns=obj.label.append("_").append(ss.str());
                        marker.id = obj_tag_list.size();
                        marker.type = visualization_msgs::Marker::CUBE;
                        marker.action = visualization_msgs::Marker::ADD;
                        marker.pose.position.x = pw.point.x;
                        marker.pose.position.y = pw.point.y;
                        marker.pose.position.z = pw.point.z;
                        marker.pose.orientation.x = 0.0;
                        marker.pose.orientation.y = 0.0;
                        marker.pose.orientation.z = 0.0;
                        marker.pose.orientation.w = 1.0;
                        marker.scale.x = obj.depth;
                        marker.scale.y =obj.width;
                        marker.scale.z = obj.height;

                        // string color = (obj.cls_id < vector_colors.size() ? vector_colors[obj.cls_id].c_str() : string("00FF00"));
                        // uint8_t colorR = hexToUint8(color.substr(0,2));
                        // uint8_t colorG = hexToUint8(color.substr(2,2));
                        // uint8_t colorB = hexToUint8(color.substr(4,2));

                        // marker.color.r = colorR/255.0;
                        // marker.color.g = colorG/255.0;
                        // marker.color.b = colorB/255.0;
                        marker.color.a = 0.6f;

                        markers.markers.push_back(marker);
                    }
                }
                obj_list.objectboxes.pop_back();
            }
            marker_pub.publish(markers);
             flag_od_result_available = false;
        }

        ros::spinOnce();
        rate.sleep();
    }
}


