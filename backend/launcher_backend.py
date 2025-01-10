import os
from time import sleep
from contextlib import redirect_stdout

script = os.path.join(os.path.dirname(__file__), "backend.py")
path = os.path.join(os.path.dirname(__file__), 'log_backend.txt')
while(True):
    with open(path, 'a') as file:
        with redirect_stdout(file):
            try:
                exec(open(script).read())
            except:
                print("backend crashed")
                sleep(10)
        