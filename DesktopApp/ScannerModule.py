import cv2
import threading
import time
import customtkinter as ctk
from PIL import Image
import os

class ScannerModule:
    def __init__(self, parent_dialog, on_scan_callback):
        self.parent = parent_dialog
        self.callback = on_scan_callback
        self.cap = None
        self.is_running = False
        self.scan_thread = None
        self.flashlight_on = False
        self.camera_index = 0
        
        # Initialize OpenCV Detectors
        self.qr_detector = cv2.QRCodeDetector()
        try:
            # BarcodeDetector might need sr.prototxt/sr.caffemodel for super-resolution, 
            # but we'll try the basic detector first.
            self.barcode_detector = cv2.barcode.BarcodeDetector()
        except:
            self.barcode_detector = None
        
        self.preview_label = None
        
    def start_scan(self, preview_label):
        if self.is_running:
            return True, "Already running"
            
        self.preview_label = preview_label
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            return False, "Could not open camera"
            
        self.is_running = True
        self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self.scan_thread.start()
        return True, "Success"
        
    def stop_scan(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.preview_label = None

    def toggle_flashlight(self):
        self.flashlight_on = not self.flashlight_on
        # Most webcams don't support this via OpenCV, but we can set properties
        if self.cap:
             self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
        
    def switch_camera(self):
        # Released and restarted by the UI to ensure clean switch
        self.stop_scan()
        self.camera_index = 1 if self.camera_index == 0 else 0
        
    def _scan_loop(self):
        last_scan_time = 0
        while self.is_running:
            if not self.cap: break
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                continue
                
            code_data = None
            
            # 1. Try QR Detection
            ok, decoded_info, points, _ = self.qr_detector.detectAndDecodeMulti(frame)
            if ok:
                for info in decoded_info:
                    if info:
                        code_data = info
                        break
            
            # 2. Try Barcode Detection if QR failed
            if not code_data and self.barcode_detector:
                try:
                    ok, decoded_info, decoded_type, points = self.barcode_detector.detectAndDecode(frame)
                    if ok:
                        for info in decoded_info:
                            if info:
                                code_data = info
                                break
                except:
                    pass

            if code_data and time.time() - last_scan_time > 1.5:
                last_scan_time = time.time()
                self.parent.after(0, lambda d=code_data: self.callback(d))
            
            # Update Preview UI
            if self.preview_label and self.is_running:
                try:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(rgb_frame)
                    
                    # Target height 300, calculate width
                    h_target = 300
                    w, h = pil_img.size
                    w_target = int(w * (h_target / h))
                    
                    ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(w_target, h_target))
                    self.parent.after(0, lambda img=ctk_img: self.preview_label.configure(image=img) if self.preview_label else None)
                except:
                    pass
                
            time.sleep(0.03)
        
        if self.cap:
            self.cap.release()
            self.cap = None
