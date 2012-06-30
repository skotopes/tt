WEB_SOCKET_SWF_LOCATION = "/static/WebSocketMain.swf";
WEB_SOCKET_DEBUG = true;

var ws;

function init_game() {
	ws = new WebSocket("ws://127.0.0.1:18888/");

	ws.onopen = function() {
		console.log("Socket: open");
		ws.send('iwannaplay');
	};
	ws.onmessage = function(e) {
		console.log("Socket: new data");
		if e.data == 'fuckoff':
		
		else if e.data == 'okay':
		else if e.data == 'update':
	};
	ws.onclose = function() {
		console.log("onclose");
	};
	ws.onerror = function() {
		console.log("onerror");
	};

	Crafty.init(700, 700);
	Crafty.background('#020217');
};
