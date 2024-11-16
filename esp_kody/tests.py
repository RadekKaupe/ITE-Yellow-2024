import json
a = float(11)
b = round(a,1)
c = {'num': b}
print(json.dumps(c))