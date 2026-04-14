# Exercise 1 - Display an image of the camera feed to the screen

#from __future__ import division
import threading
import sys, time
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, Vector3
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
from rclpy.exceptions import ROSInterruptException
import signal


class colourIdentifier(Node):
    def __init__(self):
        super().__init__('cI')
        
        # Remember to initialise a CvBridge() and set up a subscriber to the image topic you wish to use
        # We covered which topic to subscribe to should you wish to receive image data
        self.bridge = CvBridge()
        
        self.subscription = self.create_subscription(
            Image,
            'camera/image_raw',
            self.callback,
            10
        )
        self.subscription  # prevent unused variable warning
        
    def callback(self, data):
        cv_image = self.bridge.imgmsg_to_cv2(data,'bgr8')
        
        # Convert BGR to HSV colour space
        hsv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        
        # Define sensitivity for our colour range
        sensitivity = 20
        
        # Define the upper and lower bounds for Green in HSV
        # Green hue is roughly 60. We check from 40 to 80.
        hsv_green_lower = np.array([60 - sensitivity, 100, 100])
        hsv_green_upper = np.array([60 + sensitivity, 255, 255])
        
        #Create a binary mask (Pixels are 1 if they are green, 0 if they are not)
        green_mask = cv2.inRange(hsv_image, hsv_green_lower, hsv_green_upper)
        
        # Apply the mask to the original image to only show the green parts
        filtered_img = cv2.bitwise_and(cv_image, cv_image, mask=green_mask)
        
        # Display the filtered image
        cv2.namedWindow('Filtered_Feed', cv2.WINDOW_NORMAL) 
        cv2.imshow('Filtered_Feed', filtered_img)
        cv2.resizeWindow('Filtered_Feed', 320, 240) 
        cv2.waitKey(3)
        return
        # Convert the received image into a opencv image
        # But remember that you should always wrap a call to this conversion method in an exception handler
        # Show the resultant images you have created.
        

# Create a node of your class in the main and ensure it stays up and running
# handling exceptions and such
def main():

    def signal_handler(sig, frame):
        rclpy.shutdown()
    # Instantiate your class
    # And rclpy.init the entire node
    rclpy.init(args=None)
    cI = colourIdentifier()


    signal.signal(signal.SIGINT, signal_handler)
    thread = threading.Thread(target=rclpy.spin, args=(cI,), daemon=True)
    thread.start()

    try:
        while rclpy.ok():
            continue
    except ROSInterruptException:
        pass

    # Remember to destroy all image windows before closing node
    cv2.destroyAllWindows()
    

# Check if the node is executing in the main path
if __name__ == '__main__':
    main()
