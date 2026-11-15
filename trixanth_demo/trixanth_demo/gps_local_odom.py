"""Convert phone NavSatFix to local ENU position for experimental EKF visualization.
Do NOT treat this as wheel odometry or reliable Nav2 tracking.
"""
import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, NavSatStatus
from nav_msgs.msg import Odometry

class GpsLocalOdom(Node):
    def __init__(self):
        super().__init__('gps_local_odom')
        self.declare_parameter('origin_lat_deg',float('nan'))
        self.declare_parameter('origin_lon_deg',float('nan'))
        self.declare_parameter('auto_origin',True)
        self.origin_lat=float(self.get_parameter('origin_lat_deg').value)
        self.origin_lon=float(self.get_parameter('origin_lon_deg').value)
        self.publisher=self.create_publisher(Odometry,'/odometry/phone_gps',10)
        self.create_subscription(NavSatFix,'/gps/fix',self.on_fix,10)
        self.get_logger().warning('GPS-only POSITION, no wheel odometry. EKF output is experimental, not Nav2-ready.')
    def on_fix(self,msg):
        if msg.status.status < NavSatStatus.STATUS_FIX:return
        lat,lon=msg.latitude,msg.longitude
        if not (math.isfinite(lat) and math.isfinite(lon) and abs(lat)<=90 and abs(lon)<=180):return
        if not(math.isfinite(self.origin_lat) and math.isfinite(self.origin_lon)):
            if not self.get_parameter('auto_origin').value:return
            self.origin_lat,self.origin_lon=lat,lon
            self.get_logger().warning(f'Auto origin fixed at {lat:.7f}, {lon:.7f}; restart to reset datum')
        if abs(lat-self.origin_lat)>0.02 or abs(lon-self.origin_lon)>0.02:
            self.get_logger().warning('GPS outside local projection range; ignoring',throttle_duration_sec=5.)
            return
        latitude=math.radians(self.origin_lat)
        meters_lon=111412.84*math.cos(latitude)-93.5*math.cos(3*latitude)
        meters_lat=111132.92-559.82*math.cos(2*latitude)+1.175*math.cos(4*latitude)
        x=(lon-self.origin_lon)*meters_lon
        y=(lat-self.origin_lat)*meters_lat
        o=Odometry()
        o.header=msg.header
        o.header.frame_id='map'
        o.child_frame_id='phone_gps_link'
        o.pose.pose.position.x=x
        o.pose.pose.position.y=y
        o.pose.pose.orientation.w=1.0
        o.pose.covariance[0]=max(1.,msg.position_covariance[0])
        o.pose.covariance[7]=max(1.,msg.position_covariance[4])
        o.pose.covariance[14]=1e6
        o.pose.covariance[21]=1e6
        o.pose.covariance[28]=1e6
        o.pose.covariance[35]=1e6
        o.twist.covariance=[1e6 if i in (0,7,14,21,28,35) else 0.0 for i in range(36)]
        self.publisher.publish(o)

def main():
    rclpy.init();n=GpsLocalOdom()
    try:rclpy.spin(n)
    except KeyboardInterrupt:pass
    finally:n.destroy_node();rclpy.shutdown()
