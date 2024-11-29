import os
from dotenv import load_dotenv
from requests import get, post, HTTPError
from json import dumps, dumps, JSONDecodeError
from pprint import pp
import pytz
from datetime import datetime, timezone
import time
import asyncio


load_dotenv()
URL_BASE = os.getenv("AIMTEC_URL")
EP_LOGIN = f"{URL_BASE}/login"
EP_SENSORS = f"{URL_BASE}/sensors"
EP_MEASUREMENTS = f"{URL_BASE}/measurements"
EP_ALERTS = f"{URL_BASE}/alerts"
teamUUID = os.getenv("TEAM_UUID")
HEADERS = {
    "Content-Type": "application/json",
    "teamUUID": teamUUID
}

LOCAL_TIMEZONE = pytz.timezone("Europe/Prague")
STATUS = "TEST"

def convert_to_local_time(utc_timestamp: str):
    try:
        # Attempt to parse with fractional seconds
        utc_time = datetime.strptime(utc_timestamp, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        try:
            # Attempt to parse without fractional seconds
            utc_time = datetime.strptime(utc_timestamp, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            # If neither format matches, raise an error
            raise ValueError(f"Invalid timestamp format: '{utc_timestamp}'")

    # Set timezone to UTC and convert to local timezone
    utc_time = utc_time.replace(tzinfo=pytz.UTC)
    return utc_time.astimezone(LOCAL_TIMEZONE)


def post_(ep, body):
    try:
        response = post(ep, dumps(body), headers=HEADERS)
        if response.status_code == 200:
            try:
                return response.json()
            except JSONDecodeError:
                print(
                    "ERROR: THIS FILE IS NOT IN A JSON FORMAT! ABORT MISSION! I REPEAT: ABORT MISSION!")
                return {}
        else:
            print(f"ERROR: THE STATUS CODE IS: {response.status_code}")
            return {}
    except HTTPError as http_err:
        print(
            f"ERROR: A HTTP ERROR OCURRED, THIS IS WHAT IS GOING ON:{http_err} ")


def get_(ep):
    try:
        response = get(ep, headers=HEADERS)
        if response.status_code == 200:
            try:
                return response.json()
            except JSONDecodeError:
                print(
                    "ERROR: THIS FILE IS NOT IN A JSON FORMAT! ABORT MISSION! I REPEAT: ABORT MISSION!")
                return {}
        else:
            print(f"ERROR: THE STATUS CODE IS: {response.status_code}")
            return {}
    except HTTPError as http_err:
        print(
            f"ERROR: A HTTP ERROR OCURRED, THIS IS WHAT IS GOING ON:{http_err} ")


payload_login = {
    # "username": "Orange",
    # "password": "ybeeoQrSsc2eY2M1xdXM"
    "username": "Yellow",
    "password": "tmSwNIYM4p19MYk4iTr8",
}


def post_measurement_payload(payload, aimtec_sensor):
    utc_timestamp = payload.get("timestamp")
    local_timestamp = convert_to_local_time(utc_timestamp)
    local_timestamp_str = local_timestamp.strftime(
        "%Y-%m-%dT%H:%M:%S.") + f"{local_timestamp.microsecond // 1000:03d}" + local_timestamp.strftime("%z")
    local_timestamp_str = local_timestamp_str[:-
                                              2] + ":" + local_timestamp_str[-2:]
    sensorUUID = aimtec_sensor["sensorUUID"]
    value_key = aimtec_sensor["type"]  # Toto nefuguje, protoze Aimtec
    print(f"\nReal information: {value_key}")
    value = payload[value_key]

    value_key = "temperature"
    measurement_payload = {
        "createdOn": local_timestamp_str,
        "sensorUUID": sensorUUID,
        value_key: value,
        "status": STATUS
    }
    print(f"Measurement payload: {measurement_payload}")
    json = post_(EP_MEASUREMENTS, measurement_payload)
    msg = try_to_get_msg_from_json(json)
    if msg is not None:
        print(f"The message we recieved from AIMTEC is: {msg}")


def post_measurement_all(payload, aimtec_sensors):
    for aimtec_sensor in aimtec_sensors:
        post_measurement_payload(payload, aimtec_sensor)


def post_alert(payload, aimtec_sensor):
    utc_timestamp = payload.get("timestamp")
    local_timestamp = convert_to_local_time(utc_timestamp)
    local_timestamp_str = local_timestamp.strftime(
        "%Y-%m-%dT%H:%M:%S.") + f"{local_timestamp.microsecond // 1000:03d}" + local_timestamp.strftime("%z")
    local_timestamp_str = local_timestamp_str[:-
                                              2] + ":" + local_timestamp_str[-2:]
    sensorUUID = aimtec_sensor["sensorUUID"]
    value_key = aimtec_sensor["type"]  # Toto nefunguje, protoze Aimtec
    print(f"\nReal information: {value_key}")
    value = payload[value_key]

    value_key = "temperature"
    capitalized_value_key = value_key[0].upper() + value_key[1:]
    lower_limit_key = "low" + capitalized_value_key
    upper_limit_key = "high" + capitalized_value_key
    lower_limit_value, upper_limit_value = fetch_lower_and_upper_limit(
        aimtec_sensor)

    alert_payload = {
        "createdOn": local_timestamp_str,
        "sensorUUID": sensorUUID,
        value_key: value,
        lower_limit_key: lower_limit_value,
        upper_limit_key: upper_limit_value
    }
    print(f"Alert payload: {alert_payload}")
    json = post_(EP_ALERTS, alert_payload)
    msg = try_to_get_msg_from_json(json)
    if msg is not None:
        print(f"The message we recieved from AIMTEC is: {msg}")


def try_to_get_msg_from_json(json: dict):
    if json is None:
        print("No json was returned. An error probably happened somewhere earlier.")
        return None
    if len(json) == 0:
        print("A empty json was returned. An error probably happened somewhere earlier.")
        return None
    try:
        msg = json["message"]
        return msg
    except Exception as e:
        print(
            f"A error occured when trying to get the message from a json: {e}")
        return None

def check_if_value_in_range(sensor_data: dict, aimtec_sensor_dict: dict):
    type_ = aimtec_sensor_dict["type"]
    value = sensor_data[type_]
    lower_limit, upper_limit = fetch_lower_and_upper_limit(aimtec_sensor_dict)
    # print(type_)
    # print(f"Value: {value}")
    # print(f"Lower limit: {lower_limit}")
    # print(f"Upper limit: {upper_limit}")
    return value >= lower_limit and value <= upper_limit


def fetch_lower_and_upper_limit(aimtec_sensor_dict):
    for key, _ in aimtec_sensor_dict.items():
        if key.startswith("min"):
            lower_limit = aimtec_sensor_dict[key]
        if key.startswith("max"):
            upper_limit = aimtec_sensor_dict[key]
    return lower_limit, upper_limit


async def get_aimtec_sensor_dicts():
    response = get_(EP_SENSORS)
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
    return temperature, humidity, illumination


async def post_loop(ep, body):
    resp_code = -1
    try:
        print("Trying to login.")
        response = post(ep, dumps(body), headers=HEADERS)
        resp_code = response.status_code

        while resp_code != 200:
            print("Post not executed succesfully. See next message for error.")
            print(
                f"ERROR: THE STATUS CODE IS: {response.status_code}. Retrying in 10 seconds.")
            time.sleep(10)
        print("Post succeeded. Extracting JSON.")
        try:
            return response.json()
        except JSONDecodeError:
            print(
                "ERROR: THIS FILE IS NOT IN A JSON FORMAT! ABORT MISSION! I REPEAT: ABORT MISSION!")
            return {}

    except HTTPError as http_err:
        print(
            f"ERROR: A HTTP ERROR OCURRED, THIS IS WHAT IS GOING ON:{http_err} ")
        return {}


async def login_loop():
    try:
        json_file = await post_loop(EP_LOGIN, payload_login)
        print(f"Login loop finished succesfully.")
        return json_file
    except Exception as e:
        print(f"Login Failed, error code: {e}")
        return None

if __name__ == "__main__":

    # json_file = post_(EP_LOGIN, payload_login)
    # pp(f"json file: {json_file} \n")

    json_file = asyncio.run(post_loop(EP_LOGIN, payload_login))
    pp(f"json file: {json_file} \n")

    # read the sensors
    # response = get_(EP_SENSORS)
    # # pp(response) # pretty-print the response to see what we got
    # # save the first sensor UUID for later
    # SENSOR_UUID = response[0]['sensorUUID']
    # pp(f"SENSOR_UUID: {SENSOR_UUID} \n")

    # sensor_uuid_list = [json['sensorUUID'] for json in response]
    # print(sensor_uuid_list)
    # temperature = {"type": "temperature"}
    # humidity = {"type": "humidity"}
    # illumination = {"type": "illumination"}

    # for dict_ in response:
    #     if dict_['name'].endswith("temperature"):
    #         temperature.update(dict_)

    #     elif dict_['name'].endswith("humidity"):
    #         humidity.update(dict_)

    #     elif dict_['name'].endswith("illumination"):
    #         illumination.update(dict_)

    # pp(temperature)
    # pp(humidity)
    # pp(illumination)

    # response = get_(EP_ALERTS)
    # pp(response)
    # t = check_if_value_in_range(test_sensor_data, temperature)
    # print(t)
