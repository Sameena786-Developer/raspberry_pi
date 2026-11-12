from ultralytics import YOLO
import cv2
import time
import sys
import paho.mqtt.client as mqtt

# ---------------- CONFIGURATION ----------------

MODEL_PATH = "best (1).pt"

CAMERA_URL = "http://192.0.0.4:8080/video"

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "enerlytix/room1"

CLIENT_ID = "EnerlytixYOLO-Room1"

CONFIDENCE = 0.30
NO_PERSON_TIME = 5

HEARTBEAT_INTERVAL = 5

# ---------------- LOAD YOLO MODEL ----------------

print("Loading YOLO model...")

model = YOLO(MODEL_PATH)

print("YOLO model loaded successfully.")

# ---------------- MQTT CONNECTION ----------------

client = mqtt.Client(
    client_id=CLIENT_ID,
    protocol=mqtt.MQTTv311
)

print("Connecting to MQTT broker...")

try:
    client.connect(BROKER, PORT, 60)
    client.loop_start()

except Exception as e:
    print("MQTT connection failed:", e)
    sys.exit(1)

# Wait for MQTT connection
connection_start = time.monotonic()

while not client.is_connected():
    if time.monotonic() - connection_start > 10:
        print("ERROR: MQTT connection timeout.")
        client.loop_stop()
        sys.exit(1)

    time.sleep(0.2)

print("MQTT connected successfully.")

# ---------------- MQTT PUBLISH FUNCTION ----------------

def publish_state(state):

    if not client.is_connected():
        print("WARNING: MQTT disconnected. Command not sent.")
        return False

    try:
        result = client.publish(
            TOPIC,
            state,
            qos=1,
            retain=False
        )

        result.wait_for_publish(timeout=3)

        if result.is_published():
            print(f"MQTT COMMAND SENT: {state}")
            return True

        print("WARNING: MQTT publish not confirmed.")
        return False

    except Exception as e:
        print("MQTT publish error:", e)
        return False


# Send initial OFF command
publish_state("OFF")

# ---------------- CAMERA CONNECTION ----------------

cap = cv2.VideoCapture(CAMERA_URL)

if not cap.isOpened():
    print("ERROR: Could not connect to mobile camera.")

    publish_state("OFF")
    cap.release()
    client.loop_stop()
    client.disconnect()
    sys.exit(1)

print("Camera connected.")
print("Starting person detection...")
print("--------------------------------")

# ---------------- CONTROL VARIABLES ----------------

device_on = False
no_person_start = None

last_heartbeat = time.monotonic()

# ---------------- MAIN LOOP ----------------

try:

    while True:

        ret, frame = cap.read()

        if not ret:
            print("ERROR: Could not read camera frame.")

            # Allow the ESP32 watchdog to turn the relay OFF
            time.sleep(1)
            continue

        # YOLO person detection
        results = model.predict(
            source=frame,
            conf=CONFIDENCE,
            imgsz=640,
            classes=[0],
            verbose=False
        )

        person_detected = False

        for result in results:

            if result.boxes is not None:

                for box in result.boxes:

                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])

                    if class_id == 0 and confidence >= CONFIDENCE:
                        person_detected = True
                        break

        # ---------------- PERSON DETECTED ----------------

        if person_detected:

            no_person_start = None

            if not device_on:

                device_on = True

                publish_state("ON")

                print("PERSON DETECTED -> DEVICE ON")

            else:

                print("PERSON DETECTED")

        # ---------------- NO PERSON DETECTED ----------------

        else:

            print("NO PERSON DETECTED")

            if no_person_start is None:

                no_person_start = time.monotonic()

            elapsed = time.monotonic() - no_person_start

            if elapsed >= NO_PERSON_TIME:

                if device_on:

                    device_on = False

                    publish_state("OFF")

                    print("ROOM EMPTY FOR 5 SECONDS -> DEVICE OFF")

                no_person_start = None

        # ---------------- HEARTBEAT ----------------

        current_time = time.monotonic()

        if current_time - last_heartbeat >= HEARTBEAT_INTERVAL:

            current_state = "ON" if device_on else "OFF"

            publish_state(current_state)

            last_heartbeat = current_time

        # ---------------- DISPLAY ----------------

        annotated_frame = results[0].plot()

        state_text = "DEVICE: ON" if device_on else "DEVICE: OFF"

        cv2.putText(
            annotated_frame,
            state_text,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0) if device_on else (0, 0, 255),
            2
        )

        cv2.imshow("YOLO Person Detection", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

# ---------------- CLEANUP ----------------

except KeyboardInterrupt:

    print("Program interrupted.")

finally:

    print("Turning device OFF...")

    publish_state("OFF")

    cap.release()
    cv2.destroyAllWindows()

    client.loop_stop()
    client.disconnect()

    print("--------------------------------")
    print("Program stopped.")