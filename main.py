from multiprocessing import Process
import subprocess

def run_detect_movement():
    subprocess.run(["python3", "DetectMovement.py"])

def run_web_server():
    subprocess.run(["python3", "WebServer.py"])

if __name__ == "__main__":
    p1 = Process(target=run_detect_movement)
    p2 = Process(target=run_web_server)

    p1.start()
    p2.start()

    p1.join()
    p2.join()
