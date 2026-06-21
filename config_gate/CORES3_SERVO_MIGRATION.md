# Migrating the Servo Control from Arduino R4 → M5Stack CoreS3

Concrete plan to move the MCU side from your Arduino Uno R4 to the CoreS3 — for the **MG90S now**
and the **SCS0009 serial-bus servos later** — while keeping your laptop brain almost untouched.
Last updated: June 2026.

---

## 0. The good news: your workflow barely changes
- **Still Arduino IDE, still a single `.ino`.** The CoreS3 is an ESP32-S3 — flash it from the
  Arduino IDE after installing **(a)** the *esp32 by Espressif* boards package (Boards Manager) and
  **(b)** the **M5Unified / M5CoreS3** library, then select board **"M5CoreS3"** and upload over
  USB-C. Same edit-compile-upload loop you have now.
- **The laptop ↔ MCU link is identical.** The CoreS3 is a USB-serial device just like the Uno, so
  your laptop talks to it over USB serial exactly as today (same `"dPan,dTilt\n"` line). **Keep
  `rig.py`'s `move_to(pan,tilt)` contract — only the serial *port name* changes.** Your brain code
  (planner/CV/`rig.py`) is essentially untouched.
- **One code swap:** the AVR `Servo.h` doesn't drive ESP32 PWM the same way → use **`ESP32Servo.h`**
  (a near drop-in). That's the only real porting change for MG90S.

---

## 1. MG90S on the CoreS3 (do this now — PWM hobby servos)

**Wiring**
- **Signal:** use **Grove Port B (GPIO 8, GPIO 9)** → pan = G8, tilt = G9.
- **Power:** MG90S want **5 V**; drive them from an **external 5 V supply**, **not** the CoreS3's
  pins (a stalling MG90S pulls enough current to brown-out the CoreS3). **Common ground** between
  the 5 V supply and the CoreS3. (3.3 V PWM signal from the ESP32 drives MG90S fine.)

**Sketch (your `pantilt_r4.ino`, ported — same serial protocol)**
```cpp
#include <M5Unified.h>
#include <ESP32Servo.h>          // NOT the AVR Servo.h
Servo pan, tilt;
const int PAN_PIN = 8, TILT_PIN = 9;          // Grove Port B
const int PAN_C = 90, TILT_C = 90;

void setup() {
  M5.begin();
  Serial.begin(115200);                        // USB serial to the laptop (as before)
  pan.attach(PAN_PIN, 500, 2400);
  tilt.attach(TILT_PIN, 500, 2400);
  pan.write(PAN_C); tilt.write(TILT_C);
}
void loop() {
  if (Serial.available()) {
    String l = Serial.readStringUntil('\n'); l.trim();
    int c = l.indexOf(',');
    if (c > 0) {
      int dP = l.substring(0, c).toInt();
      int dT = l.substring(c + 1).toInt();
      pan.write(constrain(PAN_C + dP, 30, 150));
      tilt.write(constrain(TILT_C + dT, 55, 125));
      M5.Display.setCursor(0, 0);
      M5.Display.printf("pan %+d  tilt %+d   ", dP, dT);   // free: show on the screen
    }
  }
}
```
On the laptop, point `rig.py` at the CoreS3's port — done. (Bonus: you now have a screen, so the
read-back text can appear on the robot.)

---

## 2. SCS0009 later (serial-bus servos — a different control method)

SCS0009 are **NOT PWM**; they're **TTL half-duplex serial bus** servos (one data line, daisy-chained,
each with an ID, position feedback). So `ESP32Servo` does **not** apply — you talk a protocol over a
UART. Two ways to wire it; pick by how much you want on the MCU.

### Option A — Laptop drives the bus directly (simplest; recommended for the switch)
- Buy a **USB bus-servo adapter** — e.g. the **FeeTech FE-URT-2** (FE-URT2-C001, switch-science
  #11186, ~¥1,540; updated FE-URT-1) or a **Waveshare Bus Servo Adapter**. Plug the SCS bus into
  its **TTL/SCS port**, adapter → laptop **USB-C**.
- On the laptop, use the **FeeTech SCServo Python SDK** (`scservo_sdk`) and have `rig.py.move_to()`
  call `WritePosEx(id, pos, speed, acc)`. The laptop already computes the gaze targets, so this is
  natural.
- **CoreS3 does servos = nothing** → it's freed for voice + screen + LED.
- Pro: no half-duplex wiring on the MCU; one library, on the machine that has the targets. Con: a
  second USB device on the laptop.

> **"Where do I flash the FE-URT-2?" — you don't.** It is **not** a microcontroller; it's a dumb
> **USB-to-serial adapter** with no program of its own. You install its **USB driver** once (CH343/
> CH340 — on macOS install the CH34x driver; the servos appear as a `/dev/tty.*` port), then the
> control code lives **in your laptop's Python** (`rig.py` + `scservo_sdk`). Nothing is uploaded to
> the board. Notes: it drives the **SCS0009 (bus) only, not the MG90S (PWM)**; set servo IDs
> (pan=1, tilt=2) with FeeTech's tool first; power the servos from an **external ~6 V** on the
> board's terminal (not USB 5 V); it handles **only the servo bus** — LED/buzzer/mic/screen still
> need the CoreS3.

### Option B — CoreS3 drives the bus (keeps today's "pan,tilt over serial" architecture)
- **Wiring:** **Grove Port C (GPIO 17 / 18) as a UART** (`Serial2`) → the SCS data line. The bus is
  **half-duplex (1 wire)**, so you need either a small **half-duplex transceiver / bus-servo driver
  breakout** between the UART and the servos, or FeeTech's recommended TX/RX-tie circuit. (3.3 V TTL
  from the ESP32 is bus-compatible — verify against your servo's logic level.)
- **Library:** FeeTech **`SCServo.h`** (`SCSCL` class for the SCS series), bound to `Serial2`.
- The CoreS3 still receives your `"dPan,dTilt\n"` from the laptop and translates it to servo
  commands — so the **laptop side and protocol stay the same** as now.

**Sketch (Option B skeleton)**
```cpp
#include <M5Unified.h>
#include <SCServo.h>
SCSCL sc;
int angToTick(int deg){ return map(deg, -150, 150, 0, 1023); }   // 300° → 0..1023

void setup(){
  M5.begin();
  Serial.begin(115200);                                  // laptop
  Serial2.begin(1000000, SERIAL_8N1, 18, 17);            // Port C: (RX=18, TX=17) — match your adapter
  sc.pSerial = &Serial2;
}
void loop(){
  if (Serial.available()){
    String l = Serial.readStringUntil('\n'); l.trim();
    int c = l.indexOf(',');
    if (c > 0){
      int dP = l.substring(0,c).toInt();
      int dT = l.substring(c+1).toInt();
      sc.WritePos(1, angToTick(dP), 0, 1500);            // id 1 = pan
      sc.WritePos(2, angToTick(dT), 0, 1500);            // id 2 = tilt
    }
  }
}
```
**Before first use:** assign each servo an **ID** (pan = 1, tilt = 2) with FeeTech's config tool;
power from a **separate 6 V supply**, common ground.

---

## 3. Power & logic — the rules that prevent magic smoke
- **Never power servos from the CoreS3.** MG90S = external **5 V**; SCS0009 = external **6 V** (≈1 A
  stall each). Grove's 5 V pin can't source that — it'll brown-out/reset the CoreS3.
- **Common ground** between the servo supply and the CoreS3, always.
- **Logic level:** ESP32-S3 is 3.3 V — fine for MG90S PWM and for the SCS TTL bus (verify the bus
  voltage on your servos).
- **USB cable + pan:** the SCS0009 reach 300°/continuous — remember the **USB-camera cable tangle**
  caveat: bound the pan or use a slip ring (see `HARDWARE_ARCHITECTURE.md §3`).

---

## 4. Suggested migration order (small, safe steps)
1. **Now:** port the MG90S sketch to the CoreS3 (§1) — ESP32Servo, Port B, *same* `pan,tilt` serial
   protocol. Swap the Uno for the CoreS3, change the port in `rig.py`, confirm it moves. (Half a day.)
2. Incrementally add the CoreS3's extras in the same sketch: **screen** read-back text (`M5.Display`),
   **mic** push-to-talk + audio-stream (later), **LED antenna** via a Grove pin, buzzer.
3. **When you switch to SCS0009:** choose **Option A** (laptop drives via USB adapter — least
   friction) or **Option B** (CoreS3 drives the bus — keeps the robot on one USB). Either way, keep
   `rig.py.move_to(pan,tilt)` as the stable contract so the brain code doesn't change.

> Key principle: **the `move_to(pan,tilt)` abstraction and the serial line stay constant; only what's
> *behind* them changes** (Uno→CoreS3, PWM→bus servo). That's what makes each step a small swap, not
> a rewrite.

---

## Sources
- M5Stack **CoreS3** Grove pinout: **Port A** I2C (G2/G1), **Port B** GPIO (G9/G8), **Port C** UART
  (G18/G17). https://devices.esphome.io/devices/m5stack-cores3/ · https://docs.m5stack.com/en/core/CoreS3
- ESP32 PWM servos via **ESP32Servo** library; FeeTech **SCServo** Arduino lib / **scservo_sdk**
  Python; FeeTech FE-URT-1 / Waveshare Bus Servo Adapter for USB bus control.
- Project internal: `HARDWARE_ARCHITECTURE.md` (controller choice, SCS0009 reality, power), `rig.py`
  (the `move_to`/serial contract to preserve).
