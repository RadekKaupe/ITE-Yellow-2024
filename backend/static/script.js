function fetchLatestData() {
    fetch('/latest-data')
        .then(response => response.json())
        .then(data => {
            // Assuming data has the same format as WebSocket data
            console.log(data.sensor_data)
            updateTeamData(data.sensor_data);
            
        })
        .catch(error => console.error("Error fetching latest data:", error));
}

function onBodyLoad() {
    fetchLatestData();
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
    // sensorDataArr.forEach((sensor) => {
        // console.log(`Team Name: ${sensor.team_name}`);
        // console.log(`ID: ${sensor.id}`);
        // console.log(`Team ID: ${sensor.team_id}`);
        // console.log(`Timestamp: ${sensor.timestamp}`);
        // console.log(`Temperature: ${sensor.temperature}`);
        // console.log(`Humidity: ${sensor.humidity}`);
        // console.log(`Illumination: ${sensor.illumination}`);
        // console.log("---------------"); 
    // });
    updateTeamData(sensorDataArr)
}

function updateTeamData(sensorDataArray=[]) {
    // Iterate through each sensor data and update the corresponding element
    if (sensorDataArray.length == 0) {
        return
    } 
    console.log(sensorDataArray)
    sensorDataArray.forEach((sensor) => {
        let team_name = sensor.team_name;
        let dateAndTime;
        
        // Dynamically create the element IDs based on the team_id
        let dateElement = document.getElementById(`team-${team_name}-date`);
        let timeElement = document.getElementById(`team-${team_name}-time`);

        let tempElement = document.getElementById(`team-${team_name}-temp`);
        let humidityElement = document.getElementById(`team-${team_name}-humidity`);
        let illuminationElement = document.getElementById(`team-${team_name}-illumination`);
        if (sensor.timestamp){
            dateAndTime = extractDateAndTime( sensor.timestamp);
        }
        // If the element exists, update its innerHTML
        
        if (dateElement) {
            dateElement.textContent = dateAndTime.date.toDateString();
        }
        if (timeElement) {
            timeElement.textContent = dateAndTime.time;
        }
        if (tempElement) {
            tempElement.textContent = sensor.temperature + " °C";
        }
        if (humidityElement) {
            let text = "This team doesn't measure humidity. ";
            if ( sensor.humidity){
                    text = sensor.humidity + " %";
            }
            humidityElement.textContent = text;
        }
        if (illuminationElement) {
            let text = "This team doesn't measure illumination. ";
            if ( sensor.illumination){
                    text = sensor.illumination + " lx";
            }
            illuminationElement.textContent = text;
        }
        
    });
}

function extractDateAndTime(dateObj){
    dateAndTime = String(dateObj);
    let [dateStr, time] = dateAndTime.split("T");
    var parts = dateStr.split('-');
    var date = new Date(parts[0], parts[1] - 1, parts[2]); 
    return {date, time}
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
