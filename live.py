import cv2
import numpy as np
import time
import requests
import pyttsx3
from tensorflow.keras.models import load_model

# ===============================
# CONFIG
# ===============================
MODEL_PATH = r"D:\app_connect_dashboard\model.keras"
API_URL = "http://127.0.0.1:5000/dispose"
USER_API = "http://127.0.0.1:5000/user"

class_names = ['Non-Recyclable', 'Organic', 'Plastic', 'Recyclable']

CONFIDENCE_THRESHOLD = 0.85
COOLDOWN = 5
USER_TIMEOUT = 30  # auto reset after 30 seconds

# ===============================
# LOAD MODEL
# ===============================
model = load_model(MODEL_PATH, compile=False)

# ===============================
# VOICE ENGINE
# ===============================
engine = pyttsx3.init()
engine.setProperty('rate', 160)

def speak(text):
    engine.say(text)
    engine.runAndWait()

# ===============================
# CAMERA
# ===============================
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("❌ Camera not opening")
    exit()

# ===============================
# BARCODE DETECTOR
# ===============================
barcode_detector = cv2.barcode_BarcodeDetector()

# ===============================
# VARIABLES
# ===============================
active_user = None
active_user_name = None
last_sent_time = 0
last_barcode = None
user_start_time = 0

print("📷 Scan bar Code to Start...")

# ===============================
# MAIN LOOP
# ===============================
while True:
    ret, frame = cap.read()
    if not ret:
        break

    key = cv2.waitKey(1) & 0xFF

    # RESET USER
    if key == ord('r'):
        print("🔄 Resetting user...")
        active_user = None
        active_user_name = None
        last_barcode = None
        last_sent_time = 0
        speak("Scan next user")
        time.sleep(1)

    # AUTO RESET
    if active_user and (time.time() - user_start_time > USER_TIMEOUT):
        print("⏳ Auto reset user")
        active_user = None
        active_user_name = None
        last_barcode = None

    # ===============================
    # STEP 1: SCAN BARCODE
    # ===============================
    if active_user is None:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        decoded_info, points, _ = barcode_detector.detectAndDecode(gray)

        if decoded_info is not None and decoded_info != "":
            user_id = str(decoded_info).strip()

            if user_id != last_barcode:
                print("BARCODE DETECTED:", user_id)

                active_user = user_id
                last_barcode = user_id
                user_start_time = time.time()

                try:
                    response = requests.get(
                        f"{USER_API}/{active_user}",
                        timeout=10
                    )
                    user_data = response.json()
                    active_user_name = user_data.get("name", "Student")
                except:
                    active_user_name = "Student"

                speak(f"Welcome {active_user_name}")

        cv2.putText(frame, "Scan Barcode", (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Smart Waste Bin", frame)

        if key == ord('q'):
            break

        continue

    # ===============================
    # STEP 2: WASTE DETECTION
    # ===============================
    h, w, _ = frame.shape
    cx, cy = w // 2, h // 2

    crop = frame[cy-112:cy+112, cx-112:cx+112]

    if crop.shape[0] != 224 or crop.shape[1] != 224:
        cv2.imshow("Smart Waste Bin", frame)
        continue

    img = crop / 255.0
    img = np.expand_dims(img, axis=0)

    pred = model.predict(img, verbose=0)
    confidence = float(np.max(pred))
    label = class_names[np.argmax(pred)]

    # ===============================
    # STEP 3: SEND TO BACKEND
    # ===============================
    if confidence > CONFIDENCE_THRESHOLD and time.time() - last_sent_time > COOLDOWN:

        payload = {
            "userId": active_user,
            "wasteType": label,
            "confidence": confidence
        }

        try:
            response = requests.post(API_URL, json=payload, timeout=15)

            if response.status_code == 200:
                result = response.json()
                credits_added = result.get("creditsAdded", 0)

                print(f"♻️ {label} → {credits_added} credits to {active_user_name}")
                speak(f"{label} waste detected. {credits_added} credits added")

                last_sent_time = time.time()
            else:
                print("Server error:", response.status_code)

        except Exception as e:
            print("❌ Backend Error:", e)

    # ===============================
    # DISPLAY
    # ===============================
    cv2.rectangle(frame, (cx-112, cy-112),
                  (cx+112, cy+112), (0, 255, 0), 2)

    cv2.putText(frame, f"{label} ({confidence*100:.1f}%)", (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.putText(frame, f"User: {active_user_name}", (30, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

    cv2.putText(frame, "Press R to Reset User", (30, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("Smart Waste Bin", frame)

    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()