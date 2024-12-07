function fetchLatestData() {
    fetch('/latest-data')
        .then(response => response.json())
        .then(data => {
            // Assuming data has the same format as WebSocket data
            // console.log(data)
            let total_data = data.total_data
            console.log(total_data)
            updateStatisticsEl(total_data)
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

function updateStatisticsEl(total_data){
    document.getElementById('total-data').textContent = total_data;
}

function onSocketClose() {
    console.log("WS client: Websocket closed.")
}

function onSocketMessage(message) {
    // let span = document.getElementById("counter-value")
    
    var data
    try {
        data = JSON.parse(message.data)    
    } catch(e) {
        data = message.data
    }
    let total_data = data.total_data
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
    updateStatisticsEl(total_data)
}

