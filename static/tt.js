WEB_SOCKET_SWF_LOCATION = "/static/WebSocketMain.swf";
WEB_SOCKET_DEBUG = true;

CANVAS_WIDTH  = 555;
CANVAS_HEIGHT = 555;
SPEED = 3

var ws;
var player;

function init_game(data) {
	ds = data.split(":");
	
	Crafty.e("2D, DOM, Multiway, Collision, WiredHitBox, TankSprite" + ds[1])
		.attr({ x: 0, y: 0, w: 50, h: 50 })
		.multiway(SPEED, { UP_ARROW: -90, DOWN_ARROW: 90, LEFT_ARROW: 180, RIGHT_ARROW: 0 })
		.origin('center')
		.collision(new Crafty.polygon([0,0], [0,49], [49,49], [49,0]))
		.bind("Moved", function (direction) {
			if (this.x<0) this.x = 0;
			if (this.y<0) this.y = 0;
			if (this.x > CANVAS_WIDTH-50) this.x = CANVAS_WIDTH-50;
			if (this.y > CANVAS_HEIGHT-50) this.y = CANVAS_HEIGHT-50;
			ws.send('pos:' + this.x + ':' + this.y)
		})
		.onHit("Wall",function(obj) {
			this.disableControl();
		})
		.bind("NewDirection", function (direction) {
			if (direction.x < 0) {
				this.rotation = -90;
			} if (direction.x > 0) {
				this.rotation = 90;
			} if (direction.y < 0) {
				this.rotation = 0;
			} if (direction.y > 0) {
				this.rotation = 180;
			}
		});
};

function init_level(data) {
	l = data.split(":")[1];
	r = 0; c = 0;
	for (i=0; i<l.length; i++) {
		s = l[i];
		
		console.log(s);
		if (s == '\n') {
			r++;
			c = 0;
			continue;
		} else if (s == '_') {
			c++;
			continue;
		} else {
			Crafty.e("Wall, 2D, DOM, Collision, WiredHitBox, EnvSprite" + s)
				.attr({ x: c*50, y: r*50, w: 50, h: 50 })
				.origin('center')
				.collision(new Crafty.polygon([0,0], [0,50], [50,50], [50,0]));
			c++;
		};
	}
};

function init() {
	ws = new WebSocket("ws://127.0.0.1:18888/");

	ws.onopen = function() {
		console.log("Socket: open");
		ws.send('iwannaplay');
	};
	ws.onmessage = function(e) {
		if (e.data == 'fuckoff') {
			alert("Server do not wanna play with us.");
		} else if (e.data >= 'okay') {
			console.log('lets play');
			init_game(e.data);
		} else if (e.data >= 'level') {
			console.log('level notify');
			init_level(e.data);
		} else if (e.data >= 'update') {
			console.log('update notify');
		} else {
			console.log("Socket: unknow data <" + e.data + ">");
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
