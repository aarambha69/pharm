try:
    import cv2
    print("OpenCV imported successfully")
except Exception as e:
    print(f"OpenCV import failed: {e}")

try:
    from pyzbar import pyzbar
    print("pyzbar imported successfully")
except Exception as e:
    print(f"pyzbar import failed: {e}")
