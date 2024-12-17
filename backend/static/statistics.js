function fetchLatestData() {
    fetch('/latest-data')
        .then(response => response.json())
        .then(data => {
            // Assuming data has the same format as WebSocket data
            // console.log(data)
            updateElements(data)
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

function updateElements(data){
    // console.log(data)
    totalDataEL = document.getElementById('total-data');
    avgTmpEl = document.getElementById('avg-tmp');
    avgHumEl = document.getElementById('avg-hum');
    avgIllEl = document.getElementById('avg-ill');
    latestTimesEl = document.getElementById('time')
    latestDateEl = document.getElementById('date')
    if (totalDataEL && data.total_data){
        totalDataEL.textContent = data.total_data;
    }
    if (avgTmpEl && data.average_temperature){
        avgTmpEl.textContent = data.average_temperature.toFixed(2);
    }
    if (avgHumEl && data.average_humidity){
        avgHumEl.textContent = data.average_humidity.toFixed(2);
    }        
    if (avgIllEl && data.average_illumination){
        avgIllEl.textContent = data.average_illumination.toFixed(2);
    }
    if (latestTimesEl && latestDateEl && data.latest_yellow_timestamp){
        let date =  new Date(data.latest_yellow_timestamp);
            // console.log(date)
            formattedDate = date.toLocaleDateString('en-US', {
                weekday: 'long',  // Full day name (e.g., "Tuesday")
                month: 'short',   // Abbreviated month name (e.g., "Nov")
                day: 'numeric',   // Day of the month (e.g., "26")
                year: 'numeric'   // Full year (e.g., "2024")
              });
            localTime = date.toLocaleTimeString('en-GB', { hour12: false });
        latestTimesEl.textContent = localTime
        latestDateEl.textContent = formattedDate
        // avgIllEl.textContent = data.average_illumination.toFixed(2);
        
    }
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
    updateElements(data)
}

