import cv2
from ultralytics import YOLO

# Load model
model = YOLO("bullseye.pt")

# Open webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Run inference
    results = model(frame, imgsz=640)

    # Plot results
    annotated_frame = results[0].plot()

    # Show
    cv2.imshow("YOLO Webcam", annotated_frame)

    # Press q to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()