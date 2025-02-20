
import asyncio
import subprocess
from urllib.parse import urlencode
from urllib.request import urlopen
import tornado
from tornado.web import RequestHandler 
from os.path import join as join_path
from json import  loads as loads_json
from time import sleep
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
import sys
from datetime import datetime,  timedelta, timezone
import pytz
import jwt
import bcrypt
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.log
from urllib.request import urlopen
import datetime as dt
import logging
import numpy as np
import imutils
import pickle
import cv2
import json

import urllib
# Import of db.py for classes, which are the columns in the database tables
db_foler_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'db'))

sys.path.insert(0, db_foler_path)
from db import User

# Connecting to the database
load_dotenv()
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST", "localhost")
db_name = os.getenv("DB_NAME")
connection_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}"
print(f"Connection string: {connection_string} \n")
engine = create_engine(
    f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}")
LOCAL_TIMEZONE = pytz.timezone("Europe/Prague")

SessionLocal = sessionmaker(bind=engine)

from websocket_handler import WSHandler

def get_script_directory():
    script_path = os.path.abspath(__file__)
    script_directory = os.path.dirname(script_path)
    return script_directory


def create_folder(path): 
    try: 
        os.makedirs(path, exist_ok=True)
        print(f"Folder '{path}' created successfully.")
    except Exception as e:
        print(f"Error creating folder: {e}")


BACKEND_PATH = get_script_directory()
print(f"Backend location: {BACKEND_PATH}")
FACE_ID_PATH = os.path.join(BACKEND_PATH, 'faceid')
dataset_path = os.path.join(FACE_ID_PATH, 'dataset')
RECOG_IMAGES_PATH = os.path.join(BACKEND_PATH,'recog_images')
output_path = os.path.join(FACE_ID_PATH, 'output') 
create_folder(dataset_path)
create_folder(RECOG_IMAGES_PATH)
create_folder(output_path)



EPSILON = 1e-9
class BaseHandler(RequestHandler):
    def get_current_user(self):
        auth_token = self.get_secure_cookie("auth_token")
        print(f"Auth token: {auth_token}")
        if not auth_token:
            return None
        try:
            # Decode the JWT token and verify it
            payload = jwt.decode(auth_token, self.settings["secret_key"], algorithms=["HS256"])
            print(f"payload: {payload}")
            payload_exp = payload["exp"]
            # print(f"Current timestamp: {datetime.now(timezone.utc)}")
            if  payload_exp< datetime.now().timestamp(): 
                self.redirect_with_error("Your session has expired. Please login again.")
                # print(f"Payload expiration: {payload_exp  }")
                return
            return payload.get("user_id")
        except jwt.ExpiredSignatureError:
            self.clear_cookie("auth_token") 
            self.redirect_with_error("Your session has expired. Please login again.")
            return 
        except jwt.InvalidTokenError:
            self.clear_cookie("auth_token") 
            self.redirect_with_error("Invalid Token")
            return


    def redirect_with_error(self, error_message):
        logout_message = json.dumps({"error": error_message})
        logout_message_encoded = urllib.parse.quote(logout_message)
        self.set_cookie("logout_message",logout_message_encoded)
        self.redirect(f"/login")

class AuthHandler(RequestHandler):
    def check_if_logged_in(self):
        auth_token = self.get_secure_cookie("auth_token")
        if auth_token: 
            try: 
                jwt.decode(auth_token, self.settings["secret_key"], algorithms=["HS256"]) 
                self.redirect("/dashboard")
                return True
            except jwt.ExpiredSignatureError:
                 self.clear_cookie("auth_token") 
                 self.write({"error": "Session expired. Please login again."}) 
                 return False
            except jwt.InvalidTokenError:
                self.clear_cookie("auth_token")
                self.write({"error": "Invalid Token"}) 
                return False
        else:
            return False
class LoginHandler(AuthHandler):
    async def post(self):
        username = self.get_argument("username")
        password = self.get_argument("password")
        # print(username)
        # print(password)
        # Get user from database
        
        session = SessionLocal()

        user = session.execute(
            select(User).where(User.username == username)
            ).scalar_one_or_none()
        if not user:
            self.write({"error": "Invalid credentials"})
            return
        # print(user.approved)
        # Verify password
        if bcrypt.checkpw(password.encode(), user.password_hash):
            if(not user.approved):
                self.write({"error": "User has not been yet approved. Please contact the admin of the page."})
                return
            # Create session
            token = jwt.encode(
                {"user_id": user.id, "exp": datetime.now(timezone.utc) + timedelta(hours=1) },# Authentication expires in 1 hour
                self.settings["secret_key"]
            )

            # token = jwt.encode(
            #     {"user_id": user.id, "exp": datetime.now(timezone.utc) + timedelta(milliseconds=10000) },# Authentication expires in 10 seconds - for testing
            #     self.settings["secret_key"]
            # )
            # print(token)
            self.set_secure_cookie("auth_token", token)
            self.set_status(200)
            # self.redirect("/dashboard")
            self.write({"redirect": "/dashboard"}) 
        else:
            self.set_status(401)
            self.write({"error": "Invalid credentials"})
    def get(self):
        if(not self.check_if_logged_in()):
            self.render("static/auth/login.html")


class RegisterHandler(AuthHandler):
    async def post(self):
        # Get the username and password from the request
        username = self.get_argument("username")
        password = self.get_argument("password")
        
        # Hash the password securely
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        # Create a new User instance
        new_user = User(username=username, password_hash=password_hash)
        
        # Create a session
        session = SessionLocal()
        
        try:
            # Add the user to the session
            session.add(new_user)
            
            # Commit the session
            session.commit()
            
            # Respond with success
            self.write({"success": "User Registered. Please wait for the approval of the admin."})
        
        except Exception as e:
            # Rollback for other exceptions
            session.rollback()
            if "UniqueViolation" in str(e):
                self.write({"error": "Username is already taken. Please choose another one."})
            else:
                self.write({"error": "An unknown error occurred. Please try again."})
            # self.write({"error": f"An error occurred: {str(e)}"})
        
        finally:
            # Close the session
            session.close()
    def get(self):
        if(not self.check_if_logged_in()):
            self.render("static/auth/register.html")    

class LogoutHandler(RequestHandler):
    def get(self):
        self.clear_cookie("auth_token")
        logout_message = json.dumps({"success": "User Logout"})
        logout_message_encoded = urllib.parse.quote(logout_message)
        self.set_cookie("logout_message",logout_message_encoded)
        self.redirect("/login")
        # params = urlencode({"success": "User logout."}) 
        # self.redirect(f"/login?{params}")

tornado.log.enable_pretty_logging()
app_log = logging.getLogger("tornado.application")


def create_user_dataset_folder(username):
    # Define the base path
    base_path = dataset_path
    # print(base_path)
    # Create the full path including username
    user_path = os.path.join(base_path, username)
    # print(user_path)
    # Check if base directories exist, create them if they don't
    os.makedirs(base_path, exist_ok=True)
    
    # Create user directory if it doesn't exist
    if not os.path.exists(user_path):
        os.makedirs(user_path)
        print(f"Created directory for user: {username}")
        return True
    else:
        print(f"Directory already exists for user: {username}")
        return False

class ReceiveImageHandler(BaseHandler):
    def post(self):
        # Convert from binary data to string
        received_data = self.request.body.decode()

        assert received_data.startswith("data:image/png"), "Only data:image/png URL supported"

        username = self.get_user_from_token()
        create_user_dataset_folder(username=username)
        # Parse data:// URL
        with urlopen(received_data) as response:
            image_data = response.read()


        app_log.info("Received image: %d bytes", len(image_data))
        # Write an image to the file
        path = os.path.join(dataset_path, username)
        filename = f"img-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png" 
        full_path = os.path.join(path, filename)
        try:
            with open(full_path, "wb") as fw:
                fw.write(image_data)
            self.write({"success": f"Picture of user {username} taken."})
        except Exception as e:
            self.write({"error": f"Something went wrong when saving the picture, contact the admin."})
            print(f"Something went wrong when saving the image.")
    @tornado.web.authenticated
    def get(self):
        self.render("static/auth/receive.html")

    def get_user_from_token(self):
        auth_token = self.get_secure_cookie("auth_token")
        payload = jwt.decode(auth_token, self.settings["secret_key"], algorithms=["HS256"])

        user_id = payload["user_id"]
        session = SessionLocal()
        username = session.execute(
            select(User.username).where(User.id == user_id)
        ).scalar_one_or_none()
        return username



class TrainingHandler(RequestHandler):

    async def run_shell_script(self, script_path, *args):
        print(script_path)
        try:
            # Prepare the command with the script path and arguments
            command = ["bash", script_path] + list(args)
            
            # Run the script and capture output
            result = subprocess.run(command, 
                                    capture_output=True,
                                    text=True,
                                    check=True)
            print("Script output:", result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print("Error running script:", e)
            print("Error output:", e.stderr)
            return False
    
    async def get(self):
        train_sh_path = os.path.join(FACE_ID_PATH,'train.sh')
        WSHandler.send_message(self, {"success": "Training started. Wait for page refresh please."})
        if((await self.run_shell_script(train_sh_path, FACE_ID_PATH))== False):
            WSHandler.send_message(self, {"error": "Something went wrong during the training."})
            await asyncio.sleep(5) 
            
        # WSHandler.send_message(self, {"success": "Training finished."})

        self.redirect("/receive_image")


class RecognizeImageHandler(AuthHandler):
    def post(self):
        deploy_path = os.path.join(FACE_ID_PATH, "face_detection_model", "deploy.prototxt") 
        caffe_model_path = os.path.join(FACE_ID_PATH, "face_detection_model", "res10_300x300_ssd_iter_140000.caffemodel") 
        embedder_path = os.path.join(FACE_ID_PATH, "openface_nn4.small2.v1.t7")
        recognizer_path = os.path.join(FACE_ID_PATH, "output", "recognizer.pickle") 
        le_path = os.path.join(FACE_ID_PATH, "output", "le.pickle")

        detector = cv2.dnn.readNetFromCaffe(deploy_path, caffe_model_path)
        embedder = cv2.dnn.readNetFromTorch(embedder_path)
        recognizer = pickle.loads(open(recognizer_path, "rb").read())
        le = pickle.loads(open(le_path, "rb").read())

        received_data = self.request.body.decode()
        assert received_data.startswith("data:image/png"), "Only data:image/png URL supported"

        # Parse data:// URL
        with urlopen(received_data) as response:
            image_data = response.read()
        filename = f"img-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
        fn = os.path.join(RECOG_IMAGES_PATH, filename)
        with open(fn, "wb") as fw:
            fw.write(image_data)

        image = cv2.imread(fn)
        image = imutils.resize(image, width=600)
        (h, w) = image.shape[:2]


        imageBlob = cv2.dnn.blobFromImage(
            cv2.resize(image, (300, 300)), 1.0, (300, 300),
            (104.0, 177.0, 123.0), swapRB=False, crop=False)

        detector.setInput(imageBlob)
        detections = detector.forward()

        faces = []
        proba = None
        # loop over the detections
        for i in range(0, detections.shape[2]):
            # extract the confidence (i.e., probability) associated with the
            # prediction
            confidence = detections[0, 0, i, 2]

            # filter out weak detections
            if confidence > 0.5:
                # compute the (x, y)-coordinates of the bounding box for the
                # face
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")

                # extract the face ROI
                face = image[startY:endY, startX:endX]
                (fH, fW) = face.shape[:2]

                # ensure the face width and height are sufficiently large
                if fW < 20 or fH < 20:
                    continue

                # construct a blob for the face ROI, then pass the blob
                # through our face embedding model to obtain the 128-d
                # quantification of the face
                faceBlob = cv2.dnn.blobFromImage(face, 1.0 / 255, (96, 96),
                    (0, 0, 0), swapRB=True, crop=False)
                embedder.setInput(faceBlob)
                vec = embedder.forward()

                # perform classification to recognize the face
                preds = recognizer.predict_proba(vec)[0]
                j = np.argmax(preds)
                proba = preds[j]
                username = le.classes_[j]

                faces.append({
                    "name": username,
                    "prob": proba,
                    "bbox": {"x1": int(startX), "x2": int(endX), "y1": int(startY), "y2": int(endY)},
                })
                print(faces)
        if(len(faces) >= 2):
            self.write({"error": "Multiple Faces detected."})
            return
        if(proba == None):
            self.write({"error": "No faces were found."})
            return
        if(proba > 0.8 - EPSILON):


            session = SessionLocal()

            user = session.execute(
                select(User).where(User.username == username)
                ).scalar_one_or_none()
            if not user:
                self.write({"error": "Invalid credentials"})
                return
            # print(user.approved)
            # Verify password
            if(not user.approved): # This shouldn't  happen naturally, 
                self.write({"error": "User has not been yet approved. Please contact the admin of the page."})
                return
            # Create session
            token = jwt.encode(
                {"user_id": user.id, "exp": datetime.now(timezone.utc) + timedelta(hours=1) },# Authentication expires in 1 hour
                self.settings["secret_key"]
            )

            # token = jwt.encode(
            #     {"user_id": user.id, "exp": datetime.now(timezone.utc) + timedelta(milliseconds=10000) },# Authentication expires in 10 seconds - for testing
            #     self.settings["secret_key"]
            # )
            # print(token)
            self.set_secure_cookie("auth_token", token)
            self.set_status(200)
            response = {"faces": faces, "redirect": "/dashboard"}
            print("Result JSON")
            print(json.dumps(response, indent=4, sort_keys=True))
            self.write(response)
            return
        
        else: 
            formatted_proba = f"{proba:.3f}"
            # print(formatted_proba)
            # self.write({"error": f"Low Probability: {formatted_proba}%", "faces": faces}) # Testovaci vypisy
            self.write({"error": f"Low Probability: {formatted_proba}%"})
            return
    def get(self):
        if(not self.check_if_logged_in()):
            self.render("static/auth/recognize.html")