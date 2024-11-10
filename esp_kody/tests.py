global i
i = 1

def ab():
    global i
    i = i + 1

def aa():
    print(i)
    
    
ab()
aa()

for i in range(0,0):
    print(i)