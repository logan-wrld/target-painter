#!/usr/bin/env python3
"""
Arduino Serial Test
Tests serial communication with Arduino servo controller
"""

import serial
import time
import serial.tools.list_ports

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

def test_serial_connection(port, baudrate=9600):
    """Test connection to Arduino"""
    try:
        print(f"\nConnecting to {port} at {baudrate} baud...")
        ser = serial.Serial(port, baudrate, timeout=2)
        time.sleep(2)  # Wait for Arduino to reset
        
        # Read initial message from Arduino
        if ser.in_waiting:
            response = ser.readline().decode('utf-8').strip()
            print(f"Arduino says: {response}")
        
        return ser
    except Exception as e:
        print(f"Error connecting: {e}")
        return None

def send_servo_command(ser, x_angle, y_angle):
    """Send servo position command to Arduino"""
    command = f"X:{x_angle} Y:{y_angle}\n"
    ser.write(command.encode())
    
    # Wait for response
    time.sleep(0.1)
    if ser.in_waiting:
        response = ser.readline().decode('utf-8').strip()
        print(f"  Arduino response: {response}")

def main():
    print("=== Arduino Serial Test ===\n")
    
    # Find Arduino port
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
    
    # Connect to Arduino
    ser = test_serial_connection(port)
    if not ser:
        return
    
    print("\n✓ Connected successfully!")
    print("\nTesting servo movements...\n")
    
    try:
        # Test sequence
        test_positions = [
            (90, 90, "Center"),
            (45, 90, "Left"),
            (135, 90, "Right"),
            (90, 45, "Down"),
            (90, 135, "Up"),
            (90, 90, "Center again"),
        ]
        
        for x, y, description in test_positions:
            print(f"Moving to {description}: X={x}°, Y={y}°")
            send_servo_command(ser, x, y)
            time.sleep(1)
        
        print("\n✓ Test complete! Your servos should have moved.")
        print("If they didn't move, check:")
        print("  1. Servo wiring to Arduino pins")
        print("  2. Power supply to servos")
        print("  3. Pin numbers in Arduino code match your setup")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    finally:
        ser.close()
        print("Serial connection closed")

if __name__ == "__main__":
    main()
