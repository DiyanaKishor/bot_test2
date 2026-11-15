import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    nav_pkg = get_package_share_directory('bot_test_navigation')

    map_yaml = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')
    use_sim_time = LaunchConfiguration('use_sim_time')

    default_map = os.path.join(nav_pkg, 'maps', 'office_map.yaml') 
    default_params = os.path.join(nav_pkg, 'config', 'nav2_params.yaml')

    declare_map = DeclareLaunchArgument(
        'map', default_value=default_map,
        description='Full path to map yaml file to load')

    declare_params = DeclareLaunchArgument(
        'params_file', default_value=default_params,
        description='Full path to nav2 params yaml file')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use simulation clock')

    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'localization_launch.py')),
        launch_arguments={
            'map': map_yaml,
            'use_sim_time': use_sim_time,
            'params_file': params_file,
            'autostart': 'true'
        }.items()
    )

    return LaunchDescription([
        declare_map,
        declare_params,
        declare_use_sim_time,
        localization_launch,
    ])