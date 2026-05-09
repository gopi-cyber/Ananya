import cv2
import numpy as np

def analyze():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Could not open camera.")
        return
        
    ret, frame = cap.read()
    if ret and frame is not None:
        cv2.imwrite("captured_frame.png", frame)
        print("Saved captured_frame.png")
        
        # Calculate stats
        mean_val = np.mean(frame)
        std_val = np.std(frame)
        unique_colors = len(np.unique(frame.reshape(-1, 3), axis=0))
        
        print(f"Mean pixel value: {mean_val:.2f}")
        print(f"Standard deviation: {std_val:.2f}")
        print(f"Unique colors count: {unique_colors}")
        
        # Check if it looks like a blocked grey frame
        # Blocked frames are usually highly grey (R ~ G ~ B) and very uniform except the logo
        h, w, _ = frame.shape
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        diff_r_g = np.mean(np.abs(frame[:,:,2].astype(float) - frame[:,:,1].astype(float)))
        diff_g_b = np.mean(np.abs(frame[:,:,1].astype(float) - frame[:,:,0].astype(float)))
        
        print(f"Mean R-G diff: {diff_r_g:.2f}")
        print(f"Mean G-B diff: {diff_g_b:.2f}")
    else:
        print("Could not read frame.")
    cap.release()

if __name__ == "__main__":
    analyze()
