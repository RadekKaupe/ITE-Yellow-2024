
span.innerHTML = "nothing";
function onBodyLoad() {
    ws = new WebSocket('ws://localhost:8881/websocket')     // ws is a global variable (index.html)
    ws.onopen = onSocketOpen
    ws.onmessage = onSocketMessage
    ws.onclose = onSocketClose
}

function onSocketOpen() {
    console.log("WS client: Websocket opened.")
}

function onSocketMessage(message) {
    // let span = document.getElementById("counter-value")
    
    var data
    try {
        data = JSON.parse(message.data)    
    } catch(e) {
        data = message.data
    }
    let sensorDataArr = data.sensor_data
    sensorDataArr.forEach((sensor) => {
        console.log(`Team Name: ${sensor.team_name}`);
        console.log(`ID: ${sensor.id}`);
        console.log(`Team ID: ${sensor.team_id}`);
        console.log(`Timestamp: ${sensor.timestamp}`);
        console.log(`Temperature: ${sensor.temperature}`);
        console.log(`Humidity: ${sensor.humidity}`);
        console.log(`Illumination: ${sensor.illumination}`);
        console.log("---------------");
        updateTeamData(sensorDataArr)
    });
}

function updateTeamData(sensorDataArray) {
    // Iterate through each sensor data and update the corresponding element
    sensorDataArray.forEach((sensor) => {
        let team_name = sensor.team_name;

        // Dynamically create the element IDs based on the team_id
        let timestampElement = document.getElementById(`team-${team_name}-timestamp`);
        let tempElement = document.getElementById(`team-${team_name}-temp`);
        let humidityElement = document.getElementById(`team-${team_name}-humidity`);
        let illuminationElement = document.getElementById(`team-${team_name}-illumination`);

        // If the element exists, update its innerHTML
        if (timestampElement) {
            timestampElement.innerHTML = sensor.timestamp;
        }
        if (tempElement) {
            tempElement.innerHTML = sensor.temperature;
        }
        if (humidityElement) {
            humidityElement.innerHTML = sensor.humidity;
        }
        if (illuminationElement) {
            illuminationElement.innerHTML = sensor.illumination;
        }
    });
}



function onSocketClose() {
    console.log("WS client: Websocket closed.")
}

function sendToServer() {
    var params = {
        topic: "smarthome/room/door_open",
        sensors: ["ls311b38_02"]
    }
    ws.send(JSON.stringify(params))

}

function loadJsonFile() {
    var request = new XMLHttpRequest();
    request.open("GET", 'file_name.json', false);
    request.send(null)
    return JSON.parse(request.responseText);
}

function loadJsonHandler() {
    if (window.XMLHttpRequest) {
        xmlhttp = new XMLHttpRequest();
    }
    xmlhttp.open('GET', '/json/', false);
    xmlhttp.send(null);

    return  JSON.parse(xmlhttp.responseText);
}

function test_button_click(){
    console.log("Mam rad vlaky.")
}
