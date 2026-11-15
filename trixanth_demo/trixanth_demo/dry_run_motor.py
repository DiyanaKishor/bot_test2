"""NO GPIO OR MOTORS: prints /cmd_vel after the existing command_gate."""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
class DryRunMotor(Node):
    def __init__(self):
        super().__init__('dry_run_motor')
        self.create_subscription(Twist,'/cmd_vel',self.on_cmd,10)
        self.last=self.get_clock().now()
        self.create_timer(0.25,self.watchdog)
        self.get_logger().warning('DRY-RUN only; no GPIO, no serial, no motor output')
    def on_cmd(self,msg):
        self.last=self.get_clock().now()
        self.get_logger().info(f'cmd_vel: forward={msg.linear.x:+.3f} m/s turn={msg.angular.z:+.3f} rad/s',throttle_duration_sec=0.5)
    def watchdog(self):
        if (self.get_clock().now()-self.last).nanoseconds>1000000000:
            self.get_logger().warning('No /cmd_vel received in >1 sec',throttle_duration_sec=5.)
def main():
    rclpy.init();node=DryRunMotor()
    try:rclpy.spin(node)
    except KeyboardInterrupt:pass
    finally:node.destroy_node();rclpy.shutdown()
