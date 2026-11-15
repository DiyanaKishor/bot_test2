#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_description = get_package_share_directory('bot_test_description')
    pkg_gazebo = get_package_share_directory('bot_test_gazebo')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    xacro_file = os.path.join(pkg_description, 'urdf', 'bot_test.xacro')
    world_file = os.path.join(pkg_gazebo, 'worlds', 'blocks.world')
    bridge_config_file = os.path.join(pkg_gazebo, 'config', 'ros_gz_bridge.yaml')

    robot_description = ParameterValue(
        Command([
            'xacro ',
            LaunchConfiguration('urdf_model')
        ]),
        value_type=str
    )

    # Needs to be a variable (not inline) so the event handler below can target it --
    # everything else in this file stays inline in the return list as before.
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-topic', '/robot_description',
            '-name', LaunchConfiguration('robot_name'),
            '-x', LaunchConfiguration('x'),
            '-y', LaunchConfiguration('y'),
            '-z', LaunchConfiguration('z'),
        ]
    )

    # Same reason -- the next event handler chains off this one.
    jsb_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster'],
        output='screen'
    )

    return LaunchDescription([

        # --- Launch arguments (robot/xacro args) ---
        DeclareLaunchArgument('robot_name',   default_value='bot_test'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),

        # --- Launch arguments (spawn pose) ---
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='0.2'),

        # --- Launch arguments (node toggles) ---
        DeclareLaunchArgument('use_robot_state_pub', default_value='true'),
        DeclareLaunchArgument('use_bridge',          default_value='true'),

        # --- Launch arguments (file paths) ---
        DeclareLaunchArgument('urdf_model',   default_value=xacro_file),
        DeclareLaunchArgument('world',        default_value=world_file),
        DeclareLaunchArgument('bridge_config', default_value=bridge_config_file),

        # --- Gazebo resource path (so it can find our meshes) ---
        SetEnvironmentVariable(
            'GZ_SIM_RESOURCE_PATH',
            os.path.join(pkg_description, '..')
        ),

        # --- Gazebo Sim ---
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
            ),
            launch_arguments={
                'gz_args': [LaunchConfiguration('world'), ' -r']
            }.items()
        ),

        # --- Robot State Publisher ---
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'robot_description': robot_description
            }],
            condition=IfCondition(LaunchConfiguration('use_robot_state_pub'))
        ),

        # --- Spawn robot into Gazebo from /robot_description ---
        spawn_robot,

        # --- Load joint_state_broadcaster once the robot has finished spawning ---
        # (controller_manager exists as soon as gz_ros2_control starts, but it never
        # auto-loads controllers -- this is the deliberate, explicit step that does.)
        RegisterEventHandler(
            OnProcessExit(
                target_action=spawn_robot,
                on_exit=[jsb_spawner]
            )
        ),

        # --- Load diff_drive_controller once joint_state_broadcaster is up ---
        # (chained the same way -- one controller confirmed working before the next loads)
        RegisterEventHandler(
            OnProcessExit(
                target_action=jsb_spawner,
                on_exit=[
                    Node(
                        package='controller_manager',
                        executable='spawner',
                        arguments=['diff_drive_controller'],
                        output='screen'
                    )
                ]
            )
        ),

        # --- ROS <-> Gazebo bridge (clock, sensors, cmd_vel, etc.) ---
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='ros_gz_bridge',
            output='screen',
            arguments=['--ros-args', '-p', ['config_file:=', LaunchConfiguration('bridge_config')]],
            condition=IfCondition(LaunchConfiguration('use_bridge'))
        ),

    ])

#pkill -9 -f gz