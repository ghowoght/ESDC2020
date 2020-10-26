#include <iostream>
#include <string>
#include <sstream>
#include <fstream>
using namespace std;

std::string colors_path;

int main(void)
{
    // vector<string> vector_colors;

    ifstream infile("/home/ghowoght/workplace/myrobot/src/ros_openvino/config/labels.txt");

    string str;
    while( getline(infile, str))
    {
        // vector_colors.push_back(str);
        cout << str << endl;
    }
    // cout << str << endl;
}