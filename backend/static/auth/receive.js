// The width and height of the captured photo. We will set the
// width to the value defined here, but the height will be
// calculated based on the aspect ratio of the input stream.

var width = 320; // We will scale the photo width to this
var height = 0; // This will be computed based on the input stream

// |streaming| indicates whether or not we're currently streaming
// video from the camera. Obviously, we start at false.

var streaming = false;

// The various HTML elements we need to configure or control. These
// will be set by the startup() function.

var video = null;
var canvas = null;
var takeImageButton = null;
const hostname = window.location.hostname;
const port = window.location.port; // This will give you the port number
// const ws = new WebSocket(`wss://${hostname}:${port}/websocket`); //VM
const ws = new WebSocket(`ws://${hostname}:${port}/websocket`); //local

ws.onmessage = function (ev) {
    try {
        const data = JSON.parse(ev.data);

        if (data.success) {
            writeSuccessMessage(data.success);
        }
        if(data.error){
            writeErrorMessage(data.error)
        }
    } catch (e) {
        console.error("Failed to parse message:", e);
    }
};
function startup() {
    video = document.getElementById("video");
    canvas = document.getElementById("canvas");
    takeImageButton = document.getElementById("take-img");
    const trainButton = document.getElementById("train");

    navigator.mediaDevices
        .getUserMedia({ video: true, audio: false })
        .then(function (stream) {
            video.srcObject = stream;
            video.play();
        })
        .catch(function (err) {
            console.log("An error occurred: " + err);
        });

    video.addEventListener(
        "canplay",
        function (ev) {
            if (!streaming) {
                height = video.videoHeight / (video.videoWidth / width);

                // Firefox currently has a bug where the height can't be read from
                // the video, so we will make assumptions if this happens.

                if (isNaN(height)) {
                    height = width / (4 / 3);
                }

                video.setAttribute("width", width);
                video.setAttribute("height", height);
                canvas.setAttribute("width", width);
                canvas.setAttribute("height", height);
                streaming = true;
            }
        },
        false
    );

    takeImageButton.addEventListener(
        "click",
        function (ev) {
            takepicture();
            ev.preventDefault();
        },
        false
    );
    trainButton.addEventListener("click", () => {
        window.location.href = "/train";
    });
}

// Capture a photo by fetching the current contents of the video
// and drawing it into a canvas, then converting that to a PNG
// format data URL. By drawing it on an offscreen canvas and then
// drawing that to the screen, we can change its size and/or apply
// other changes before drawing it.
function sendpicture(data) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/receive_image", true);
    xhr.setRequestHeader("Content-Type", "text/plain");
    xhr.onreadystatechange = function () {
        const response = JSON.parse(xhr.response);
        // console.log(response);
        if (response.error) {
            writeErrorMessage(response.error);
        }
        if (response.success) {
            writeSuccessMessage(response.success);
        }
    };
    xhr.send(data);
}

function takepicture() {
    var context = canvas.getContext("2d");
    if (width && height) {
        canvas.width = width;
        canvas.height = height;
        context.drawImage(video, 0, 0, width, height);

        var data = canvas.toDataURL("image/png");
        sendpicture(data);
    }
}

function recognizepicture(data) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/recognize", true);

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            response = JSON.parse(xhr.response);

            faces = response.faces;
            console.log(faces);

            names = [];
            faces.forEach((face) =>
                names.push(
                    face.name + " (" + Math.round(face.prob * 100) + "%)"
                )
            );
            names = names.join(", ");
            console.log(names);

            results.innerHTML = names;
        }
    };

    xhr.setRequestHeader("Content-Type", "text/plain");
    xhr.send(data);
}

function recognize() {
    var context = canvas.getContext("2d");
    if (width && height) {
        canvas.width = width;
        canvas.height = height;
        context.drawImage(video, 0, 0, width, height);

        var data = canvas.toDataURL("image/png");
        recognizepicture(data);
    }
}

// Set up our event listener to run the startup process
// once loading is complete.
window.addEventListener("load", startup, false);

import { writeErrorMessage, writeSuccessMessage } from "./messageDisplay.js";
