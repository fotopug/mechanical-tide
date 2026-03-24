/*
 * Mechanical Tide Clock - Serial Command Handler
 * Parse and handle serial commands from Python application
 */

#ifndef SERIAL_HANDLER_H
#define SERIAL_HANDLER_H

#include "config.h"

// Status modes (defined in main sketch)
enum StatusMode {
  STARTUP_PULSE,
  NORMAL_OPERATION,
  SUCCESS_BLINK,
  FAILURE_BLINK,
  INTERMITTENT_ERROR
};

// External references (defined in main sketch)
extern StatusMode currentMode;
extern float tidePosition;
extern uint8_t baseColorR, baseColorG, baseColorB;
extern float wavePeriod;
extern bool dataReceived;

/*
 * Parse TIDE command: TIDE:<pos>,<r>,<g>,<b>
 * Example: TIDE:3.75,255,200,0
 */
bool parseTideCommand(String cmd) {
  // Remove "TIDE:" prefix
  cmd = cmd.substring(5);
  
  // Parse position
  int firstComma = cmd.indexOf(',');
  if (firstComma == -1) return false;
  
  String posStr = cmd.substring(0, firstComma);
  tidePosition = posStr.toFloat();
  
  // Validate position (0.0 - 9.999)
  if (tidePosition < 0.0 || tidePosition >= 10.0) {
    return false;
  }
  
  // Parse RGB values
  cmd = cmd.substring(firstComma + 1);
  int secondComma = cmd.indexOf(',');
  if (secondComma == -1) return false;
  
  String rStr = cmd.substring(0, secondComma);
  baseColorR = rStr.toInt();
  
  cmd = cmd.substring(secondComma + 1);
  int thirdComma = cmd.indexOf(',');
  if (thirdComma == -1) return false;
  
  String gStr = cmd.substring(0, thirdComma);
  baseColorG = gStr.toInt();
  
  String bStr = cmd.substring(thirdComma + 1);
  baseColorB = bStr.toInt();
  
  return true;
}

/*
 * Parse WAVE command: WAVE:<period>
 * Example: WAVE:6.5
 */
bool parseWaveCommand(String cmd) {
  // Remove "WAVE:" prefix
  cmd = cmd.substring(5);
  
  float period = cmd.toFloat();
  
  // Validate period (2.0 - 8.0 seconds, as per spec)
  if (period < 2.0 || period > 8.0) {
    return false;
  }
  
  wavePeriod = period;
  return true;
}

/*
 * Parse STATUS command: STATUS:<state>
 * Example: STATUS:SUCCESS, STATUS:FAIL, STATUS:ERROR
 */
bool parseStatusCommand(String cmd) {
  // Remove "STATUS:" prefix
  cmd = cmd.substring(7);
  cmd.trim();
  
  if (cmd == "SUCCESS") {
    currentMode = SUCCESS_BLINK;
    return true;
  } else if (cmd == "FAIL") {
    currentMode = FAILURE_BLINK;
    return true;
  } else if (cmd == "ERROR") {
    currentMode = INTERMITTENT_ERROR;
    return true;
  }
  
  return false;
}

/*
 * Main serial command parser
 * Reads incoming commands and routes to appropriate handler
 */
void parseSerialCommand() {
  if (!Serial.available()) {
    return;
  }
  
  String cmd = Serial.readStringUntil('\n');
  cmd.trim();
  
  if (cmd.length() == 0) {
    return;
  }
  
  bool success = false;
  
  if (cmd.startsWith("TIDE:")) {
    success = parseTideCommand(cmd);
    if (success) {
      currentMode = NORMAL_OPERATION;
      dataReceived = true;
    }
  } 
  else if (cmd.startsWith("WAVE:")) {
    success = parseWaveCommand(cmd);
  } 
  else if (cmd.startsWith("STATUS:")) {
    success = parseStatusCommand(cmd);
  }
  else {
    Serial.println("ERR:Unknown command");
    return;
  }
  
  if (success) {
    Serial.println("OK");
  } else {
    Serial.println("ERR:Invalid format");
  }
}

#endif // SERIAL_HANDLER_H
