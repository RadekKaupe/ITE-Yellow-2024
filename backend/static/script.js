// console.log(document)
let spans = document.getElementsByTagName("span") //get element by ID ani query selector nefungovaly
console.log(counterValue)
if (spans.length > 0) {
    // Access the first <span> element and set its innerHTML
    spans[0].innerHTML = 0; // Set innerHTML to a number, e.g., 14
}
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
    var data
    try {
        data = JSON.parse(message.data)    
    } catch(e) {
        data = message.data
    }
    console.log(message.data)
    if (data.counter !== undefined) {
        if (spans == null){
            console.log("counterValue is Null!")
            console.log(spans[0])
        } else{
            console.log(spans[0])
            spans[0].innerHTML = data.counter; // This will now correctly update the span
        }
        
    }
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
