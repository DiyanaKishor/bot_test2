#!/usr/bin/env python3

import os
from pathlib import Path
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg = get_package_share_directory('bot_test_description')
    xacro_file = os.path.join(pkg, 'urdf', 'bot_test.xacro')
    rviz_config_path = os.path.join(pkg, 'rviz', 'display.rviz')

    #robot_description = Command(['xacro ', xacro_file])
    robot_description = ParameterValue(
        Command([
            'xacro ',
            LaunchConfiguration('urdf_model')
        ]),
    value_type=str
    )

    return LaunchDescription([

        # --- Launch arguments (robot/xacro args) ---
        DeclareLaunchArgument('robot_name',     default_value='bot_test'),
        DeclareLaunchArgument('prefix',         default_value=''),
        DeclareLaunchArgument('use_gazebo',     default_value='false',  choices=['true', 'false']),
        DeclareLaunchArgument('enable_odom_tf', default_value='true',   choices=['true', 'false']),

        # --- Launch arguments (node toggles) ---
        DeclareLaunchArgument('use_sim_time',   default_value='false'),
        DeclareLaunchArgument('use_rviz',       default_value='true'),
        DeclareLaunchArgument('use_jsp',        default_value='false',  choices=['true', 'false']),
        DeclareLaunchArgument('jsp_gui',        default_value='true',   choices=['true', 'false']),

        # --- Launch arguments (file paths) ---
        DeclareLaunchArgument('urdf_model',      default_value=xacro_file),
        DeclareLaunchArgument('rviz_config_file', default_value=rviz_config_path),

        # --- Robot State Publisher ---
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'robot_description': robot_description
            }]
        ),

        # --- Joint State Publisher (headless, no GUI) ---
        Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            name='joint_state_publisher',
            parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
            condition=IfCondition(LaunchConfiguration('use_jsp'))
        ),

        # --- Joint State Publisher GUI ---
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui',
            parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
            condition=IfCondition(LaunchConfiguration('jsp_gui'))
        ),

        # --- RViz ---
        Node(
            package='rviz2',
            executable='rviz2',
            output='screen',
            arguments=['-d', LaunchConfiguration('rviz_config_file')],
            parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
            condition=IfCondition(LaunchConfiguration('use_rviz'))
        ),

    ])