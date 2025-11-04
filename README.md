# target-painter
The code in this repo captures frames from a webcam, detects a target (bright spot or colored blob), maps pixel coordinates to servo angles using a calibration, and sends X/Y commands over serial to an Arduino that moves two servos to point the laser.

How it works (3 steps)

Capture: read frames from the configured webcam.
Detect: find the target (bright spot or red/green/blue blob) and compute its pixel coordinates.
Act: convert pixels → servo angles using calibration, then send "X:<angle> Y:<angle>" over serial to the Arduino.