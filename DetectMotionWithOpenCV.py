from gpiozero import LED, Buzzer
from picamera2 import Picamera2
import cv2
import time
import os
import yagmail
from ultralytics import YOLO

# === CẤU HÌNH ===
led = LED(17)
buzzer = Buzzer(27)

VIDEO_FOLDER_PATH = "/home/mylinh/Desktop/raspberry_programming/Movement-Detection/videos"
LOG_FILE_NAME = os.path.join(VIDEO_FOLDER_PATH, "video_logs.txt")
VIDEO_FPS = 10
NO_MOTION_TIMEOUT = 5  # giây: dừng quay nếu không còn phát hiện người
FRAME_DELAY = 1 / VIDEO_FPS

# Tạo thư mục nếu chưa tồn tại
if not os.path.exists(VIDEO_FOLDER_PATH):
    os.makedirs(VIDEO_FOLDER_PATH)

# Thiết lập email
with open("/home/mylinh/.local/share/.email_password", "r") as f:
    password = f.read().strip()
yag = yagmail.SMTP("mylinh285002@gmail.com", password)

# Khởi tạo camera
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)})
picam2.configure(config)
picam2.start()
time.sleep(2)

# Khởi tạo YOLO
model = YOLO('yolov8n.pt')  # mô hình nhẹ nhất

# === HÀM XỬ LÝ ===
def is_human_present_yolo(frame):
    results = model(frame, verbose=False)[0]
    for box in results.boxes:
        class_id = int(box.cls[0])
        if model.names[class_id] == "person":
            return True
    return False

def create_video_writer(file_path, frame, fps=30):
    height, width = frame.shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    return cv2.VideoWriter(file_path, fourcc, fps, (width, height))

def update_video_log(log_file, video_file):
    with open(log_file, "a") as f:
        f.write(video_file + "\n")

# === BIẾN QUẢN LÝ QUAY VIDEO ===
recording = False
video_writer = None
last_motion_time = 0
video_file_path = ""

# === VÒNG LẶP CHÍNH ===
frame1 = picam2.capture_array()
frame2 = picam2.capture_array()

print("🎥 Hệ thống sẵn sàng phát hiện chuyển động có người và quay video...")

frame_count = 0
yolo_check_interval = 5  # chỉ chạy YOLO mỗi 5 frame
human_present = False  # kết quả YOLO gần nhất

while True:
    diff = cv2.absdiff(frame1, frame2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
    dilated = cv2.dilate(thresh, None, iterations=3)
    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    movement_detected = any(cv2.contourArea(contour) > 1000 for contour in contours)
    frame_time = time.time()
    
    

    frame_count += 1
    if frame_count % yolo_check_interval == 0:
        human_present = is_human_present_yolo(frame1)




    if movement_detected and human_present:
        led.on()
        last_motion_time = frame_time

        if not recording:
            video_file_path = os.path.join(VIDEO_FOLDER_PATH, f"video_{int(frame_time)}.mp4")
            video_writer = create_video_writer(video_file_path, frame1)
            recording = True
            print(f"▶️ Bắt đầu quay video: {video_file_path}")

        if recording:
            video_writer.write(frame1)

    else:
        led.off()
        if recording:
            # Nếu đã quá timeout không phát hiện chuyển động người → dừng quay
            if frame_time - last_motion_time > NO_MOTION_TIMEOUT:
                print(f"⏹️ Dừng quay. Lưu video: {video_file_path}")
                video_writer.release()
                update_video_log(LOG_FILE_NAME, video_file_path)
                recording = False
                video_writer = None

    frame1 = frame2
    frame2 = picam2.capture_array()
    
    elapsed_time = time.time() - frame_time
    sleep_time = FRAME_DELAY - elapsed_time
    if sleep_time > 0:
        time.sleep(sleep_time)

    print(f"⏱️ Frame time: {elapsed_time:.3f}s → approx. {1/elapsed_time:.1f} FPS")
