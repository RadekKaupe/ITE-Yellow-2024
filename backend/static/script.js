function fetchLatestData() {
    fetch('/latest-data')
        .then(response => response.json())
        .then(data => {
            // Assuming data has the same format as WebSocket data
            // console.log(data)
            let just_sensor_data = data.sensor_data
            updateTeamData(just_sensor_data);
            
        })
        .catch(error => console.error("Error fetching latest data:", error));
}

function onBodyLoad() {
    fetchLatestData();
    const hostname = window.location.hostname;  
    ws = new WebSocket(`ws://${hostname}:8881/websocket`);
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
    // console.log(data.sensor_data)
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
    // console.log(sensorDataArray)
    sensorDataArray.forEach((sensor) => {
        let outliers = sensor.outliers
        let team_name = sensor.team_name;
        let dateAndTime;
        
        // Dynamically create the element IDs based on the team_id
        let dateElement = document.getElementById(`team-${team_name}-date`);
        let timeElement = document.getElementById(`team-${team_name}-time`);

        let tempElement = document.getElementById(`team-${team_name}-temp`);
        let humidityElement = document.getElementById(`team-${team_name}-humidity`);
        let illuminationElement = document.getElementById(`team-${team_name}-illumination`);
        if (sensor.timestamp){
            // console.log(sensor.timestamp)
            let date =  new Date(sensor.timestamp);
            // console.log(date)
            formattedDate = date.toLocaleDateString('en-US', {
                weekday: 'long',  // Full day name (e.g., "Tuesday")
                month: 'short',   // Abbreviated month name (e.g., "Nov")
                day: 'numeric',   // Day of the month (e.g., "26")
                year: 'numeric'   // Full year (e.g., "2024")
              });
            localTime = date.toLocaleTimeString('en-GB', { hour12: false }); 
            // console.log(localTime);
            // const date = new Date(dateAndTime);
            // const localTime = date.toLocaleTimeString('en-GB', { hour12: false }); // 'en-GB' is used to get 24-hour format
            // console.log(localTime);
        }
        // If the element exists, update its innerHTML
        
        if (dateElement) {
            dateElement.textContent = formattedDate;
        }
        if (timeElement) {
            timeElement.textContent = localTime; 
        }
        if (tempElement) {
            
            tempElement.textContent = sensor.temperature + " °C";
            if (outliers.is_temperature_out_of_range === true) {
                tempElement.style.color = "#ecf0f1";
                tempElement.style.backgroundColor = "#e74c3c";
                if (team_name === "red"){
                    tempElement.style.backgroundColor = "#333333";
                } 
                tempElement.style.fontWeight = "bold";
            } else{
                tempElement.style.textDecoration = "underline";
            }
        }
        if (humidityElement) {
            if (outliers.is_humidity_out_of_range === true) {
                humidityElement.style.color = "#ecf0f1";
                humidityElement.style.backgroundColor = "#e74c3c";
                if (team_name === "red"){
                    humidityElement.style.backgroundColor = "#333333";
                } 
                humidityElement.style.fontWeight = "bold";
            } else{
                humidityElement.style.textDecoration = "underline";
            }
            let text = "This team probably doesn't measure humidity right now. ";
            if ( sensor.humidity != null ){
                    text = sensor.humidity + " %";
            }
            humidityElement.textContent = text;
        }
        if (illuminationElement) {
            if (outliers.is_illumination_out_of_range === true) {
                illuminationElement.style.color = "#ecf0f1";
                illuminationElement.style.backgroundColor = "#e74c3c";
                if (team_name === "red"){
                    illuminationElement.style.backgroundColor = "#333333";
                } 
                illuminationElement.style.fontWeight = "bold";
            } else{
                illuminationElement.style.textDecoration = "underline";
            }
            let text = "This team probably doesn't measure illumination right now. ";
            if ( sensor.illumination != null){
                    text = sensor.illumination + " lx";
            }
            illuminationElement.textContent = text;
        }
        
    });
}

// function extractDateAndTime(dateObj){
//     dateAndTime = String(dateObj);
//     let [dateStr, time] = dateAndTime.split("T");
//     var parts = dateStr.split('-');
//     var date = new Date(parts[0], parts[1] - 1, parts[2]); 
//     return {date, time}
// }

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
