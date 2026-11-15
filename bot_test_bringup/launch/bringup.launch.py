#!/usr/bin/env python3
"""
bringup.launch.py -- Phase 7 orchestration only.

This file does NOT define any new nodes, controllers, or logic. It only:
  1. Includes bot_test_gazebo/launch/gazebo_sim.launch.py, which already does
     everything: starts Gazebo, robot_state_publisher, spawns the robot,
     chains joint_state_broadcaster -> diff_drive_controller, and starts the
     ros_gz bridge (clock, scan, imu).
  2. Starts RViz directly (using bot_test_description's rviz config), since
     re-including bot_test_description's own launch file would spin up a
     second robot_state_publisher and duplicate the TF tree.
  3. Starts cmd_vel_relay_node (already written, in this package) so any
     standard Twist publisher (teleop_twist_keyboard, joysticks, Nav2 later)
     works without needing to know diff_drive_controller expects
     TwistStamped.

One command should boot the whole simulated robot: drivable, sensors live.
"""
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch.actions import ExecuteProcess


def generate_launch_description():

    pkg_gazebo = get_package_share_directory('bot_test_gazebo')
    pkg_description = get_package_share_directory('bot_test_description')

    rviz_config_path = os.path.join(pkg_description, 'rviz', 'display.rviz')

    return LaunchDescription([

        # --- Launch arguments (passthrough to gazebo_sim.launch.py) ---
        DeclareLaunchArgument('robot_name',   default_value='bot_test'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='0.2'),
        DeclareLaunchArgument('world', default_value=os.path.join(
            pkg_gazebo, 'worlds', 'blocks.world'
        )),

        # --- Launch arguments (bringup-level toggles) ---
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument('rviz_config_file', default_value=rviz_config_path),

        # --- Everything sim-related: Gazebo, RSP, spawn, controllers, bridge ---
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_gazebo, 'launch', 'gazebo_sim.launch.py')
            ),
            launch_arguments={
                'robot_name':   LaunchConfiguration('robot_name'),
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'x': LaunchConfiguration('x'),
                'y': LaunchConfiguration('y'),
                'z': LaunchConfiguration('z'),
                'world': LaunchConfiguration('world'),
            }.items()
        ),

        # --- RViz (started directly, not via bot_test_description's launch
        #     file, to avoid a duplicate robot_state_publisher / TF tree) ---
        Node(
            package='rviz2',
            executable='rviz2',
            output='screen',
            arguments=['-d', LaunchConfiguration('rviz_config_file')],
            parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
            condition=IfCondition(LaunchConfiguration('use_rviz'))
        ),

        # --- cmd_vel relay: Twist (from teleop/Nav2/joystick) -> TwistStamped
        #     (required by diff_drive_controller with use_stamped_vel: true) ---
        Node(
            package='bot_test_bringup',
            executable='cmd_vel_relay_node',
            name='cmd_vel_relay',
            output='screen',
            parameters=[{
                'input_topic': '/cmd_vel',
                'output_topic': '/diff_drive_controller/cmd_vel',
                'frame_id': 'base_link',
            }]
        ),

        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[
                os.path.join(get_package_share_directory('bot_test_bringup'), 'config', 'ekf.yaml'),
                {'use_sim_time': LaunchConfiguration('use_sim_time')}
            ]
        ),


        Node(
            package='twist_mux',
            executable='twist_mux',
            name='twist_mux',
            output='screen',
            parameters=[os.path.join(
                get_package_share_directory('bot_test_bringup'),
                'config', 'twist_mux.yaml'
            )],
            remappings=[('cmd_vel_out', '/cmd_vel')]
        ),


        Node(
            package='rosbridge_server',
            executable='rosbridge_websocket',
            name='rosbridge_websocket',
            output='screen',
            parameters=[{'port': 9090}]
        ),

        ExecuteProcess(
            cmd=['python3', '-m', 'http.server', '8000'],
            cwd=os.path.join(
                get_package_share_directory('bot_test_bringup'),
                'web'
            ),
            output='screen'
        ),

    ])
