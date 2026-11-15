"""Conservative obstacle presence indicator. Does NOT command motors."""
import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2
from std_msgs.msg import Bool

class Guard(Node):
    def __init__(self):
        super().__init__('pointcloud_guard')
        self.declare_parameter('cloud_topic','/camera/depth/points')
        self.declare_parameter('stop_distance_m',0.8)
        self.declare_parameter('width_m',0.75)
        self.declare_parameter('cloud_frame_is_base_link',False)
        self.out=self.create_publisher(Bool,'/demo/obstacle_stop',10)
        self.t=self.get_clock().now()
        self.hazard=True
        self.create_subscription(PointCloud2,self.get_parameter('cloud_topic').value,self.cb,10)
        self.create_timer(0.2,self.tick)
        self.get_logger().warning('Monitor ONLY. Expects pointcloud axes in base_link (x forward y left z up). Defaults STOP until configured.')
    def cb(self,msg):
        self.t=self.get_clock().now()
        if not self.get_parameter('cloud_frame_is_base_link').value:
            self.hazard=True
            return
        stop=float(self.get_parameter('stop_distance_m').value)
        width=float(self.get_parameter('width_m').value)
        hits=0
        try:
            for i,p in enumerate(point_cloud2.read_points(msg,field_names=('x','y','z'),skip_nans=True)):
                if i % 4: continue
                x,y,z=map(float,p)
                if all(math.isfinite(v) for v in (x,y,z)) and 0.08 < x < stop and abs(y) < width/2 and -0.10 < z < 0.7:
                    hits+=1
                    if hits>=6:break
            self.hazard=hits>=6
        except (ValueError,TypeError,KeyError) as e:
            self.hazard=True
            self.get_logger().error(f'Unable to decode pointcloud: {e}',throttle_duration_sec=5.)
    def tick(self):
        stale=(self.get_clock().now()-self.t).nanoseconds>500000000
        self.out.publish(Bool(data=self.hazard or stale))
def main():
    rclpy.init();n=Guard()
    try:rclpy.spin(n)
    except KeyboardInterrupt:pass
    finally:n.destroy_node();rclpy.shutdown()
