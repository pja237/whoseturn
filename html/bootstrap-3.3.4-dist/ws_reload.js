
var ws = new WebSocket("ws://192.168.56.207:8888/ws");
ws.onopen = function() {
    ws.send("Hello, world");
};
ws.onmessage = function (evt) {
    //alert(evt.data);
    location.reload();
};

