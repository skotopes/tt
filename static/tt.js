WEB_SOCKET_SWF_LOCATION = "/static/WebSocketMain.swf";
WEB_SOCKET_DEBUG = true;

CANVAS_WIDTH  = 550;
CANVAS_HEIGHT = 550;

CANVAS_TILE_W = 50;
CANVAS_TILE_H = 50;

SPEED = 5

var ws;
var player;
var teams_map = {
	A:0,
	0:0,
	B:1,
	1:1,
	C:2,
	2:2,
	D:3,
	3:3
};
var teams = [
	{},
	{},
	{},
	{}
];

function init_level(data) {
	lvl = data[1];
	r = 0; c = 0;
	for (i=0; i<lvl.length; i++) {
		s = lvl[i];
		if (s == '\n') {
			r++;
			c = 0;
			continue;
		} else if (s == '_') {
			// empty
		} else if (s == '0' || s == '1' || s == '2' || s == '3') {
			// respawn base
			teams[teams_map[s]]['rx'] = c;
			teams[teams_map[s]]['ry'] = r;
		} else if (s == 'A' || s == 'B' || s == 'C' || s == 'D') {
			// flag base
			teams[teams_map[s]]['fx'] = c;
			teams[teams_map[s]]['fy'] = r;
			
			Crafty.e("Wall, 2D, DOM, EnvSprite" + s)
				.attr({ x: c*50, y: r*50, w: 50, h: 50 })
				.origin('center');
		} else {
			Crafty.e("Wall, 2D, DOM, MoveCollision, EnvSprite" + s)
				.attr({ x: c*50, y: r*50, w: 50, h: 50 })
				.trackCollision()
				.origin('center');
		};
		c++;
	}
};

function init_player(data) {
	rx = teams[data[1]]['rx'] * 50;
	ry = teams[data[1]]['ry'] * 50;
	player = Crafty.e("2D, DOM, MoveCollision, MoveMachine, TankSprite" + data[1])
		.attr({ x: rx, y: ry, w: 50, h: 50 })
		.origin('center')
		.setupMove(SPEED, { UP_ARROW: 0, DOWN_ARROW: 180, RIGHT_ARROW: 90, LEFT_ARROW: -90 })
		.trackCollision()
		.bind("Moved", function (delta) {
			if (this.x<0) this.x = 0;
			if (this.y<0) this.y = 0;
			if (this.x > CANVAS_WIDTH-50) this.x = CANVAS_WIDTH-50;
			if (this.y > CANVAS_HEIGHT-50) this.y = CANVAS_HEIGHT-50;
			ws.send('pos:' + this.x + ':' + this.y + ':' + this.rotation)
		});
	ws.send('pos:' + player.x + ':' + player.y + ':' + player.rotation)
};

function update_opponent(data) {
	t = teams[teams_map[data[1]]];
	tx = parseInt(data[2]);
	ty = parseInt(data[3]);
	tr = parseInt(data[4]);
	console.log(data[1]);
	if (!t.hasOwnProperty('obj')) {
		t['obj'] = Crafty.e("2D, DOM, MoveCollision, TankSprite" + data[1])
			.attr({ x: tx, y: ty, w: 50, h: 50, rotation: tr })
			.origin('center')
			.trackCollision();
	} else { 
		t['obj'].x = tx;
		t['obj'].y = ty;
		t['obj'].rotation = tr;
	}
};

function init() {
	ws = new WebSocket("ws://127.0.0.1:18888/");

	ws.onopen = function() {
		console.log("Socket: open");
		ws.send('iwannaplay');
	};
	ws.onmessage = function(e) {
		data = e.data.split(':');
		if (data[0] == 'fuckoff') {
			alert("engine: Server do not wanna play with us.");
		} else if (data[0] == 'okay') {
			console.log('engine: lets play:', e.data);
			init_player(data);
		} else if (data[0] == 'level') {
			console.log('engine: got level');
			init_level(data);
		} else if (data[0] == 'update') {
			console.log('engine: update notify', e.data);
			update_opponent(data);
		} else {
			console.log("engine: unknow data <" + e.data + ">");
		}
	};
	ws.onclose = function() {
		alert("Server connection closed.");
	};
	ws.onerror = function() {
		alert("Socket error, report this bug to aku");
	};

	Crafty.init(CANVAS_WIDTH, CANVAS_HEIGHT);
	Crafty.background('#222237');
	Crafty.sprite(50, "/static/tt_sprite.png", {
		// Tanks
		TankSprite0: [0, 0],
		TankSprite1: [1, 0],
		TankSprite2: [2, 0],
		TankSprite3: [3, 0],
		// team flags
		FlagSprite0: [0, 1],
		FlagSprite1: [1, 1],
		FlagSprite2: [2, 1],
		FlagSprite3: [3, 1],
		// Some env
		EnvSpriteT:  [0, 2],
		EnvSpriteW:  [1, 2],
		EnvSpriteS:  [2, 2],
		// Tank bases
		EnvSpriteA:  [3, 2],
		EnvSpriteB:  [3, 2],
		EnvSpriteC:  [3, 2],
		EnvSpriteD:  [3, 2],
	});
	
};
