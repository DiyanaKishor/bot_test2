"""Phone GPS + IMU experiment; no AMCL, no wheel odometry, no motor control."""
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from pathlib import Path

def generate_launch_description():
    yaml_path = str(Path(get_package_share_directory('trixanth_demo'))/'config'/'ekf_phone.yaml')
    return LaunchDescription([
        Node(package='trixanth_demo', executable='phone_udp_bridge',output='screen'),
        Node(package='trixanth_demo', executable='gps_local_odom',output='screen'),
        Node(package='robot_localization',executable='ekf_node',name='ekf_phone',parameters=[yaml_path],output='screen'),
    ])
