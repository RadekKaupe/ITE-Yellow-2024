global i
i = 1

def ab():
    global i
    i = i + 1

def aa():
    print(i)
    
ab()
aa()