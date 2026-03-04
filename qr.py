import cv2
from pyzbar.pyzbar import decode

# open camera
cap = cv2.VideoCapture(0)   # laptop webcam

while True:
    ret, frame = cap.read()

    if not ret:
        print("Camera not working")
        break

    # detect QR / barcode
    barcodes = decode(frame)

    for barcode in barcodes:
        data = barcode.data.decode("utf-8")
        print("Detected:", data)

        x, y, w, h = barcode.rect
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)

    cv2.imshow("QR Scanner", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()