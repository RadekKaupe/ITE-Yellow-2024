import os
from dotenv import load_dotenv
from requests import get, post, HTTPError
from json import dumps, dumps, JSONDecodeError
from pprint import pp

load_dotenv()
URL_BASE = os.getenv("AIMTEC_URL")
EP_LOGIN = f"{URL_BASE}/login"
EP_SENSORS = f"{URL_BASE}/sensors"
EP_MEASUREMENTS = f"{URL_BASE}/measurements"
EP_ALERTS = f"{URL_BASE}/alerts"
teamUUID = os.getenv("TEAM_UUID")
HEADERS ={      
    "Content-Type": "application/json",
    "teamUUID" : teamUUID
    }



def post_(ep, body):
    try:
        response = post(ep, dumps(body), headers=HEADERS)
        if response.status_code == 200:
            try:
                return response.json()
            except JSONDecodeError:
                print("ERROR: THIS FILE IS NOT IN A JSON FORMAT! ABORT MISSION! I REPEAT: ABORT MISSION!")
                return {}
        else:
            print(f"ERROR: THE STATUS CODE IS: {response.status_code}")
            return {}
    except HTTPError as http_err:
        print(f"ERROR: A HTTP ERROR OCURRED, THIS IS WHAT IS GOING ON:{http_err} ") 



def get_(ep):
    try:
        response = get(ep, headers=HEADERS)
        if response.status_code == 200:
            try:
                return response.json()
            except JSONDecodeError:
                print("ERROR: THIS FILE IS NOT IN A JSON FORMAT! ABORT MISSION! I REPEAT: ABORT MISSION!")
                return {}
        else:
            print(f"ERROR: THE STATUS CODE IS: {response.status_code}")
            return {}
    except HTTPError as http_err:
            print(f"ERROR: A HTTP ERROR OCURRED, THIS IS WHAT IS GOING ON:{http_err} ") 

        
payload_login = {
    # "username": "Orange",
    # "password": "ybeeoQrSsc2eY2M1xdXM"
    "username": "Yellow",
    "password": "tmSwNIYM4p19MYk4iTr8",
}

json_file = post_(EP_LOGIN, payload_login)
pp(f"json file: {json_file} \n" )


# read the sensors
response = get_(EP_SENSORS)
# pp(response) # pretty-print the response to see what we got
SENSOR_UUID = response[0]['sensorUUID'] # save the first sensor UUID for later
pp(f"SENSOR_UUID: {SENSOR_UUID} \n")

sensor_uuid_list = [json['sensorUUID'] for json in response]
print(sensor_uuid_list)
temperature = {"type": "temperature"}
humidity = {"type": "humidity"}
illumination = {"type": "illumination"}

for dict_ in response:
    if dict_['name'].endswith("temperature"):
        temperature.update(dict_)
    
    elif dict_['name'].endswith("humidity"):
        humidity.update(dict_)
    
    elif dict_['name'].endswith("illumination"):
        illumination.update(dict_)
    
pp(temperature)
pp(humidity)
pp(illumination)

##
## Momentalne si to delam slozitejsi a pocitam s tim, 
## ze muze byt vice senzoru jednoho typu
## To mi ale bude komplikovat ukladani do db, protoze si nemuzu ukladat jednodusse True/Null
##
##
print()

# # create a new measurement    
# measurement_payload = {
#     "createdOn": "2023-09-20T13:00:00.000+01:00",
#     "sensorUUID": SENSOR_UUID,
#     "temperature": "92.1",
#     "status": "TEST"
# }
# json_file = post_(EP_MEASUREMENTS, measurement_payload)
# pp(json_file)


response = get_(EP_ALERTS)
pp(response)



alert_payload = {
		"createdOn": None,
		"sensorUUID": None,
		"temperature": None,
        "lowTemperature": None,
        "highTemperature": None
	}


test_sensor_data = {"team_name": "orange", "timestamp": "2024-11-27T11:25:25.508795", "temperature": 25.77, "humidity": 55.27, "illumination": 754.88}

# {"team_name": "pink", "timestamp": "2024-11-27T11:25:25.508795", "temperature": 21.77, "humidity": 55.27, "illumination": 754.88}
# {"team_name": "green", "timestamp": "2024-11-27T11:25:26.509872", "temperature": 18.17, "humidity": 35.21, "illumination": 441.03}
# {"team_name": "pink", "timestamp": "2024-11-27T11:25:27.510298", "temperature": 23.02, "humidity": 67.59, "illumination": 403.88}

def check_if_value_in_range(sensor_data:dict, aimtec_sensor_dict:dict):
    type_ = aimtec_sensor_dict["type"]
    value = sensor_data[type_]
    for key, _ in aimtec_sensor_dict.items():
        if key.startswith("min"):
            lower_limit = aimtec_sensor_dict[key]
        if key.startswith("max"):
            upper_limit = aimtec_sensor_dict[key]
    print(type_)
    print(f"Value: {value}")
    print(f"Lower limit: {lower_limit}")
    print(f"Upper limit: {upper_limit}")
    return value >= lower_limit and value <= upper_limit
    

t = check_if_value_in_range(test_sensor_data, temperature)
print(t)