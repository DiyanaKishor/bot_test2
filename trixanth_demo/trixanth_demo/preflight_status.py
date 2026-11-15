"""Check interfaces are discoverable; never fabricate hardware measurements."""
import rclpy
from rclpy.node import Node

TOPICS=['/imu/data','/gps/fix','/camera/depth/points','/cmd_vel_teleop','/cmd_vel_auto','/cmd_vel']
class PreflightStatus(Node):
    def __init__(self):
        super().__init__('preflight_status')
        self.create_timer(5.0,self.report)
        self.report()
    def report(self):
        for t in TOPICS:
            pubs=self.get_publishers_info_by_topic(t)
            self.get_logger().info(f'{t}: {len(pubs)} publisher(s) discovered',throttle_duration_sec=4.0)
        self.get_logger().warning('Publisher discovery is NOT proof of valid sensor data or a safe motor control path',throttle_duration_sec=20.)
def main():
    rclpy.init();n=PreflightStatus()
    try:rclpy.spin(n)
    except KeyboardInterrupt:pass
    finally:n.destroy_node();rclpy.shutdown()
