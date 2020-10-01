#include <iostream>
#include <string>
#include <sstream>
using namespace std;

#include "ros/ros.h"
#include "std_msgs/String.h"
#include "serial/serial.h"

#include "serial_node/serial_msg.h"
#include<nav_msgs/Odometry.h>  
#include <tf/transform_broadcaster.h>


#define sBUFFER_SIZE 1024
#define rBUFFER_SIZE 1024
unsigned char s_buffer[sBUFFER_SIZE];
unsigned char r_buffer[rBUFFER_SIZE];

serial::Serial ser;
typedef union
{
	float data;
	unsigned char data8[4];
} data_u;


void cmd_callback(const geometry_msgs::Twist::ConstPtr& cmd_vel)
{
    uint8_t _cnt = 0;
    data_u _temp; // 声明一个联合体实例，使用它将待发送数据转换为字节数组
	uint8_t data_to_send[14]; // 待发送的字节数组
	
	data_to_send[_cnt++]=0xAA;
		
	// 将要发送的数据赋值给联合体的float成员
	// 相应的就能更改字节数组成员的值
	_temp.data = cmd_vel->linear.x;
	data_to_send[_cnt++]=_temp.data8[0];
	data_to_send[_cnt++]=_temp.data8[1];
	data_to_send[_cnt++]=_temp.data8[2];
	data_to_send[_cnt++]=_temp.data8[3]; // 最高位
	
	_temp.data = cmd_vel->linear.y;
	data_to_send[_cnt++]=_temp.data8[0];
	data_to_send[_cnt++]=_temp.data8[1];
	data_to_send[_cnt++]=_temp.data8[2];
	data_to_send[_cnt++]=_temp.data8[3]; // 最高位
	
	_temp.data = cmd_vel->angular.z;
	data_to_send[_cnt++]=_temp.data8[0];
	data_to_send[_cnt++]=_temp.data8[1];
	data_to_send[_cnt++]=_temp.data8[2];
	data_to_send[_cnt++]=_temp.data8[3]; // 最高位

    char checkout = 0;
    for(int i = 1; i < _cnt; i++)
    {
        checkout += data_to_send[i];
    }
	data_to_send[_cnt++] = checkout;

    // 串口发送
    ser.write(data_to_send, 14);
}


int main(int argc, char** argv)
{
	ros::init(argc, argv, "serial_node");
	ros::NodeHandle nh;

	// 打开串口
	try
	{
		ser.setPort("/dev/ttyACM0");
		ser.setBaudrate(115200);
		serial::Timeout to = serial::Timeout::simpleTimeout(1000);
		ser.setTimeout(to);
		ser.open();
	}
	catch(serial::IOException &e)
	{
		ROS_INFO_STREAM("Failed to open port ");
		return -1;
	}
	ROS_INFO_STREAM("Succeed to open port" );

	int cnt = 0;
	ros::Publisher odom_pub = nh.advertise<nav_msgs::Odometry>("odom", 50);
	tf::TransformBroadcaster odom_broadcaster;
	ros::Subscriber sub = nh.subscribe("/cmd_vel", 10, cmd_callback);

	nav_msgs::Odometry odom;
	geometry_msgs::TransformStamped odom_trans;

	double x = 0.0;
	double y = 0.0;
	double th = 0.0;

	double vx = 0.1;
	double vy = -0.1;
	double vth = 0.1;

	ros::Time current_time, last_time;
	current_time = ros::Time::now();
 	last_time = ros::Time::now();

	int state = 0;
	unsigned char data_receive[16] = {0};
    while(ros::ok())
	{
		serial_node::serial_msg msg;
		if(ser.available())
		{
            uint8_t buffer = 0;
			size_t bytes_read = ser.read(&buffer, 1);

			if(state == 0 && buffer == 0xAA)
			{
				state++;
			}
			else if(state == 1 && buffer == 0xEE)
			{
				state++;
			}
			else if(state >= 2 && state < 19)
			{
				data_receive[state-2]=buffer;
				state ++;
				if(state == 19)
				{
					uint8_t checkout = 0;
					for(int k = 0; k < 16; k++)
					{
						checkout += data_receive[k];
					}
					if(checkout == data_receive[16])
					{
							data_u temp;
							temp.data8[0] = data_receive[0];
							temp.data8[1] = data_receive[1];
							temp.data8[2] = data_receive[2];
							temp.data8[3] = data_receive[3];							
							vx =temp.data;
							temp.data8[0] = data_receive[4];
							temp.data8[1] = data_receive[5];
							temp.data8[2] = data_receive[6];
							temp.data8[3] = data_receive[7];							
							vy =temp.data;
							temp.data8[0] = data_receive[8];
							temp.data8[1] = data_receive[9];
							temp.data8[2] = data_receive[10];
							temp.data8[3] = data_receive[11];							
							vth=temp.data;
							temp.data8[0] = data_receive[12];
							temp.data8[1] = data_receive[13];
							temp.data8[2] = data_receive[14];
							temp.data8[3] = data_receive[15];							
							th = temp.data / 180.0 * 3.1415926535; // 转换为弧度

							current_time = ros::Time::now();
							
							double dt = (current_time - last_time).toSec();
							double delta_x = (vx * cos(th) - vy * sin(th)) * dt;
							double delta_y = (vx * sin(th) + vy * cos(th)) * dt;
							x += delta_x;
							y += delta_y;

							geometry_msgs::Quaternion odom_quat = tf::createQuaternionMsgFromYaw(th);
							odom_trans.header.stamp = current_time;
							odom_trans.header.frame_id = "odom";
							odom_trans.child_frame_id = "base_link";

							odom_trans.transform.translation.x = x;
							odom_trans.transform.translation.y = y;
							odom_trans.transform.translation.z = 0.0;
							odom_trans.transform.rotation = odom_quat;
							//send the transform
							odom_broadcaster.sendTransform(odom_trans);
							odom.header.stamp = current_time;
							odom.header.frame_id = "odom";

							//set the position
							odom.pose.pose.position.x = x;
							odom.pose.pose.position.y = y;
							odom.pose.pose.position.z = 0.0;
							odom.pose.pose.orientation = odom_quat;

							//set the velocity
							odom.child_frame_id = "base_link";
							odom.twist.twist.linear.x = vx;
							odom.twist.twist.linear.y = vy;
							odom.twist.twist.angular.z = vth;

							//publish the message
							odom_pub.publish(odom);

							last_time = current_time;
					}					
					ROS_INFO("%f, %f, %f,", x, y, th);

					state = 0;
				}
			}
			else state = 0;
		}

		ros::spinOnce();
		cnt++;
	}
	ser.close();

	return 0;
}