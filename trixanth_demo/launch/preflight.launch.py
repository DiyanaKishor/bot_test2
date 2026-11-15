"""Safe software-only preflight. No Nav2, motor outputs or dummy wheel odometry."""
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(package='trixanth_demo',executable='phone_udp_bridge',output='screen'),
        Node(package='trixanth_demo',executable='pointcloud_guard',output='screen'),
        Node(package='trixanth_demo',executable='preflight_status',output='screen'),
        Node(package='trixanth_demo',executable='dry_run_motor',output='screen'),
    ])
