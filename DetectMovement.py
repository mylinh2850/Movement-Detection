from gpiozero import MotionSensor, LED
from picamzero import Camera
import yagmail
from signal import pause
import time
import os

def take_photo(camera, folder_path):
    file_name = folder_path + "/img_" + str(time.time()) + ".jpg"
    camera.take_photo(file_name)
    return file_name

def update_photo_log_file(log_file_name, photo_file_name):
    with open(log_file_name, "a") as f:
        f.write(photo_file_name)
        f.write("\n")
        
def send_photo_by_email(yagmail_client, file_name):
    yagmail_client.send(to="mylinh2850@gmail.com",
                        subject="New photo from Raspberry Pi",
                        contents="Check out the new photo",
                        attachments=file_name)

# Global variables
time_motion_started = time.time()
last_time_photo_taken = 0
MOVEMENT_DETECTED_TRESHOLD = 5.0
MIN_DURATION_BETWEEN_PHOTOS = 30.0
CAMERA_FOLDER_PATH = "/home/mylinh/Desktop/raspberry_programming/project/photos"
LOG_FILE_NAME = CAMERA_FOLDER_PATH + "/photo_logs.txt"

# Setup email
password = ""
with open("/home/mylinh/.local/share/.email_password", "r") as f:
    password = f.read().rstrip()

yag = yagmail.SMTP("mylinh285002@gmail.com", password)
print("Email setup OK")

# Setup Camera
camera = Camera()
camera.still_size = (1536, 864)
camera.flip_camera(vflip=True, hflip=True)
time.sleep(2)
if not os.path.exists(CAMERA_FOLDER_PATH):
    os.mkdir(CAMERA_FOLDER_PATH)
print("Camera setup OK")

# Remove log file
if os.path.exists(LOG_FILE_NAME):
    os.remove(LOG_FILE_NAME)
    print("Previous log file removed")

# Setup GPIOs
pir = MotionSensor(4)
led = LED(17)
print("GPIOs setup OK")

def motion_detected():
    # print("Starting timer")
    global time_motion_started
    time_motion_started = time.time()
    led.on()
    
def motion_finished():
    global last_time_photo_taken
    led.off()
    motion_duration = time.time() - time_motion_started
    # print(motion_duration)
    if motion_duration > MOVEMENT_DETECTED_TRESHOLD:
        if time.time() - last_time_photo_taken > MIN_DURATION_BETWEEN_PHOTOS:
            last_time_photo_taken = time.time()
            print("Taking a photo and sending it by email")
            photo_file_name = take_photo(camera, CAMERA_FOLDER_PATH)
            update_photo_log_file(LOG_FILE_NAME, photo_file_name)
            send_photo_by_email(yag, photo_file_name)
            

pir.when_motion = motion_detected
pir.when_no_motion = motion_finished
print("Everything has been setup.")
pause()