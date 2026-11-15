"""Galaxy M36 / SensaGram Android UDP JSON to ROS 2 IMU + GPS.

Android IMU axes: x phone-right, y phone-top, z out of screen.
Measurements are in the *phone* frame, NOT rover base_link. Calibrate
mounting transform before EKF/Nav2. Timestamps use Pi receipt time.
"""
import json
import math
import socket
import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, NavSatFix, NavSatStatus

class PhoneUdpBridge(Node):
    def __init__(self):
        super().__init__('phone_udp_bridge')
        self.declare_parameter('port', 5005)
        self.declare_parameter('imu_frame', 'phone_imu_link')
        self.declare_parameter('gps_frame', 'phone_gps_link')
        self.declare_parameter('max_imu_age_s', 0.5)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', int(self.get_parameter('port').value)))
        self.sock.setblocking(False)
        self.imu_pub = self.create_publisher(Imu, '/imu/data', 10)
        self.gps_pub = self.create_publisher(NavSatFix, '/gps/fix', 10)
        self.accel = None
        self.gyro = None
        self.rotation = None
        self.last_android_gyro_timestamp = None
        self.timer = self.create_timer(0.01, self.poll)
        self.get_logger().info('Galaxy M36 phone bridge ready: UDP 5005 (Android + normalized JSON)')

    @staticmethod
    def triple(data):
        if not isinstance(data, (list, tuple)) or len(data) < 3:
            raise ValueError('Expected three sensor components')
        v = tuple(float(x) for x in data[:3])
        if not all(math.isfinite(x) for x in v):
            raise ValueError('Non-finite sensor component')
        return v

    def poll(self):
        for _ in range(100):
            try:
                raw, _ = self.sock.recvfrom(8192)
            except BlockingIOError:
                break
            try:
                data = json.loads(raw.decode('utf-8'))
                kind = data.get('type')
                if kind == 'imu':
                    self.handle_normalized_imu(data)
                elif kind == 'gps':
                    self.handle_gps(data)
                elif kind == 'android.sensor.accelerometer':
                    self.accel = (self.triple(data['values']), time.monotonic())
                elif kind == 'android.sensor.gyroscope':
                    self.gyro = (self.triple(data['values']), time.monotonic())
                    # Publish only once per new gyroscope measurement.
                    self.publish_android_imu()
                elif kind == 'android.sensor.rotation_vector':
                    v = data['values']
                    if isinstance(v, list) and len(v) >= 4:
                        q = [float(x) for x in v[:4]]
                        n = math.sqrt(sum(x*x for x in q))
                        if n > 0.5 and all(math.isfinite(x) for x in q):
                            self.rotation = ([x/n for x in q], time.monotonic())
                # Android location is not automatically parsed: inspect actual packet.
            except (UnicodeDecodeError, ValueError, KeyError, TypeError, OverflowError) as exc:
                self.get_logger().warning(f'Dropped invalid phone packet: {exc}', throttle_duration_sec=5.)

    def new_imu(self):
        m = Imu()
        m.header.stamp = self.get_clock().now().to_msg()
        m.header.frame_id = str(self.get_parameter('imu_frame').value)
        # ROS convention: negative first covariance element means unavailable.
        m.orientation_covariance[0] = -1.0
        m.angular_velocity_covariance = [0.05,0,0, 0,0.05,0, 0,0,0.05]
        m.linear_acceleration_covariance = [0.5,0,0, 0,0.5,0, 0,0,0.5]
        return m

    def publish_android_imu(self):
        if self.gyro is None or self.accel is None:
            return
        now = time.monotonic()
        max_age = float(self.get_parameter('max_imu_age_s').value)
        if now - self.accel[1] > max_age or now - self.gyro[1] > max_age:
            return
        m = self.new_imu()
        m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z = self.gyro[0]
        m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z = self.accel[0]
        if self.rotation is not None and now - self.rotation[1] < max_age:
            m.orientation.x, m.orientation.y, m.orientation.z, m.orientation.w = self.rotation[0]
            # Illustrative uncertainties only; calibrate before localization.
            m.orientation_covariance = [0.2,0,0, 0,0.2,0, 0,0,0.4]
        self.imu_pub.publish(m)

    def handle_normalized_imu(self, d):
        w = d['angular_velocity']
        a = d['linear_acceleration']
        vals = [float(w[k]) for k in ('x','y','z')] + [float(a[k]) for k in ('x','y','z')]
        if not all(math.isfinite(x) for x in vals):
            return
        m = self.new_imu()
        m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z = vals[:3]
        m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z = vals[3:]
        if 'orientation' in d:
            q = d['orientation']
            qv = [float(q[k]) for k in ('x','y','z','w')]
            norm = math.sqrt(sum(x*x for x in qv))
            if norm > 0.5 and all(math.isfinite(x) for x in qv):
                m.orientation.x, m.orientation.y, m.orientation.z, m.orientation.w = [x/norm for x in qv]
                m.orientation_covariance = [0.2,0,0, 0,0.2,0, 0,0,0.4]
        self.imu_pub.publish(m)

    def handle_gps(self, d):
        lat = float(d['lat'])
        lon = float(d['lon'])
        alt = float(d.get('alt', 0))
        acc = float(d.get('horizontal_accuracy_m', 15))
        if not (-90 <= lat <= 90 and -180 <= lon <= 180
                and math.isfinite(alt) and math.isfinite(acc) and 0 < acc < 10000):
            return
        m = NavSatFix()
        m.header.stamp = self.get_clock().now().to_msg()
        m.header.frame_id = str(self.get_parameter('gps_frame').value)
        m.status.status = NavSatStatus.STATUS_FIX if bool(d.get('valid', True)) else NavSatStatus.STATUS_NO_FIX
        m.status.service = NavSatStatus.SERVICE_GPS
        m.latitude = lat
        m.longitude = lon
        m.altitude = alt
        m.position_covariance = [acc*acc,0,0, 0,acc*acc,0, 0,0,max(4*acc*acc,25)]
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
