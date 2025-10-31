#!/usr/bin/env python3
"""
Simple Webcam Display
Displays live feed from Logitech webcam using OpenCV
Press 'q' to quit
"""

import cv2

def main():
    # CHANGE THIS NUMBER to select your camera:
    # 0 = usually built-in laptop webcam (FaceTime HD Camera - 5 FPS)
    # 1 = usually USB webcam (Logitech C922 Pro Stream Webcam - 15 FPS)
    CAMERA_INDEX = 0  # <-- TESTING: Try camera 0 instead
    
    print(f"Attempting to open camera {CAMERA_INDEX}...")
    print("Expected cameras:")
    print("  Camera 0: FaceTime HD Camera (5 FPS)")
    print("  Camera 1: Logitech C922 Pro Stream (15 FPS)")
    
    # Mac-specific: Try AVFoundation backend first (better Mac support for external cameras)
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_AVFOUNDATION)
    
    # If AVFoundation fails, try default backend
    if not cap.isOpened():
        print("AVFoundation backend failed, trying default backend...")
        cap = cv2.VideoCapture(CAMERA_INDEX)
    
    # Check if camera opened successfully
    if not cap.isOpened():
        print("err: could not open webcam")
        print("try changing the camera index (0, 1, 2, etc.)")
        return
    
    # Get current camera properties to verify which camera we got
    current_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    current_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    current_fps = cap.get(cv2.CAP_PROP_FPS)
    backend = cap.get(cv2.CAP_PROP_BACKEND)
    
    print("Webcam opened successfully!")
    print(f"Camera properties: {current_width}x{current_height} @ {current_fps} FPS (Backend: {backend})")
    
    # Determine which camera this likely is based on FPS
    if current_fps <= 6:
        print("🚨 This appears to be the MacBook's FaceTime camera (low FPS)")
        print("   Try changing CAMERA_INDEX to 0 if you want the built-in camera")
        print("   or to a different number for the Logitech camera")
    else:
        print("✅ This appears to be the Logitech camera (higher FPS)")
    
    # Set resolution (optional - adjust as needed)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("Press 'q' to quit")
    
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        
        # Check if frame was read successfully
        if not ret:
            print("Error: Can't receive frame. Exiting...")
            break
        
        # Display the frame
        cv2.imshow('Webcam Feed', frame)
        
        # Break loop on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release the camera and close windows
    cap.release()
    cv2.destroyAllWindows()
    print("Webcam closed")

if __name__ == "__main__":
    main()