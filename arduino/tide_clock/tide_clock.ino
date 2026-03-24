/*
 * Mechanical Tide Clock
 * 
 * A real-time tide visualization system using Circuit Playground Classic
 * - Displays tide position on 10 NeoPixel ring (clock-style)
 * - Multi-LED gradient effect with smooth interpolation
 * - Heat-map colors based on water level relative to Mean Sea Level
 * - Wave-synchronized breathing effect (2-8 second period)
 * 
 * Hardware: Adafruit Circuit Playground Classic
 * Communication: Serial @ 115200 baud
 * 
 * Serial Commands:
 *   TIDE:<pos>,<r>,<g>,<b>  - Set tide position (0-9.999) and base color
 *   WAVE:<period>           - Set breathing period (2-8 seconds)
 *   STATUS:<state>          - Trigger status animation (SUCCESS/FAIL/ERROR)
 * 
 * Responses:
 *   OK                      - Command successful
 *   ERR:<message>           - Command failed
 */

#include <Adafruit_NeoPixel.h>
#include "config.h"
#include "led_renderer.h"
#include "serial_handler.h"

// NeoPixel initialization
Adafruit_NeoPixel pixels(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// State variables
float tidePosition = 0.0;           // Current tide position (0.0 - 9.999)
uint8_t baseColorR = STARTUP_R;     // Base color red component
uint8_t baseColorG = STARTUP_G;     // Base color green component  
uint8_t baseColorB = STARTUP_B;     // Base color blue component
float wavePeriod = DEFAULT_WAVE_PERIOD;  // Breathing period in seconds
bool dataReceived = false;          // Has data been received from Python?

// Display mode state machine
StatusMode currentMode = STARTUP_PULSE;
StatusMode previousMode = STARTUP_PULSE;

// Timing
unsigned long lastUpdate = 0;

void setup() {
  // Initialize serial communication
  Serial.begin(SERIAL_BAUD);
  
  // Initialize NeoPixels
  pixels.begin();
  pixels.setBrightness(255);  // Full brightness (breathing effect handles dimming)
  pixels.show();  // Initialize all pixels to 'off'
  
  // Wait a moment for serial to stabilize
  delay(100);
  
  // Optional: Send startup message
  Serial.println("# Mechanical Tide Clock v1.0");
  Serial.println("# Ready for commands");
}

void loop() {
  // Handle incoming serial commands
  parseSerialCommand();
  
  // Render appropriate display based on current mode
  switch (currentMode) {
    case STARTUP_PULSE:
      renderStartupPulse();
      break;
      
    case NORMAL_OPERATION:
      renderTideDisplay();
      break;
      
    case SUCCESS_BLINK:
      // Success blink returns true when complete
      if (renderSuccessBlink()) {
        currentMode = NORMAL_OPERATION;
      }
      break;
      
    case FAILURE_BLINK:
      renderFailureBlink();
      break;
      
    case INTERMITTENT_ERROR:
      renderTideWithError();
      break;
  }
  
  // Update NeoPixels
  pixels.show();
  
  // Control frame rate (~50 FPS)
  delay(LOOP_DELAY_MS);
}

/*
 * Optional: Add test functions for standalone testing
 * Uncomment in setup() to test without Python
 */

// Test startup pulse for 10 seconds
void testStartupPulse() {
  Serial.println("# Testing startup pulse...");
  for (int i = 0; i < 500; i++) {
    renderStartupPulse();
    pixels.show();
    delay(20);
  }
  Serial.println("# Startup pulse test complete");
}

// Test tide display at a specific position
void testTideDisplay() {
  Serial.println("# Testing tide display...");
  tidePosition = 3.7;
  baseColorR = 255;
  baseColorG = 200;
  baseColorB = 0;  // Yellow
  wavePeriod = 6.0;
  currentMode = NORMAL_OPERATION;
  Serial.println("# Tide display active (position 3.7, yellow)");
}

// Test all status animations
void testStatusAnimations() {
  Serial.println("# Testing status animations...");
  
  // Test success blink
  Serial.println("# Success blink...");
  currentMode = SUCCESS_BLINK;
  for (int i = 0; i < 100; i++) {
    if (renderSuccessBlink()) break;
    pixels.show();
    delay(20);
  }
  delay(1000);
  
  // Test failure blink
  Serial.println("# Failure blink (5 seconds)...");
  currentMode = FAILURE_BLINK;
  for (int i = 0; i < 250; i++) {
    renderFailureBlink();
    pixels.show();
    delay(20);
  }
  delay(1000);
  
  // Test error indicator
  Serial.println("# Error indicator (5 seconds)...");
  tidePosition = 5.0;
  baseColorR = 0;
  baseColorG = 255;
  baseColorB = 0;  // Green
  wavePeriod = 5.0;
  currentMode = INTERMITTENT_ERROR;
  for (int i = 0; i < 250; i++) {
    renderTideWithError();
    pixels.show();
    delay(20);
  }
  
  Serial.println("# Status animations test complete");
  currentMode = NORMAL_OPERATION;
}
