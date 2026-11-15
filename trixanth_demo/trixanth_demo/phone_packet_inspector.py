"""Print the first 40 raw UDP phone datagrams, for adapting real Android sensor output."""
import socket
import rclpy
from rclpy.node import Node

class PhonePacketInspector(Node):
    def __init__(self):
        super().__init__('phone_packet_inspector')
        self.declare_parameter('port', 5006)
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.sock.bind(('0.0.0.0',int(self.get_parameter('port').value)))
        self.sock.setblocking(False)
        self.count=0
        self.create_timer(0.05,self.poll)
        self.get_logger().info('Raw phone packet inspector running on UDP 5006')
    def poll(self):
        for _ in range(15):
            try:data,addr=self.sock.recvfrom(8192)
            except BlockingIOError:break
            if self.count < 40:
                self.get_logger().info(f'{addr[0]}: {data[:1500].decode(errors="replace")}')
            self.count+=1
            if self.count==40:self.get_logger().info('Captured 40; further packets suppressed')
def main():
    rclpy.init();node=PhonePacketInspector()
    try:rclpy.spin(node)
    except KeyboardInterrupt:pass
    finally:node.sock.close();node.destroy_node();rclpy.shutdown()
