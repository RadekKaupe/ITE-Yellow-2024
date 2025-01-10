import os
from time import sleep
from contextlib import redirect_stdout

script = os.path.join(os.path.dirname(__file__), "subscriber_vm.py")
path = os.path.join(os.path.dirname(__file__), 'log_subscriber.txt')
while(True):
    with open(path, 'a') as file:
        with redirect_stdout(file):
            try:
                exec(open(script).read())
            except:
                print("subscriber crashed")
                sleep(10)