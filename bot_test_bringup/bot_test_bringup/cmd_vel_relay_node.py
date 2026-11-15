#!/usr/bin/env python3
"""
cmd_vel_relay_node.py -- relays geometry_msgs/Twist to geometry_msgs/TwistStamped.

Almost every teleop tool, joystick driver, or custom control script publishes
plain Twist on the standard /cmd_vel topic. diff_drive_controller (this ROS 2
Jazzy / ros2_controllers release) requires TwistStamped instead. This node
bridges the two so any standard tool "just works" without needing to know
about the controller's specific topic name or message type.

Topic names are ROS parameters (not hardcoded) so this can be reused as-is
if the controller or topic naming ever changes -- just override via launch
arguments instead of editing/rebuilding source.

Params:
    input_topic  (string, default: /cmd_vel)
    output_topic (string, default: /diff_drive_controller/cmd_vel)
    frame_id     (string, default: base_link)
"""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped


class CmdVelRelay(Node):
    def __init__(self):
        super().__init__('cmd_vel_relay')

        self.declare_parameter('input_topic', '/cmd_vel')
        self.declare_parameter('output_topic', '/diff_drive_controller/cmd_vel')
        self.declare_parameter('frame_id', 'base_link')

        input_topic = self.get_parameter('input_topic').value
        output_topic = self.get_parameter('output_topic').value
        self.frame_id = self.get_parameter('frame_id').value

        self.subscription = self.create_subscription(
            Twist, input_topic, self.cmd_vel_callback, 10
        )
        self.publisher = self.create_publisher(TwistStamped, output_topic, 10)

        self.get_logger().info(
            f'cmd_vel_relay started: {input_topic} (Twist) -> {output_topic} (TwistStamped)'
        )

    def cmd_vel_callback(self, msg: Twist):
        stamped = TwistStamped()
        stamped.header.stamp = self.get_clock().now().to_msg()
        stamped.header.frame_id = self.frame_id
        stamped.twist = msg
        self.publisher.publish(stamped)


def main(args=None):
    rclpy.init(args=args)
    node = CmdVelRelay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()