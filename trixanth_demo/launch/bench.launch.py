"""Software-only bench: no EKF, no Nav2, no serial driver and no motors."""
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(package='trixanth_demo',executable='phone_udp_bridge',output='screen'),
        Node(package='trixanth_demo',executable='dry_run_motor',output='screen'),
        Node(package='trixanth_comms',executable='command_gate',output='screen'),
    ])
