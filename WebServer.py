from flask import Flask
import os

CAMERA_FOLDER_PATH = "/home/mylinh/Desktop/raspberry_programming/project/photos"
LOG_FILE_NAME = CAMERA_FOLDER_PATH + "/photo_logs.txt"
previous_line_counter = 0

app = Flask(__name__, static_url_path=CAMERA_FOLDER_PATH, static_folder=CAMERA_FOLDER_PATH)

@app.route("/")
def index():
    return "Hello"

@app.route("/check-photos")
def check_photos():
    global previous_line_counter
    line_counter = 0
    if os.path.exists(LOG_FILE_NAME):
        last_photo_file_name = ""
        with open(LOG_FILE_NAME, "r") as f:
            for line in f:
                line_counter += 1
                last_photo_file_name = line.rstrip()
        difference = line_counter - previous_line_counter
        previous_line_counter = line_counter
        message = str(difference) + " new photos since you last checked <br/>"
        message += "Last photo: " + last_photo_file_name + "<br/>"
        message += "<img src=\"" + last_photo_file_name + "\">"
        return message
    else:
        return "No photo available"

app.run(host="0.0.0.0")