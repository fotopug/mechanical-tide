/*
 * Mechanical Tide Clock - LED Renderer
 * Functions for rendering LED patterns and effects
 */

#ifndef LED_RENDERER_H
#define LED_RENDERER_H

#include <Adafruit_NeoPixel.h>
#include "config.h"

// External references (defined in main sketch)
extern Adafruit_NeoPixel pixels;
extern float tidePosition;
extern uint8_t baseColorR, baseColorG, baseColorB;
extern float wavePeriod;

/*
 * Calculate breathing brightness using sine wave
 * Returns value between BREATHING_MIN and BREATHING_MAX
 */
float calculateBreathingBrightness(unsigned long currentTime, float period) {
  float t = currentTime / 1000.0;  // Convert to seconds
  float phase = (2.0 * PI * t) / period;
  return BREATHING_MIN + (BREATHING_MAX - BREATHING_MIN) * (0.5 + 0.5 * sin(phase));
}

/*
 * Fill all LEDs with a single color
 */
void fillAll(uint8_t r, uint8_t g, uint8_t b) {
  for (int i = 0; i < NUM_LEDS; i++) {
    pixels.setPixelColor(i, pixels.Color(r, g, b));
  }
}

/*
 * Clear all LEDs
 */
void clearAll() {
  fillAll(0, 0, 0);
}

/*
 * Render startup pulse animation (aqua pulsing on all LEDs)
 */
void renderStartupPulse() {
  float t = millis() / 1000.0;
  float brightness = 0.3 + 0.4 * (0.5 + 0.5 * sin(t * 2.0));  // Gentle pulse
  
  uint8_t r = STARTUP_R * brightness;
  uint8_t g = STARTUP_G * brightness;
  uint8_t b = STARTUP_B * brightness;
  
  fillAll(r, g, b);
}

/*
 * Render tide display with multi-LED gradient and breathing effect
 */
void renderTideDisplay() {
  unsigned long currentTime = millis();
  
  // Calculate breathing brightness
  float breathBrightness = calculateBreathingBrightness(currentTime, wavePeriod);
  
  // Calculate LED positions and intensities
  int primaryLED = (int)tidePosition;
  int secondaryLED = (primaryLED + 1) % NUM_LEDS;
  float fraction = tidePosition - primaryLED;
  
  // Initialize all intensities to 0
  float intensities[NUM_LEDS];
  for (int i = 0; i < NUM_LEDS; i++) {
    intensities[i] = 0.0;
  }
  
  // Set primary and secondary LED intensities
  intensities[primaryLED] = 1.0;
  intensities[secondaryLED] = fraction;
  
  // Add gradient glow to neighbors
  int neighborBefore = (primaryLED - 1 + NUM_LEDS) % NUM_LEDS;
  int neighborAfter = (secondaryLED + 1) % NUM_LEDS;
  intensities[neighborBefore] = GRADIENT_NEIGHBOR_INTENSITY;
  intensities[neighborAfter] = GRADIENT_FAR_INTENSITY;
  
  // Render with gradient and breathing
  for (int i = 0; i < NUM_LEDS; i++) {
    float intensity = intensities[i] * breathBrightness;
    uint8_t r = baseColorR * intensity;
    uint8_t g = baseColorG * intensity;
    uint8_t b = baseColorB * intensity;
    pixels.setPixelColor(i, pixels.Color(r, g, b));
  }
}

/*
 * Render success animation (double-blink green)
 * Returns true when animation is complete
 */
bool renderSuccessBlink() {
  static int blinkCount = 0;
  static unsigned long lastBlink = 0;
  static bool initialized = false;
  
  if (!initialized) {
    blinkCount = 0;
    lastBlink = millis();
    initialized = true;
  }
  
  unsigned long now = millis();
  
  if (now - lastBlink > STATUS_BLINK_MS) {
    blinkCount++;
    lastBlink = now;
    
    if (blinkCount % 2 == 1) {
      fillAll(SUCCESS_R, SUCCESS_G, SUCCESS_B);  // Green ON
    } else {
      clearAll();  // OFF
    }
    
    if (blinkCount >= 4) {  // 2 complete blinks (on-off-on-off)
      initialized = false;
      return true;  // Animation complete
    }
  }
  
  return false;  // Animation still running
}

/*
 * Render failure animation (slow red blink at 1 Hz)
 */
void renderFailureBlink() {
  unsigned long t = millis();
  bool on = (t / 1000) % 2 == 0;
  
  if (on) {
    fillAll(FAILURE_R, FAILURE_G, FAILURE_B);  // Red
  } else {
    clearAll();  // Off
  }
}

/*
 * Render tide display with intermittent error indicator
 * Shows normal tide display + blinking red LED 9
 */
void renderTideWithError() {
  // Render normal tide display
  renderTideDisplay();
  
  // Add blinking error LED on LED 9
  unsigned long t = millis();
  bool on = (t / 500) % 2 == 0;  // 2 Hz blink
  
  if (on) {
    pixels.setPixelColor(9, pixels.Color(ERROR_R, ERROR_G, ERROR_B));
  }
}

#endif // LED_RENDERER_H
