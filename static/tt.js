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
	{ cnt: "blue", w:0 },
	{ cnt: "red", w:0 },
	{ cnt: "green", w:0 },
	{ cnt: "yellow", w:0 }
];

function level_init(data) {
	lvl = data[1];
	r = 0; c = 0;
	for (i=0; i<lvl.length; i++) {
		s = lvl[i];
		if (s == '\n') {
			// New row
			r++;
			c = 0;
			continue;
		} else if (s == '_') {
			// Empty
		} else if (s == '0' || s == '1' || s == '2' || s == '3') {
			// Respawn base
			teams[teams_map[s]]['rx'] = c;
			teams[teams_map[s]]['ry'] = r;
			Crafty.e("Base, 2D, DOM, FlagSprite" + s)
				.origin('center')
				.attr({ x: c*50, y: r*50, w: 50, h: 50 });
		} else if (s == 'T') {
			// Tree: rotate them!
			rot = 90 * Math.floor(Math.random()*4);
			Crafty.e("Tree, 2D, DOM, MoveCollision, EnvSprite" + s)
				.origin('center')
				.attr({ x: c*50, y: r*50, w: 50, h: 50, rotation: rot })
				.trackCollision();
		} else {
			// Other env
			Crafty.e("Wall, 2D, DOM, MoveCollision, EnvSprite" + s)
				.origin('center')
				.attr({ x: c*50, y: r*50, w: 50, h: 50 })
				.trackCollision();
		};
		c++;
	}
};

function stats_init(data) {
	for (var i=0;i<4;i++) {
		t = teams[i]
		t['w'] = parseInt(data[i+1]);
		$('#'+t['cnt']).text(t['w']);
	}
};

function player_init(data) {
	t = teams[data[1]];
	rx = t['rx'] * 50;
	ry = t['ry'] * 50;
	t['obj'] = Crafty.e("Player, 2D, DOM, MoveCollision, MoveMachine, Weapon, TankSprite" + data[1])
		.origin('center')
		.attr({ x: rx, y: ry, w: 50, h: 50, _team: data[1] })
		.setupMove(SPEED, { UP_ARROW: 0, DOWN_ARROW: 180, RIGHT_ARROW: 90, LEFT_ARROW: -90 })
		.trackCollision()
		.bind("Moved", function (delta) {
			if (this.x<0) this.x = 0;
			if (this.y<0) this.y = 0;
			if (this.x > CANVAS_WIDTH-50) this.x = CANVAS_WIDTH-50;
			if (this.y > CANVAS_HEIGHT-50) this.y = CANVAS_HEIGHT-50;
			ws.send('pos:' + this.x + ':' + this.y + ':' + this.rotation)
		});
	ws.send('pos:' + t['obj'].x + ':' + t['obj'].y + ':' + t['obj'].rotation)
};

function any_hit(data) {
	t = teams[data[1]];
	w = teams[data[2]];
	w['w'] += 1
	$('#'+w['cnt']).text(w['w']);
	t['obj'].x = t['rx'] * 50;
	t['obj'].y = t['ry'] * 50;
};

function op_update(data) {
	t = teams[teams_map[data[1]]];
	tx = parseInt(data[2]);
	ty = parseInt(data[3]);
	tr = parseInt(data[4]);
	if (!t.hasOwnProperty('obj')) {
		t['obj'] = Crafty.e("Opponent, 2D, DOM, MoveCollision, TankSprite" + data[1])
			.origin('center')
			.attr({ x: tx, y: ty, w: 50, h: 50, rotation: tr, _team: data[1] })
			.trackCollision()
			.bind('Hit', function (by) {
				ws.send('hit:' + this._team + ':' + by._team);
			});
	} else { 
		t['obj'].x = tx;
		t['obj'].y = ty;
		t['obj'].rotation = tr;
	}
};

function op_fire(data) {
	t = teams[teams_map[data[1]]];
	// toododdododo
};

function op_remove(data) {
	t = teams[teams_map[data[1]]];
	if (t.hasOwnProperty('obj')) {
		t['obj'].destroy();
		delete t['obj'];
	}
};

function init() {
	ws = new WebSocket("ws://127.0.0.1:18888/");

	ws.onopen = function() {
		console.log('socket: open');
		ws.send('iwannaplay');
	};
	ws.onmessage = function(e) {
		data = e.data.split(':');
		console.log('engine:', data);
		if (data[0] == 'fuckoff') {
			alert('engine:', e.data);
		} else if (data[0] == 'okay') {
			player_init(data);
		} else if (data[0] == 'hit') {
			any_hit(data);
		} else if (data[0] == 'level') {
			level_init(data);
		} else if (data[0] == 'stats') {
			stats_init(data);
		} else if (data[0] == 'op_update') {
			op_update(data);
		} else if (data[0] == 'op_fire') {
			op_fire(data);
		} else if (data[0] == 'op_remove') {
			op_remove(data);
		} else {
			console.log('[ERROR] unknow data type', data[0]);
		}
	};
	ws.onclose = function() {
		console.log('socket: closed');
		alert("Server connection closed.");
	};
	ws.onerror = function() {
		console.log('socket: error');
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
		EnvSpriteB:  [3, 2]
	});
	
};
