import os
from time import sleep
from contextlib import redirect_stdout
from traceback import print_exc

script = os.path.join(os.path.dirname(__file__), "backend.py")
path = os.path.join(os.path.dirname(__file__), 'log_backend.txt')

with open(path, 'a') as file:
        with redirect_stdout(file):
            print("launcher_backend.py started =================================================")
            while(True):
                try:
                    exec(open(script).read())
                except:
                    print_exc(file=file)
                    sleep(10)
        