import os
from time import sleep
from contextlib import redirect_stdout
from traceback import print_exc

script = os.path.join(os.path.dirname(__file__), "subscriber_vm.py")
path = os.path.join(os.path.dirname(__file__), 'log_subscriber.txt')

with open(path, 'a') as file:
        with redirect_stdout(file):
            print("launcher_subscriber.py started =================================================")
            while(True):
                try:
                    exec(open(script).read())
                except:
                    print_exc()
                    sleep(10)