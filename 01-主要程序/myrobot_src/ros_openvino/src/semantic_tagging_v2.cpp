#include <iostream>
#include <string>
#include <sstream>
#include <fstream>
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
float explore_depth;

float dist_threshold[] = {0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 1};

vector<string> vector_colors;
vector<string> vector_labels;
vector<float> vector_thickness;
vector<float> vector_dist_threshold;

class Objection
{
public:
    string label;
    int cls_id;
    float x;
    float y;
    float z;
    Objection(string label_, int cls_id_, float x_, float y_, float z_):label(label_), cls_id(cls_id_), x(x_), y(y_), z(z_){}

    bool isSameObjection(int cls_id_, float x_, float y_, float z_)
    {
        // 两者标签不同，则必定不是同一目标
        if(cls_id != cls_id_)
        {
            return false;
        }
        // 两者重心距离小于阈值，则认为是同一个物体
        float dist = sqrt(pow(x - x_, 2) + pow(y - y_, 2) + pow(z - z_, 2));
        if(dist < vector_dist_threshold[cls_id])
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

    if (nh.getParam("/semantic_tagging/explore_depth", explore_depth)){
        ROS_INFO("explore_depth: %f", explore_depth);
    }

    vector_colors.clear();
    vector_labels.clear();

    if (nh.getParam("/semantic_tagging/config", colors_path)){
        ROS_INFO("Configs: %s", colors_path.c_str());
    }
    ifstream infile(colors_path.c_str());    
    string str;
    while(infile >> str)
    {
        vector_labels.push_back(str);
        cout << vector_labels.back() << endl;
        infile >> str;
        vector_colors.push_back(str);
        cout << vector_colors.back() << endl;
        float temp;
        infile >> temp;
        vector_thickness.push_back(temp);
        cout << vector_thickness.back() << endl;
        infile >> temp;
        vector_dist_threshold.push_back(temp);
        cout << vector_dist_threshold.back() << endl;        
    }
    infile.close();
    

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


    while(ros::ok())
    {
        try
        {
            // 监听从camera_link到map的转换
            listener.waitForTransform("/map", "/camera_link", ros::Time(0), ros::Duration(3.0));
            listener.lookupTransform("/map", "/camera_link", ros::Time(0), transform);
        }
        catch(tf::TransformException &ex)
        {
            ROS_ERROR("%s", ex.what());
            ros::Duration(1.0).sleep();
            continue;
        }

        // 如果有新检测到的目标
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
                obj_list.objectboxes.pop_back(); // 删掉最后一个
                // 如果大于探测距离，则略过
                if(obj.x > explore_depth)
                    continue;

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
                    string label = vector_labels[obj.cls_id];
                    Objection temp(label, obj.cls_id, pw.point.x, pw.point.y, pw.point.z);
                    bool isNewObj = true;
                    for(int i = 0; i < obj_tag_list.size(); i++)
                    {
                        if(obj_tag_list[i].isSameObjection(obj.cls_id, pw.point.x, pw.point.y, pw.point.z))
                        {
                            isNewObj = false;
                        }
                    }
                    if(isNewObj)
                    {
                        ROS_INFO("Add 1 new target: %s", obj.label.c_str());
                        obj_tag_list.push_back(temp);

                        // 可视化
                        marker.header.frame_id = "/map";
                        marker.header.stamp = ros::Time::now();
                        stringstream ss;
                        ss << obj_tag_list.size();
                        marker.ns=label.append("_").append(ss.str()); //在标签后添加一个id
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
                        marker.scale.x = vector_thickness[obj.cls_id];//obj.depth;
                        marker.scale.y =obj.width;
                        marker.scale.z = obj.height;

                        string color = (obj.cls_id < vector_colors.size() ? vector_colors[obj.cls_id] : string("00FF00"));
                        uint8_t colorR = hexToUint8(color.substr(0,2));
                        uint8_t colorG = hexToUint8(color.substr(2,2));
                        uint8_t colorB = hexToUint8(color.substr(4,2));

                        marker.color.r = colorR/255.0;
                        marker.color.g = colorG/255.0;
                        marker.color.b = colorB/255.0;
                        marker.color.a = 0.6f;

                        markers.markers.push_back(marker);
                    }
                }
                
            }
            marker_pub.publish(markers);
             flag_od_result_available = false;
        }

        ros::spinOnce();
        rate.sleep();
    }
}


