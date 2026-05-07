# test_vision.py
import cv2
import numpy as np
import detection
from config import YELLOW_HSV_LOW, YELLOW_HSV_HIGH

def run_test():
    print("[TEST] Starting Manual Vision Test...")
    print("[TEST] Press 'q' to quit.")
    
    # Open the Mac's FaceTime camera
    cap = detection.open_camera()

    while True:
        try:
            # 1. Read frame from camera
            frame = detection.read_frame(cap)
            
            # 2. Check if detection triggers
            is_visible = detection.is_target_visible(frame)
            
            # 3. Get annotated frame (draws green circles)
            debug_frame = detection.annotate(frame.copy())
            
            # 4. Display status on the frame
            status_text = "TARGET DETECTED!" if is_visible else "Searching..."
            color = (0, 255, 0) if is_visible else (0, 0, 255)
            cv2.putText(debug_frame, status_text, (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

            # 5. Show the windows
            cv2.imshow("Detection Debug", debug_frame)

            # 6. Break on 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        except Exception as e:
            print(f"[ERROR] {e}")
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_test()