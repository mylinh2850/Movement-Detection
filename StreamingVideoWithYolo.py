from flask import Flask, Response
from gpiozero import LED, Buzzer
from picamera2 import Picamera2
from ultralytics import YOLO
import cv2
import time
import threading

# === CẤU HÌNH ===
led = LED(17)
buzzer = Buzzer(27)

FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FRAME_INTERVAL = 0.1  # khoảng 10 FPS
YOLO_INTERVAL = 5  # chỉ chạy YOLO mỗi 5 frame

# Khởi tạo camera
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"format": "RGB888", "size": (FRAME_WIDTH, FRAME_HEIGHT)})
picam2.configure(config)
picam2.start()
time.sleep(2)

# Khởi tạo YOLO
model = YOLO('yolov8n.pt')

# === FLASK STREAMING ===
app = Flask(__name__)
frame_lock = threading.Lock()
output_frame = None

def capture_frames():
    global output_frame
    frame_count = 0
    last_detection = time.time()
    prev_time = time.time()
    fps = 0.0

    while True:
        start_time = time.time()

        frame = picam2.capture_array()
        draw_frame = frame.copy()

        # Chạy YOLO mỗi vài frame
        if frame_count % YOLO_INTERVAL == 0:
            results = model(frame, verbose=False)[0]
            for box in results.boxes:
                class_id = int(box.cls[0])
                conf = float(box.conf[0])
                if model.names[class_id] == "person":
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(draw_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(draw_frame, f"person {conf:.2f}", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    last_detection = time.time()

        if time.time() - last_detection > 10:
            draw_frame = frame.copy()

        # === Tính FPS thực tế ===
        curr_time = time.time()
        fps = 1.0 / (curr_time - prev_time)
        prev_time = curr_time

        # === Hiển thị FPS lên khung hình ===
        cv2.putText(draw_frame, f"FPS: {fps:.2f}", (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        with frame_lock:
            output_frame = draw_frame

        frame_count += 1
        time.sleep(FRAME_INTERVAL)


def generate_stream():
    global output_frame
    while True:
        with frame_lock:
            if output_frame is None:
                continue
            ret, jpeg = cv2.imencode('.jpg', output_frame)
            if not ret:
                continue
            frame_bytes = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return '<h1>Live Stream with YOLO</h1><img src="/video_feed">'

@app.route('/video_feed')
def video_feed():
    return Response(generate_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    t = threading.Thread(target=capture_frames)
    t.daemon = True
    t.start()
    app.run(host="0.0.0.0", port=5000, debug=False)
