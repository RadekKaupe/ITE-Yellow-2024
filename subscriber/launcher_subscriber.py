import os

script = os.path.join(os.path.dirname(__file__), "subscriber_vm.py")
while(True):
    try:
        exec(open(script).read())
    except:
        print("subscriber crashed")