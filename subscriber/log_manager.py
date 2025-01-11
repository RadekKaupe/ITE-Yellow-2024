import os
import re
import time

NUM_LOGS = 48
PERIOD = 3600 # sec
ORIGINAL = "log_subscriber.txt"

scriptDir = os.path.dirname(__file__)
print(scriptDir)
directory = os.path.join(scriptDir, "logs")
print(directory)

def isLog(file):
    return(re.search("log[0-9][0-9][0-9].txt$", file) != None)

tmp = filter(isLog, os.listdir(directory)) # in some weird data type
files = list()

for file in tmp: 
    files.append(os.path.join(directory, str(file)))

files = sorted(files, key=os.path.getmtime) # sort by time updated (recent last)

#print("oldest: " + files[0])
i = int(re.search("[0-9][0-9][0-9]",files[0]).group())
#print(i)

while(True):
    
    i = i%NUM_LOGS
    copied = False
    if(not copied):
        try:
            print("copying to log{:03d}.txt".format(i))
            with open(os.path.join(scriptDir, ORIGINAL), "r") as original:
                with open(os.path.join(directory, "log{:03d}.txt".format(i)), "w") as log:
                    log.write("copied on: " + (time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))  + '\n')
                    for line in original:
                        log.write(line)
            copied = True
        except:
            print("copying failed")
            time.sleep(5)
            continue
    
    if(copied):
        try:
            print("erasing original")
            open(os.path.join(scriptDir, ORIGINAL), "w").close()
        except:
            print("erasure failed")
            continue
        
    time.sleep(PERIOD)    
    i+=1