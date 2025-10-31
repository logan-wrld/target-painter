/*************************************************** 
  Arduino Servo Controller for PCA9685
  Receives servo position commands via Serial from Python
  
  Protocol: "X:<angle> Y:<angle>\n"
  Example: "X:90 Y:45\n"
  
  Hardware: Adafruit PCA9685 16-Channel PWM Servo Driver
  Connect: SDA to Arduino SDA, SCL to Arduino SCL
  
  Upload this to your Arduino/Mini Metro using Arduino IDE
 ****************************************************/

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// Create PWM driver object (default address 0x40)
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// Servo channel numbers on the PCA9685 board
// CHANGE THESE to match which channels your servos are plugged into (0-15)
#define SERVO_X_CHANNEL 0  // X-axis servo (pan/horizontal)
#define SERVO_Y_CHANNEL 1  // Y-axis servo (tilt/vertical)

// Servo pulse length limits (matching your working test code)
#define SERVOMIN  150   // Minimum pulse length (0 degrees)
#define SERVOMAX  600   // Maximum pulse length (180 degrees)
#define USMIN  600      // Minimum microseconds
#define USMAX  2400     // Maximum microseconds
#define SERVO_FREQ 50   // Analog servos run at ~50 Hz

// Current servo positions (in degrees)
int posX = 90;  // Center X
int posY = 90;  // Center Y

// Serial communication
String inputString = "";
boolean stringComplete = false;

void setup() {
  Serial.begin(9600);
  
  // Initialize PCA9685
  pwm.begin();
  pwm.setOscillatorFrequency(27000000);
  pwm.setPWMFreq(SERVO_FREQ);
  
  delay(10);
  
  // Move to center position
  setServoAngle(SERVO_X_CHANNEL, posX);
  setServoAngle(SERVO_Y_CHANNEL, posY);
  
  // Reserve space for input string
  inputString.reserve(50);
  
  // Signal ready
  Serial.println("PCA9685 Servo Controller Ready");
  Serial.println("Send commands as: X:<angle> Y:<angle>");
}

void loop() {
  // Check if we received a complete command
  if (stringComplete) {
    processCommand(inputString);
    
    // Clear the string for next command
    inputString = "";
    stringComplete = false;
  }
}

// Convert angle (0-180) to microseconds and move servo
void setServoAngle(uint8_t channel, int angle) {
  // Constrain angle to valid range
  angle = constrain(angle, 0, 180);
  
  // Map angle to microseconds (like your working test code)
  int microseconds = map(angle, 0, 180, USMIN, USMAX);
  
  // Use writeMicroseconds (like your working test code)
  pwm.writeMicroseconds(channel, microseconds);
  
  // Also try direct PWM method as backup
  // int pulse = map(angle, 0, 180, SERVOMIN, SERVOMAX);
  // pwm.setPWM(channel, 0, pulse);
}

// This function is called automatically when serial data arrives
void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    inputString += inChar;
    
    // If newline character, we have a complete command
    if (inChar == '\n') {
      stringComplete = true;
    }
  }
}

void processCommand(String command) {
  command.trim();  // Remove whitespace
  
  // Parse X and Y values from command string
  int xIndex = command.indexOf("X:");
  int yIndex = command.indexOf("Y:");
  
  if (xIndex >= 0 && yIndex >= 0) {
    // Extract X value
    int xStart = xIndex + 2;
    int xEnd = command.indexOf(' ', xStart);
    String xStr = command.substring(xStart, xEnd);
    int newX = xStr.toInt();
    
    // Extract Y value
    int yStart = yIndex + 2;
    String yStr = command.substring(yStart);
    int newY = yStr.toInt();
    
    // Constrain values to valid servo range (0-180)
    newX = constrain(newX, 0, 180);
    newY = constrain(newY, 0, 180);
    
    // Update servo positions
    posX = newX;
    posY = newY;
    setServoAngle(SERVO_X_CHANNEL, posX);
    setServoAngle(SERVO_Y_CHANNEL, posY);
    
    // Send confirmation back to Python
    Serial.print("OK X:");
    Serial.print(posX);
    Serial.print(" Y:");
    Serial.println(posY);
  } else {
    Serial.println("ERROR: Invalid command format");
  }
}
