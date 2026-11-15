#!/usr/bin/env python3
import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

def create_pose(navigator, x, y, yaw_w=1.0, yaw_z=0.0):
    """Utility helper to build a stamped pose in the map frame."""
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.orientation.z = yaw_z
    pose.pose.orientation.w = yaw_w
    return pose

def main():
    rclpy.init()
    navigator = BasicNavigator()

    # 1. Wait until Nav2 lifecycle nodes are fully ACTIVE
    print("Waiting for Nav2 to become fully active...")
    navigator.waitUntilNav2Active()

    # 2. Define mission waypoints [x, y, orient_w, orient_z]
    waypoints = [
        create_pose(navigator, 2.0, 1.0, yaw_w=1.0, yaw_z=0.0),
        create_pose(navigator, 0.0, 0.0, yaw_w=0.707, yaw_z=0.707),
        create_pose(navigator, 4.0, 2.5, yaw_w=0.0, yaw_z=1.0),
        create_pose(navigator, 0.0, 0.0, yaw_w=1.0, yaw_z=0.0),
    ]

    # 3. Send the waypoint list to waypoints action server
    print("Starting Waypoint Patrol...")
    navigator.followWaypoints(waypoints)

    # 4. Monitor progress loop
    i = 0
    while not navigator.isTaskComplete():
        i += 1
        feedback = navigator.getFeedback()
        if feedback and i % 5 == 0:  # Throttled print
            print(f'Currently executing waypoint: {feedback.current_waypoint}')

    # 5. Check outcome
    result = navigator.getResult()
    if result == TaskResult.SUCCEEDED:
        print('Patrol completed successfully!')
    elif result == TaskResult.CANCELED:
        print('Patrol task was canceled!')
    elif result == TaskResult.FAILED:
        print('Patrol task failed!')

    rclpy.shutdown()

if __name__ == '__main__':
    main()



#chmod +x way_point_test.py
# 
# this will connvert the .py files to executable scripts
# How Linux permission works: Unlike Windows, Linux does not allow a file to run as a program just because it has a .py extension.
# It checks permission flags on the file. chmod stands for CHange MODe, and +x adds the eXecute flag.

# Why ROS 2 requires it: When you run a script using ros2 run <package> <script> or install it using CMake's install(PROGRAMS ...), 
# ROS 2 attempts to launch the script directly as a standalone program. Without the +x flag, Linux blocks ROS 2 from launching it, 
# resulting in a Permission denied or Executable not found error.   