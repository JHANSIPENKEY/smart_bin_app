import cv2
import numpy as np
import os
import time
import serial  # for Arduino communication
from tensorflow.keras.models import load_model

# Load the trained model
model = load_model(r"D:\app_connect_dashboard\model.keras")

# Arduino setup
#arduino = serial.Serial('COM3', 9600, timeout=1)  # Change COM port if needed
time.sleep(2)  # Wait for Arduino to initialize

# Class labels
class_names = ['Non-Recyclable', 'Organic', 'Plastic', 'Recyclable']
IMG_SIZE = 224

# Output folder for images
os.makedirs("captures", exist_ok=True)
capture_count = 1

# Debouncing
last_confident_detection_time = {}
COOLDOWN_PERIOD = 5
  # seconds
current_display_label = "Unknown"
current_display_conf = 0.0
last_displayed_update_time = 0.0
last_label = None  # For Arduino communication

# Start webcam
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("❌ Error: Could not open webcam.")
    exit()

print("✅ Waste Detector with Arduino Started!")
print(" - Press 'q' to quit")
print(" - Press 's' to save frame")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Frame grab failed.")
        break

    h, w, _ = frame.shape
    cx, cy = w // 2, h // 2
    left, top = max(0, cx - IMG_SIZE // 2), max(0, cy - IMG_SIZE // 2)
    right, bottom = min(w, cx + IMG_SIZE // 2), min(h, cy + IMG_SIZE // 2)
    cropped = frame[top:bottom, left:right]

    if cropped.shape[0] != IMG_SIZE or cropped.shape[1] != IMG_SIZE:
        cv2.putText(frame, "Camera not aligned", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.imshow('♻️ Waste Detector', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

    img = cropped / 255.0
    img = np.expand_dims(img, axis=0)

    pred = model.predict(img, verbose=0)
    confidence = np.max(pred)
    label_id = np.argmax(pred)
    label = class_names[label_id]

    if confidence < 0.85:
        label = "Unknown"

    current_time = time.time()
    if confidence > 0.4:
        if label not in last_confident_detection_time or \
                (current_time - last_confident_detection_time[label]) > COOLDOWN_PERIOD:
            print(f"Detected: {label} ({confidence * 100:.1f}%)")
            last_confident_detection_time[label] = current_time
            current_display_label = label
            current_display_conf = confidence
            last_displayed_update_time = current_time
    else:
        if current_display_label != "Unknown" and \
                (current_time - last_displayed_update_time) > COOLDOWN_PERIOD:
            current_display_label = "Unknown"
            current_display_conf = 0.0

    # Send signal to Arduino only if label changed
    '''if label != last_label:
        if label == "Plastic":
            arduino.write(b'1\n')
        elif label == "Organic":
            arduino.write(b'2\n')
        elif label == "Recyclable":
            arduino.write(b'3\n')
        elif label == "Unknown":
            arduino.write(b'4\n')
        last_label = label'''

    # Draw bounding box and label
    display_text = f"{current_display_label} ({current_display_conf * 100:.1f}%)"
    display_color = (0, 255, 0) if current_display_label != "Unknown" else (0, 0, 255)
    cv2.rectangle(frame, (left, top), (right, bottom), display_color, 2)
    cv2.putText(frame, display_text, (left, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, display_color, 2)

    # Show frame
    cv2.imshow('♻️ Waste Detector - Press s to capture, q to quit', frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        filename = f"captures/{current_display_label}_{capture_count}.jpg"
        cv2.imwrite(filename, frame)
        print(f"📸 Saved: {filename}")
        capture_count += 1

cap.release()
cv2.destroyAllWindows()
