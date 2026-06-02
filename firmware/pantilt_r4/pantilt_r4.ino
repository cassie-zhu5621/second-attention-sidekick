/*
 * Pan-tilt v1 test sketch  —  Arduino Uno R4 + 2x MG90S
 * Second Attention sidekick (hardware test)
 *
 * Library: built-in "Servo" (no install needed)
 *
 * Wiring:
 *   PAN  signal (orange) -> pin D9
 *   TILT signal (orange) -> pin D10
 *   servo V+ (red)       -> R4 5V pin   (USB-C charger, 2-3A, NOT a PC port)
 *   servo GND (brown)    -> R4 GND
 *   (optional) 1000uF cap across 5V/GND
 *
 * R4 signal is 5V -> more reliable for MG90S than ESP32's 3.3V.
 *
 * What it does:
 *   1. On boot, slow eased sweep, ONE axis at a time (low peak current).
 *   2. Then listens on Serial (115200) for "pan,tilt\n"  e.g.  "30,-10"
 *      -> matches rig.py _format_cmd seam. Angles are relative to center.
 */

#include <Servo.h>

const int PAN_PIN    = 9;
const int TILT_PIN   = 10;
const int BUTTON_PIN = 2;   // button other leg -> GND (uses internal pull-up)

// Mechanical center + safe limits (degrees). Tune to your build.
const int PAN_CENTER  = 90;
const int TILT_CENTER = 90;
const int PAN_MIN = 30,  PAN_MAX = 150;
const int TILT_MIN = 55, TILT_MAX = 125;   // ~+/-35 deg, CoreS3 overhang

Servo pan;
Servo tilt;

int curPan  = PAN_CENTER;
int curTilt = TILT_CENTER;

// Sweep waypoints (4 corners). Toggle on/off with the button.
const int NWP = 4;
const int wpPan[NWP]  = { 30, 150, 150,  30 };   // matches PAN_MIN/MAX
const int wpTilt[NWP] = { 55,  55, 125, 125 };   // matches TILT_MIN/MAX
int wp = 0;
unsigned long lastStep = 0;
const int SWEEP_STEP_MS = 50;     // bigger = slower glide (observing pace)
const int DWELL_MS      = 10000;  // pause 10s at each corner = "observing"
// Rhythm: glide(=searching) -> dwell 10s(=observing). The camera is a separate
// WiFi node; it detects stillness on its own and captures during these dwells
// (every ~3s), so move frames (blurry) are skipped. No wire between the boards.

bool sweeping  = false;          // toggled by button
bool dwelling  = false;          // currently paused at a corner
unsigned long dwellUntil = 0;

// Button debounce / edge-detect
int btnStable = HIGH, btnLast = HIGH;
unsigned long btnDebounce = 0;

int clampi(int v, int lo, int hi) { return v < lo ? lo : (v > hi ? hi : v); }

// Move both axes smoothly to target (eased: small steps, no snapped writes)
void easeTo(int tgtPan, int tgtTilt, int stepDelayMs = 15) {
  tgtPan  = clampi(tgtPan,  PAN_MIN,  PAN_MAX);
  tgtTilt = clampi(tgtTilt, TILT_MIN, TILT_MAX);
  while (curPan != tgtPan || curTilt != tgtTilt) {
    if (curPan  < tgtPan)  curPan++;  else if (curPan  > tgtPan)  curPan--;
    if (curTilt < tgtTilt) curTilt++; else if (curTilt > tgtTilt) curTilt--;
    pan.write(curPan);
    tilt.write(curTilt);
    delay(stepDelayMs);
  }
}

void setup() {
  Serial.begin(115200);
  delay(300);

  pinMode(BUTTON_PIN, INPUT_PULLUP);   // pressed = LOW

  pan.attach(PAN_PIN,  500, 2400);   // MG90S pulse range (us)
  tilt.attach(TILT_PIN, 500, 2400);

  curPan = PAN_CENTER; curTilt = TILT_CENTER;
  pan.write(curPan);
  tilt.write(curTilt);
  delay(500);

  // Boot sweep -- BOTH axes together (diagonal), SLOW (35ms/step) to keep
  // peak current low so two servos can move at once on a modest supply.
  Serial.println("Boot sweep (both axes together, slow)...");
  easeTo(PAN_MIN,  TILT_MIN, 35);
  easeTo(PAN_MAX,  TILT_MAX, 35);
  easeTo(PAN_MIN,  TILT_MAX, 35);
  easeTo(PAN_MAX,  TILT_MIN, 35);
  easeTo(PAN_CENTER, TILT_CENTER, 35);
  Serial.println("Ready. Send 'pan,tilt' e.g. 30,-10 (both move together)");
}

void loop() {
  // --- Button: each press TOGGLES sweeping on/off (debounced) ---
  int btn = digitalRead(BUTTON_PIN);
  if (btn != btnLast) { btnDebounce = millis(); btnLast = btn; }
  if (millis() - btnDebounce > 30 && btn != btnStable) {
    btnStable = btn;
    if (btnStable == LOW) {            // just pressed
      sweeping = !sweeping;            // toggle
      dwelling = false;                // start moving immediately
      Serial.println(sweeping ? "sweep ON" : "sweep OFF");
    }
  }

  // --- Sweeping: glide to a corner, pause to observe, go to next ---
  if (sweeping) {
    if (dwelling) {
      if (millis() >= dwellUntil) dwelling = false;   // done observing
    } else if (millis() - lastStep >= (unsigned long)SWEEP_STEP_MS) {
      lastStep = millis();
      int tp = clampi(wpPan[wp],  PAN_MIN,  PAN_MAX);
      int tt = clampi(wpTilt[wp], TILT_MIN, TILT_MAX);
      if (curPan  < tp) curPan++;  else if (curPan  > tp) curPan--;
      if (curTilt < tt) curTilt++; else if (curTilt > tt) curTilt--;
      pan.write(curPan);
      tilt.write(curTilt);
      if (curPan == tp && curTilt == tt) {            // reached a corner
        wp = (wp + 1) % NWP;
        dwelling = true;
        dwellUntil = millis() + DWELL_MS;             // pause and "observe"
      }
    }
    return;   // while sweeping, ignore serial
  }

  // --- Stopped: accept "pan,tilt" over serial ---
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    int comma = line.indexOf(',');
    if (comma > 0) {
      int dPan  = line.substring(0, comma).toInt();   // relative to center
      int dTilt = line.substring(comma + 1).toInt();
      easeTo(PAN_CENTER + dPan, TILT_CENTER + dTilt);
      Serial.print("-> pan="); Serial.print(curPan);
      Serial.print(" tilt="); Serial.println(curTilt);
    }
  }
}
