Crafty.c("MoveMachine", {
	init: function() {
		this._keys = {};
		this._mkp = 0;
		// Bind to events
		this.bind("KeyDown",function(e) {
			if(this._keys.hasOwnProperty(e.key)) {
				// pick up current rotation and increment keys pressed
				this.rotation = this._keys[e.key];
				this._mkp ++;
			};
		}).bind("KeyUp",function(e) {
			if(this._keys.hasOwnProperty(e.key)) {
				// decrement keys pressed
				this._mkp --;
			};
		}).bind("EnterFrame",function(e) {
			if (this._mkp > 0) {
				// calculate x,y displacement
				dx = Math.round(Math.sin(this.rotation * (Math.PI / 180)) * 1000 * this._speed) / 1000;
				dy = - Math.round(Math.cos(this.rotation * (Math.PI / 180)) * 1000 * this._speed) / 1000;
				// new position
				x = this.x + dx;
				y = this.y + dy;
				// check collisions
				cldd = this.is_collided(x, y, this.w, this.h);
				// move auto aligment
				if (cldd) {
					if (x%50<16) x=x-x%50;
					if (x%50>44) x=x-x%50+50;
					if (y%50<16) y=y-y%50;
					if (y%50>44) y=y-y%50+50;
					cldd = this.is_collided(x, y, this.w, this.h);
				}
				// apply if everyting is fine
				if (!cldd) {
					this.x = x;
					this.y = y;
					this.trigger("Moved", {x:dx, y:dy});
				}
			}
		});
	},
	setupMove: function(speed, keys) {
		// setup keys and speed
		this._speed = speed;
		for(var k in keys) {
			this._keys[Crafty.keys[k]] = keys[k];
		};
		return this;
	}
});
