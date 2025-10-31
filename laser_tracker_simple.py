#!/usr/bin/env python3
"""
Simple Object Tracker with Laser Pointer
Detects brightest/colored object and points laser at it

SIMPLE VERSION - Minimal code
"""

import cv2
import serial
import time
import numpy as np
import serial.tools.list_ports

# ========== CONFIGURATION ==========
CAMERA_INDEX = 0
DETECTION_MODE = "bright"  # Options: "bright", "red", "green", "blue"

# CALIBRATION VALUES - Adjusted to fix laser pointing too low
X_SERVO_MIN = 150  # Swapped back to reverse direction
X_SERVO_MAX = 80   # Swapped back to reverse direction
Y_SERVO_MIN = 50   # Increased from 35 to move laser up
Y_SERVO_MAX = 125  # Increased from 110 to move laser up
# ===================================

def find_arduino():
    """Find Arduino port automatically"""
    ports = serial.tools.list_ports.comports()
    
    print("Available serial ports:")
    for port in ports:
        print(f"  {port.device} - {port.description}")
        # Look for Arduino-like devices
        if 'Arduino' in port.description or 'USB' in port.description or 'Serial' in port.description:
            print(f"  → Likely Arduino: {port.device}")
            return port.device
    
    return None

class LaserTracker:
    def __init__(self, camera_index, arduino_port):
        # Setup camera
        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_AVFOUNDATION)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Setup Arduino
        self.ser = serial.Serial(arduino_port, 9600, timeout=1)
        time.sleep(2)
        print("Connected to Arduino!")
        
        # Current target
        self.target_x = self.width // 2
        self.target_y = self.height // 2
    
    def detect_object(self, frame, mode="bright"):
        """Simple object detection - returns (x, y) or None"""
        
        if mode == "bright":
            # Find brightest spot
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (15, 15), 0)
            (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(blur)
            return maxLoc
        
        elif mode == "red":
            # Detect red objects
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            # Red color range in HSV
            lower_red1 = np.array([0, 100, 100])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([160, 100, 100])
            upper_red2 = np.array([180, 255, 255])
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            mask = mask1 | mask2
            
        elif mode == "green":
            # Detect green objects
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            lower = np.array([40, 50, 50])
            upper = np.array([80, 255, 255])
            mask = cv2.inRange(hsv, lower, upper)
            
        elif mode == "blue":
            # Detect blue objects
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            lower = np.array([100, 100, 100])
            upper = np.array([130, 255, 255])
            mask = cv2.inRange(hsv, lower, upper)
        
        # For color detection, find center of detected blob
        if mode in ["red", "green", "blue"]:
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                # Get largest contour
                largest = max(contours, key=cv2.contourArea)
                if cv2.contourArea(largest) > 500:  # Minimum size threshold
                    M = cv2.moments(largest)
                    if M["m00"] > 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        return (cx, cy)
        
        return None
    
    def pixel_to_servo(self, x, y):
        """Convert pixel position to servo angles using calibration"""
        servo_x = int(np.interp(x, [0, self.width], [X_SERVO_MIN, X_SERVO_MAX]))
        servo_y = int(np.interp(y, [0, self.height], [Y_SERVO_MAX, Y_SERVO_MIN]))
        return servo_x, servo_y
    
    def point_laser(self, x, y):
        """Point laser at pixel coordinates"""
        servo_x, servo_y = self.pixel_to_servo(x, y)
        command = f"X:{servo_x} Y:{servo_y}\n"
        self.ser.write(command.encode())
    
    def run(self, mode="bright"):
        """Main tracking loop"""
        print(f"\n=== Laser Tracker ({mode} mode) ===")
        print("Press 'q' to quit")
        print("Press 'b' for bright mode")
        print("Press 'r' for red detection")
        print("Press 'g' for green detection")
        print("Press 'u' for blue detection\n")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # Detect object
            detection = self.detect_object(frame, mode)
            
            if detection:
                self.target_x, self.target_y = detection
                self.point_laser(self.target_x, self.target_y)
                
                # Draw crosshair on detected object
                cv2.drawMarker(frame, detection, (0, 255, 0), 
                              cv2.MARKER_CROSS, 30, 3)
                cv2.circle(frame, detection, 10, (0, 255, 0), 2)
            
            # Show detection mode
            cv2.putText(frame, f"Mode: {mode.upper()}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow('Laser Tracker', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('b'):
                mode = "bright"
            elif key == ord('r'):
                mode = "red"
            elif key == ord('g'):
                mode = "green"
            elif key == ord('u'):
                mode = "blue"
        
        self.cleanup()
    
    def cleanup(self):
        self.cap.release()
        self.ser.close()
        cv2.destroyAllWindows()

def main():
    # Find Arduino port automatically (same as test_arduino_serial.py)
    port = find_arduino()
    
    if not port:
        print("\nCouldn't auto-detect Arduino.")
        print("Common ports:")
        print("  Mac: /dev/cu.usbmodem* or /dev/cu.usbserial*")
        print("  Linux: /dev/ttyUSB* or /dev/ttyACM*")
        print("  Windows: COM3, COM4, etc.")
        port = input("\nEnter Arduino port manually (or press Enter to exit): ")
        if not port:
            return
    
    print(f"Using Arduino port: {port}\n")
    
    tracker = LaserTracker(CAMERA_INDEX, port)
    tracker.run(mode=DETECTION_MODE)

if __name__ == "__main__":
    main()