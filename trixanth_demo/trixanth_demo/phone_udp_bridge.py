"""UDP JSON -> ROS 2 sensor_msgs. Incoming measurements must be in ROS ENU/FLU conventions."""
import json
import math
import socket
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, NavSatFix, NavSatStatus

class PhoneUdpBridge(Node):
    def __init__(self):
        super().__init__('phone_udp_bridge')
        self.declare_parameter('port', 5005)
        self.declare_parameter('imu_frame', 'phone_imu_link')
        self.declare_parameter('gps_frame', 'phone_gps_link')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', int(self.get_parameter('port').value)))
        self.sock.setblocking(False)
        self.imu_pub = self.create_publisher(Imu, '/imu/data', 10)
        self.gps_pub = self.create_publisher(NavSatFix, '/gps/fix', 10)
        self.timer = self.create_timer(0.02, self.poll)
        self.get_logger().info('Phone UDP bridge ready on port 5005; no sensors connected yet')

    def poll(self):
        for _ in range(30):
            try:
                raw, _ = self.sock.recvfrom(4096)
            except BlockingIOError:
                break
            try:
                data = json.loads(raw.decode('utf-8'))
                if data.get('type') == 'imu':
                    self.handle_imu(data)
                elif data.get('type') == 'gps':
                    self.handle_gps(data)
            except (UnicodeDecodeError, ValueError, KeyError, TypeError) as exc:
                self.get_logger().warning(f'Dropped invalid phone packet: {exc}', throttle_duration_sec=5.0)

    def handle_imu(self, d):
        w = d['angular_velocity']
        a = d['linear_acceleration']
        values = [float(w[k]) for k in ('x','y','z')] + [float(a[k]) for k in ('x','y','z')]
        if not all(math.isfinite(x) for x in values):
            return
        m = Imu()
        m.header.stamp = self.get_clock().now().to_msg()
        m.header.frame_id = str(self.get_parameter('imu_frame').value)
        m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z = values[:3]
        m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z = values[3:]
        m.angular_velocity_covariance = [0.05,0,0,0,0.05,0,0,0,0.05]
        m.linear_acceleration_covariance = [0.5,0,0,0,0.5,0,0,0,0.5]
        m.orientation_covariance[0] = -1.0
        if 'orientation' in d:
            q = d['orientation']
            qv = [float(q[k]) for k in ('x','y','z','w')]
            if all(math.isfinite(x) for x in qv):
                norm = math.sqrt(sum(x*x for x in qv))
                if norm > 0.5:
                    m.orientation.x, m.orientation.y, m.orientation.z, m.orientation.w = [x/norm for x in qv]
                    m.orientation_covariance = [0.2,0,0,0,0.2,0,0,0,0.4]
        self.imu_pub.publish(m)

    def handle_gps(self, d):
        lat = float(d['lat'])
        lon = float(d['lon'])
        alt = float(d.get('alt',0))
        acc = float(d.get('horizontal_accuracy_m',15))
        if not (-90 <= lat <= 90 and -180 <= lon <= 180 and math.isfinite(alt) and 0 < acc < 10000):
            return
        m = NavSatFix()
        m.header.stamp = self.get_clock().now().to_msg()
        m.header.frame_id = str(self.get_parameter('gps_frame').value)
        m.status.status = NavSatStatus.STATUS_FIX if bool(d.get('valid', True)) else NavSatStatus.STATUS_NO_FIX
        m.status.service = NavSatStatus.SERVICE_GPS
        m.latitude = lat
        m.longitude = lon
        m.altitude = alt
        m.position_covariance = [acc*acc,0,0,0,acc*acc,0,0,0,max(4*acc*acc,25)]
        m.position_covariance_type = NavSatFix.COVARIANCE_TYPE_DIAGONAL_KNOWN
        self.gps_pub.publish(m)

def main():
    rclpy.init()
    node = PhoneUdpBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.sock.close()
        node.destroy_node()
        rclpy.shutdown()
