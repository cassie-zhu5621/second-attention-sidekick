/*
 * pantilt_sweep.ino — Arduino Uno R4 + 2x MG90S  (DATASET-COLLECTION sweep)
 *
 * For collecting a dataset WITHOUT the brain: on power-up it autonomously sweeps a
 * pan/tilt grid forever — glide to a spot, DWELL a few seconds (so the camera's
 * stillness capture grabs sharp frames), then move to the next spot. No laptop,
 * no serial, no button needed; just power the R4.
 *
 * Pair with: the collector camera (sidekick-cam) + sidekick_collector.py, which
 * saves the still frames. For the LIVE brain loop instead, flash pantilt_r4.ino.
 *
 * Wiring: PAN -> D9, TILT -> D10, servo V+ -> external 5V, GND shared.
 */

#include <Servo.h>

const int PAN_PIN  = 9;
const int TILT_PIN = 10;

const int PAN_CENTER  = 90;
const int TILT_CENTER = 90;
const int PAN_MIN = 30,  PAN_MAX = 150;
const int TILT_MIN = 55, TILT_MAX = 125;

const int   STEP_MS  = 40;     // glide pace (bigger = slower, gentler current)
const long  DWELL_MS = 8000;   // pause at each spot so the camera captures still frames

// scan grid (offsets from center) — boustrophedon so it doesn't jump across each row
const int PAN_OFFS[]  = { -60, -30, 0, 30, 60 };
const int TILT_OFFS[] = { -25, 0, 25 };

Servo pan, tilt;
int curPan = PAN_CENTER, curTilt = TILT_CENTER;

int clampi(int v, int lo, int hi) { return v < lo ? lo : (v > hi ? hi : v); }

void easeTo(int tp, int tt) {
  tp = clampi(tp, PAN_MIN, PAN_MAX);
  tt = clampi(tt, TILT_MIN, TILT_MAX);
  while (curPan != tp || curTilt != tt) {
    if (curPan  < tp) curPan++;  else if (curPan  > tp) curPan--;
    if (curTilt < tt) curTilt++; else if (curTilt > tt) curTilt--;
    pan.write(curPan);
    tilt.write(curTilt);
    delay(STEP_MS);
  }
}

void setup() {
  Serial.begin(115200);
  pan.attach(PAN_PIN, 500, 2400);
  tilt.attach(TILT_PIN, 500, 2400);
  easeTo(PAN_CENTER, TILT_CENTER);
  Serial.println("autonomous sweep (dataset mode) — sweeping forever");
}

void loop() {
  int nT = sizeof(TILT_OFFS) / sizeof(int);
  int nP = sizeof(PAN_OFFS) / sizeof(int);
  for (int ti = 0; ti < nT; ti++) {
    for (int k = 0; k < nP; k++) {
      int pi = (ti % 2 == 0) ? k : (nP - 1 - k);     // boustrophedon
      easeTo(PAN_CENTER + PAN_OFFS[pi], TILT_CENTER + TILT_OFFS[ti]);
      Serial.print("dwell @ pan="); Serial.print(curPan);
      Serial.print(" tilt="); Serial.println(curTilt);
      delay(DWELL_MS);                               // hold still for capture
    }
  }
}
