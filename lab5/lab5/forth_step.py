# Exercise 4 - Following a colour (green) and stopping upon sight of another (blue).
import threading
import sys, time
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
from rclpy.exceptions import ROSInterruptException
import signal

class Robot(Node):
    def __init__(self):
        super().__init__('robot')
        
        # 1. Initialise publisher for movement
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        # 2. State variables for continuous movement
        self.action = "STOP" 
        self.turn_speed = 0.0 
        self.sensitivity = 20

        # 3. Initialise CvBridge and image subscriber
        self.bridge = CvBridge()
        self.subscription = self.create_subscription(Image, '/camera/image_raw', self.callback, 10)
        self.subscription  

    def callback(self, data):
        try:
            image = self.bridge.imgmsg_to_cv2(data, 'bgr8')
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridge Error: {e}")
            return
            
        # Convert to HSV
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Bounds for Green
        hsv_green_lower = np.array([60 - self.sensitivity, 100, 100])
        hsv_green_upper = np.array([60 + self.sensitivity, 255, 255])
        
        # Bounds for Blue
        hsv_blue_lower = np.array([120 - self.sensitivity, 100, 100])
        hsv_blue_upper = np.array([120 + self.sensitivity, 255, 255])

        # Create Masks
        green_mask = cv2.inRange(hsv_image, hsv_green_lower, hsv_green_upper)
        blue_mask = cv2.inRange(hsv_image, hsv_blue_lower, hsv_blue_upper)

        # Find Contours
        blue_contours, _ = cv2.findContours(blue_mask, mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_SIMPLE)
        green_contours, _ = cv2.findContours(green_mask, mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_SIMPLE)

        # Default state resets every frame
        self.action = "STOP"
        self.turn_speed = 0.0

        # --- PRIORITY 1: Safety Stop (Blue) ---
        if len(blue_contours) > 0:
            c_blue = max(blue_contours, key=cv2.contourArea)
            if cv2.contourArea(c_blue) > 500:
                self.action = "STOP"
                (x, y), radius = cv2.minEnclosingCircle(c_blue)
                cv2.circle(image, (int(x), int(y)), int(radius), (255, 0, 0), 2)
                
        # --- PRIORITY 2: Track Target (Green) ---
        elif len(green_contours) > 0:
            c_green = max(green_contours, key=cv2.contourArea)
            area = cv2.contourArea(c_green)
            
            if area > 500: 
                (x, y), radius = cv2.minEnclosingCircle(c_green)
                cv2.circle(image, (int(x), int(y)), int(radius), (0, 255, 0), 2)

                # 1. Calculate Angular Z (Steering)
                image_width = image.shape[1]
                screen_center = image_width / 2.0
                error_x = screen_center - x
                
                Kp = 0.005 # Proportional Gain
                self.turn_speed = error_x * Kp 

                # 2. Calculate Linear X (Distance based on Area)
                if area > 60000:
                    self.action = "BACKWARD" 
                elif area < 30000:
                    self.action = "FORWARD"  
                else:
                    self.action = "SPIN_ONLY" 

        # Display feeds
        cv2.namedWindow('camera_Feed', cv2.WINDOW_NORMAL)
        cv2.imshow('camera_Feed', image)
        cv2.resizeWindow('camera_Feed', 320, 240)
        cv2.waitKey(3)

    # --- Continuous Movement Functions ---
    def walk_forward(self):
        msg = Twist()
        msg.linear.x = 0.15  
        msg.angular.z = self.turn_speed 
        self.publisher.publish(msg)

    def walk_backward(self):
        msg = Twist()
        msg.linear.x = -0.15 
        msg.angular.z = -self.turn_speed # Invert steering when backing up
        self.publisher.publish(msg)
        
    def spin_in_place(self):
        msg = Twist()
        msg.linear.x = 0.0   
        msg.angular.z = self.turn_speed 
        self.publisher.publish(msg)

    def stop(self):
        msg = Twist()
        msg.linear.x = 0.0
        msg.angular.z = 0.0
        self.publisher.publish(msg)


def main():
    def signal_handler(sig, frame):
        robot.stop() 
        rclpy.shutdown()

    rclpy.init(args=None)
    robot = Robot()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Spin node in background to keep camera frames coming in
    thread = threading.Thread(target=rclpy.spin, args=(robot,), daemon=True)
    thread.start()

    # Main thread continuously publishes the current state at ~10Hz
    try:
        while rclpy.ok():
            if robot.action == "FORWARD":
                robot.walk_forward()
            elif robot.action == "BACKWARD":
                robot.walk_backward()
            elif robot.action == "SPIN_ONLY":
                robot.spin_in_place()
            else:
                robot.stop()
                
            time.sleep(0.1) 

    except ROSInterruptException:
        pass
    finally:
        robot.stop()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()