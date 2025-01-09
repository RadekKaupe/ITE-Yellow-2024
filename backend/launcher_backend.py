import os
import time

script = os.path.join(os.path.dirname(__file__), "backend.py")
while(True):
    try:
        exec(open(script).read())
    except:
        print("backend crashed")
        time.sleep(10)
        