cmake_minimum_required(VERSION 2.8.3)
project(xrobot)

## Compile as C++11, supported in ROS Kinetic and newer
# add_compile_options(-std=c++11)

## Find catkin macros and libraries
## if COMPONENTS list like find_package(catkin REQUIRED COMPONENTS xyz)
## is used, also find other catkin packages
find_package(catkin REQUIRED COMPONENTS
  message_generation
  roscpp
  rospy
  serial
  std_msgs
  tf
)

# add_message_files(
#   FILES
# )
# generate_messages(
#   DEPENDENCIES
# )

catkin_package(
 CATKIN_DEPENDS
 message_runtime
)

# 头文件路径
include_directories(
include
  ${catkin_INCLUDE_DIRS}
)

# 生成可执行文件
add_executable( robot_node src/robot_node.cpp )
#该项让编译器知道要注意编译顺序
add_dependencies(robot_node ${${PROJECT_NAME}_EXPORTED_TARGETS} ${catkin_EXPORTED_TARGETS}) 

# 链接库
target_link_libraries(robot_node ${catkin_LIBRARIES})