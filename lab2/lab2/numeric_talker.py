import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_msgs.msg import Int8


class Talker(Node):
    def __init__(self):
        super().__init__('numeric_talker')
        self.numeric_publisher = self.create_publisher(Int8, 'numeric_chatter', 10)

        timer_in_seconds = 0.5
        self.timer = self.create_timer(timer_in_seconds, self.talker_callback)
        self.counter = 0

    def talker_callback(self):
        num_msg = Int8()
        num_msg.data = self.counter
        self.numeric_publisher.publish(num_msg)
        self.get_logger().info(f'Publishin Int8: {num_msg.data}')
        self.counter += 1
        
        if self.counter > 127:
            self.counter = 0

def main(args=None):
    rclpy.init(args=args)

    talker = Talker()
    rclpy.spin(talker)


if __name__ == '__main__':
    main()


