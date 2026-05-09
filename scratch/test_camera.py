import cv2
import sys

def test_cameras():
    print("Python version:", sys.version)
    print("OpenCV version:", cv2.__version__)
    
    backends = [
        ("Default", cv2.CAP_ANY),
        ("DSHOW", cv2.CAP_DSHOW),
        ("MSMF", cv2.CAP_MSMF)
    ]
    
    for backend_name, backend_api in backends:
        print(f"\n--- Testing Backend: {backend_name} ---")
        for index in [0, 1, 2]:
            cap = cv2.VideoCapture(index, backend_api)
            opened = cap.isOpened()
            print(f"Index {index}: Opened={opened}")
            if opened:
                ret, frame = cap.read()
                print(f"  Read Frame Success: {ret}")
                if ret and frame is not None:
                    print(f"  Frame Shape: {frame.shape}")
                cap.release()

if __name__ == "__main__":
    test_cameras()
