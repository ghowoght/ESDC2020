#ifndef __MOTOR_H__
#define __MOTOR_H__

#include "sys.h"

extern uint32_t ADC_Value[50]; 

typedef struct 
{
		volatile float linear_x;  // x轴线速度 m/s
		volatile float linear_y;  // y轴线速度 m/s
		volatile float angular_z; // z轴角速度 rad/s 右手准则
}vel_st; 

typedef struct
{
	float motor_1;
	float motor_2;
	float motor_3;
	float motor_4;
}motor_st;

typedef struct
{
	int motor_1;
	int motor_2;
	int motor_3;
	int motor_4;
}rpm_st;

typedef struct
{
	float x;
	float y;
	float theta;
}pose_st;

typedef struct
{
	vel_st vel; // 速度
	pose_st pose; // 位姿
}odom_st;
extern odom_st odom;

typedef struct
{
	int max_rpm_; // 每分钟车轮的最大转速
	float wheels_x_distance_;
	float wheels_y_distance_;
	float pwm_res_;
	float wheel_circumference_;
	int total_wheels_;
	
	vel_st exp_vel;		// 小车整体的目标速度
	vel_st fb_vel;		// 测量得到的小车整体速度
	rpm_st exp_wheel_rpm;	// 使用逆运动学模型转换得到的轮子的目标转速
	motor_st fb_wheel_cmps;	// 编码器反馈值 cm/s
	rpm_st fb_wheel_rpm;	// 编码器反馈值 rad/min
	motor_st pwm;	// 电机的PWM输出值
}kinematics_st;
extern kinematics_st kinematics;



//定义PID
typedef struct
{
	float kp;							// 比例系数
	float ki;							// 积分系数
	float kd;							// 微分系数
	
	float err;						// 误差
	float err_last;				// 前一次的误差
	float err_inte;				// 误差积分
	float err_diff;				// 误差微分

	float expect;					// 目标值
	float expect_last;		// 前一次的目标值
	float feedback;				// 反馈值
	float feedback_last;	// 前一次的反馈值
	
	float out;						// PID输出
}pid_st;
extern pid_st pid[4];
extern pid_st pid_yaw;

void Kinematics_Init(void);
void Encoder_Task(u32 dT_us);

void Set_Speed(void);
void PID_Init(void);
void Motor_Task(u32 dT_us);
void data_encoder(uint8_t data);

void Exp_Speed_Cal(void);
void Fb_Speed_Cal(void);

void PID_Controller( u32 dT_us,
										float expect, 
										float feedback, 
										pid_st *pid,
										float inte_d_lim, // 单次积分限幅
										float inte_lim // 积分限幅
											);
										
float Get_MiMx(float x, float min, float max );
										
void Power_Task(u32 dT_ms);

#endif 
