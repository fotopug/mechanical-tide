/*
 * Mechanical Tide Clock - Configuration
 * Constants and pin definitions for Circuit Playground Classic
 */

#ifndef CONFIG_H
#define CONFIG_H

// Hardware Configuration
#define LED_PIN 8              // Circuit Playground NeoPixel data pin
#define NUM_LEDS 10            // Number of NeoPixels on Circuit Playground
#define SERIAL_BAUD 115200     // Serial communication baud rate

// Breathing Effect Configuration
#define BREATHING_MIN 0.30     // Minimum brightness (30%)
#define BREATHING_MAX 1.00     // Maximum brightness (100%)
#define DEFAULT_WAVE_PERIOD 7.0  // Default breathing period in seconds

// Gradient Configuration
#define GRADIENT_NEIGHBOR_INTENSITY 0.15   // Adjacent LED intensity
#define GRADIENT_FAR_INTENSITY 0.10        // Far neighbor intensity

// Timing Configuration
#define LOOP_DELAY_MS 20       // Main loop delay (~50 FPS)
#define STATUS_BLINK_MS 200    // Blink duration for status animations

// Startup Colors (Aqua pulse)
#define STARTUP_R 0
#define STARTUP_G 255
#define STARTUP_B 200

// Status Colors
#define SUCCESS_R 0
#define SUCCESS_G 255
#define SUCCESS_B 0

#define FAILURE_R 255
#define FAILURE_G 0
#define FAILURE_B 0

#define ERROR_R 255
#define ERROR_G 0
#define ERROR_B 0

#endif // CONFIG_H
