#!/usr/bin/env python3
"""
Laser Calibration Tool
Click 4 corners of camera view to calibrate laser positioning
"""

import cv2
import serial
import time
import numpy as np
import serial.tools.list_ports

def find_arduino():
    """Find Arduino port automatically"""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if 'Arduino' in port.description or 'USB' in port.description or 'Serial' in port.description:
            return port.device
    return None

class LaserCalibrator:
    def __init__(self, camera_index, arduino_port):
        # Setup camera
        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_AVFOUNDATION)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Setup Arduino
        self.ser = serial.Serial(arduino_port, 9600, timeout=1)
        time.sleep(2)
        print("Connected to Arduino!")
        
        # Calibration values
        self.x_servo_min = 150
        self.x_servo_max = 85
        self.y_servo_min = 80
        self.y_servo_max = 115
        
    def point_laser(self, servo_x, servo_y):
        """Send servo angles to Arduino"""
        command = f"X:{servo_x} Y:{servo_y}\n"
        self.ser.write(command.encode())
        time.sleep(0.3)
    
    def calibrate_corner(self, corner_name, servo_x, servo_y):
        """Calibrate one corner"""
        print(f"\n=== Calibrating {corner_name} ===")
        print(f"Moving laser to servo position X={servo_x}, Y={servo_y}")
        self.point_laser(servo_x, servo_y)
        
        print("Adjust laser position if needed:")
        print("  W/S - Y servo up/down")
        print("  A/D - X servo left/right")
        print("  SPACE - Confirm position")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            cv2.putText(frame, f"Calibrating: {corner_name}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Servo: X={servo_x} Y={servo_y}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "WASD to adjust, SPACE to confirm", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow('Calibration', frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            changed = False
            if key == ord('w'):
                servo_y = min(180, servo_y + 5)
                changed = True
            elif key == ord('s'):
                servo_y = max(0, servo_y - 5)
                changed = True
            elif key == ord('a'):
                servo_x = max(0, servo_x - 5)
                changed = True
            elif key == ord('d'):
                servo_x = min(180, servo_x + 5)
                changed = True
            elif key == ord(' '):
                print(f"Confirmed: X={servo_x}, Y={servo_y}")
                return servo_x, servo_y
            
            if changed:
                self.point_laser(servo_x, servo_y)
        
        return servo_x, servo_y
    
    def run_calibration(self):
        """Run calibration"""
        print("\n" + "="*50)
        print("LASER CALIBRATION")
        print("="*50)
        print("\nWe'll calibrate 4 corners.")
        print("Point the laser at each corner, then press SPACE.")
        
        input("\nPress Enter to start...")
        
        corners = [
            ("TOP-LEFT", 45, 135),
            ("TOP-RIGHT", 135, 135),
            ("BOTTOM-RIGHT", 135, 45),
            ("BOTTOM-LEFT", 45, 45),
        ]
        
        calibrated = []
        for corner_name, start_x, start_y in corners:
            servo_x, servo_y = self.calibrate_corner(corner_name, start_x, start_y)
            calibrated.append((servo_x, servo_y))
        
        self.x_servo_min = min(calibrated[0][0], calibrated[3][0])
        self.x_servo_max = max(calibrated[1][0], calibrated[2][0])
        self.y_servo_min = min(calibrated[2][1], calibrated[3][1])
        self.y_servo_max = max(calibrated[0][1], calibrated[1][1])
        
        print("\n" + "="*50)
        print("CALIBRATION COMPLETE!")
        print("="*50)
        print(f"X_SERVO_MIN = {self.x_servo_min}")
        print(f"X_SERVO_MAX = {self.x_servo_max}")
        print(f"Y_SERVO_MIN = {self.y_servo_min}")
        print(f"Y_SERVO_MAX = {self.y_servo_max}")
        
        with open('calibration.txt', 'w') as f:
            f.write(f"X_SERVO_MIN = {self.x_servo_min}\n")
            f.write(f"X_SERVO_MAX = {self.x_servo_max}\n")
            f.write(f"Y_SERVO_MIN = {self.y_servo_min}\n")
            f.write(f"Y_SERVO_MAX = {self.y_servo_max}\n")
        
        print("\nSaved to calibration.txt")
        self.cleanup()
    
    def cleanup(self):
        self.cap.release()
        self.ser.close()
        cv2.destroyAllWindows()

def main():
    port = find_arduino()
    if not port:
        port = input("Enter Arduino port: ").strip()
        if not port:
            return
    
    calibrator = LaserCalibrator(0, port)
    calibrator.run_calibration()

if __name__ == "__main__":
    main()