#!/usr/bin/env python3
"""
Cursor Target Simulator
Move your mouse cursor to simulate targets and test laser alignment
Perfect for calibration and testing!
"""

import cv2
import serial
import time
import numpy as np
import serial.tools.list_ports

# ========== CONFIGURATION ==========
CAMERA_INDEX = 0

# CALIBRATION VALUES - SAFE LIMITS to prevent servo burnout
X_SERVO_MIN = 105
X_SERVO_MAX = 60
Y_SERVO_MIN = 0   # Increased from 35 for safety
Y_SERVO_MAX = 60  # Decreased from 135 for safety

# SAFETY SETTINGS
MIN_MOVE_DELAY = 0.05  # Minimum delay between servo commands (50ms)
SERVO_SAFE_MIN = 10    # Absolute minimum servo angle
SERVO_SAFE_MAX = 170   # Absolute maximum servo angle
# ===================================

def find_arduino():
    """Find Arduino port automatically"""
    ports = serial.tools.list_ports.comports()
    
    print("Available serial ports:")
    for port in ports:
        print(f"  {port.device} - {port.description}")
        if 'Arduino' in port.description or 'USB' in port.description or 'Serial' in port.description:
            print(f"  → Likely Arduino: {port.device}")
            return port.device
    
    return None

class CursorTargetSimulator:
    def __init__(self, camera_index, arduino_port=None):
        # Setup camera
        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_AVFOUNDATION)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Setup Arduino (optional)
        self.ser = None
        if arduino_port:
            try:
                self.ser = serial.Serial(arduino_port, 9600, timeout=1)
                time.sleep(2)
                print("Connected to Arduino!")
                self.laser_enabled = True
            except:
                print("Arduino not connected - running in simulation mode")
                self.laser_enabled = False
        else:
            print("Running in simulation mode (no laser)")
            self.laser_enabled = False
        
        # Mouse position
        self.mouse_x = self.width // 2
        self.mouse_y = self.height // 2
        
        # Target simulation
        self.show_crosshair = True
        self.show_servo_info = True
        
        # Safety features
        self.last_command_time = 0
        self.last_servo_x = 90  # Start at center
        self.last_servo_y = 90  # Start at center
    
    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse movement"""
        self.mouse_x = x
        self.mouse_y = y
        
        # Debug: uncomment to see mouse movement
        # print(f"Mouse moved to: {x}, {y}")
        
        # Point laser if connected
        if self.laser_enabled and self.ser:
            self.point_laser(x, y)
    
    def pixel_to_servo(self, x, y):
        """Convert pixel position to servo angles using calibration"""
        servo_x = int(np.interp(x, [0, self.width], [X_SERVO_MIN, X_SERVO_MAX]))
        servo_y = int(np.interp(y, [0, self.height], [Y_SERVO_MAX, Y_SERVO_MIN]))
        return servo_x, servo_y
    
    def point_laser(self, x, y):
        """Point laser at pixel coordinates with safety checks"""
        # Rate limiting - don't send commands too fast
        current_time = time.time()
        if current_time - self.last_command_time < MIN_MOVE_DELAY:
            return
        
        servo_x, servo_y = self.pixel_to_servo(x, y)
        
        # SAFETY: Clamp servo values to safe range
        servo_x = max(SERVO_SAFE_MIN, min(SERVO_SAFE_MAX, servo_x))
        servo_y = max(SERVO_SAFE_MIN, min(SERVO_SAFE_MAX, servo_y))
        
        # SAFETY: Don't make huge jumps - limit movement per step
        max_step = 20  # Maximum degrees per command
        if abs(servo_x - self.last_servo_x) > max_step:
            servo_x = self.last_servo_x + (max_step if servo_x > self.last_servo_x else -max_step)
        if abs(servo_y - self.last_servo_y) > max_step:
            servo_y = self.last_servo_y + (max_step if servo_y > self.last_servo_y else -max_step)
        
        command = f"X:{servo_x} Y:{servo_y}\n"
        self.ser.write(command.encode())
        
        # Update tracking
        self.last_command_time = current_time
        self.last_servo_x = servo_x
        self.last_servo_y = servo_y
        
        # Debug output (uncomment to see commands being sent)
        # print(f"Sent: {command.strip()} (pixel: {x},{y})")
    
    def draw_crosshair(self, frame, x, y, color=(0, 255, 0), size=30, thickness=2):
        """Draw crosshair at position"""
        cv2.drawMarker(frame, (x, y), color, cv2.MARKER_CROSS, size, thickness)
        cv2.circle(frame, (x, y), 15, color, thickness)
    
    def draw_grid(self, frame, spacing=100):
        """Draw grid for easier alignment reference"""
        color = (50, 50, 50)  # Dark gray
        
        # Vertical lines
        for x in range(0, self.width, spacing):
            cv2.line(frame, (x, 0), (x, self.height), color, 1)
        
        # Horizontal lines
        for y in range(0, self.height, spacing):
            cv2.line(frame, (0, y), (self.width, y), color, 1)
    
    def run(self):
        """Main simulation loop"""
        print("\n" + "="*50)
        print("CURSOR TARGET SIMULATOR")
        print("="*50)
        print("Move your mouse cursor over the video window")
        print("The laser will follow your cursor position")
        print("")
        print("Controls:")
        print("  Mouse - Move target")
        print("  'c' - Toggle crosshair")
        print("  'i' - Toggle servo info display")
        print("  'g' - Toggle grid")
        print("  'q' - Quit")
        print("")
        if self.laser_enabled:
            print("Laser connected - laser will follow cursor")
        else:
            print(" No laser - simulation mode only")
        print("="*50)
        
        cv2.namedWindow('Cursor Target Simulator')
        cv2.setMouseCallback('Cursor Target Simulator', self.mouse_callback)
        
        show_grid = False
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # Draw grid if enabled
            if show_grid:
                self.draw_grid(frame)
            
            # Draw crosshair at mouse position
            if self.show_crosshair:
                self.draw_crosshair(frame, self.mouse_x, self.mouse_y, 
                                   color=(0, 255, 0) if self.laser_enabled else (0, 255, 255))
            
            # Show info overlay
            if self.show_servo_info:
                servo_x, servo_y = self.pixel_to_servo(self.mouse_x, self.mouse_y)
                
                # Info background
                cv2.rectangle(frame, (10, 10), (400, 120), (0, 0, 0), -1)
                cv2.rectangle(frame, (10, 10), (400, 120), (255, 255, 255), 1)
                
                # Text info
                info_lines = [
                    f"Cursor: ({self.mouse_x}, {self.mouse_y})",
                    f"Servo: X={servo_x}, Y={servo_y}",
                    f"Laser: {'ACTIVE' if self.laser_enabled else 'SIMULATED'}",
                    f"Resolution: {self.width}x{self.height}"
                ]
                
                for i, line in enumerate(info_lines):
                    cv2.putText(frame, line, (15, 30 + i*20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Instructions
            cv2.putText(frame, "Move mouse to test laser alignment", 
                       (10, self.height - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.putText(frame, "Press 'c' for crosshair, 'i' for info, 'g' for grid, 'q' to quit", 
                       (10, self.height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
            cv2.imshow('Cursor Target Simulator', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                self.show_crosshair = not self.show_crosshair
                print(f"Crosshair: {'ON' if self.show_crosshair else 'OFF'}")
            elif key == ord('i'):
                self.show_servo_info = not self.show_servo_info
                print(f"Servo info: {'ON' if self.show_servo_info else 'OFF'}")
            elif key == ord('g'):
                show_grid = not show_grid
                print(f"Grid: {'ON' if show_grid else 'OFF'}")
        
        self.cleanup()
    
    def cleanup(self):
        self.cap.release()
        if self.ser:
            self.ser.close()
        cv2.destroyAllWindows()

def main():
    print("🎯 Cursor Target Simulator")
    print("Perfect for testing laser alignment!")
    
    # Ask if user wants to connect laser
    use_laser = input("\nConnect laser? (y/n): ").lower().startswith('y')
    
    port = None
    if use_laser:
        port = find_arduino()
        if not port:
            port = input("Enter Arduino port (or press Enter to skip): ").strip()
            if not port:
                print("Running without laser...")
    
    simulator = CursorTargetSimulator(CAMERA_INDEX, port)
    simulator.run()

if __name__ == "__main__":
    main()