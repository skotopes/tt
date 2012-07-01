Crafty.c("MoveMachine", {
	init: function() {
		this._keys = {};
		this._mkp = 0;
		
		this.bind("KeyDown",function(e) {
			if(this._keys.hasOwnProperty(e.key)) {
				this.rotation = this._keys[e.key];
				this._mkp ++;
			};
		}).bind("KeyUp",function(e) {
			if(this._keys.hasOwnProperty(e.key)) {
				this._mkp --;
			};
		});
		
		this.bind("EnterFrame",function(e) {
			if (this._mkp > 0) {
				dx = Math.round(Math.sin(this.rotation * (Math.PI / 180)) * 1000 * this._speed) / 1000;
				dy = - Math.round(Math.cos(this.rotation * (Math.PI / 180)) * 1000 * this._speed) / 1000;
				x = this.x + dx;
				y = this.y + dy;
				
				cldd = this.is_collided(x, y, this.w, this.h);
				if (cldd) {
					if (x%50<16) x=x-x%50;
					if (x%50>44) x=x-x%50+50;
					if (y%50<16) y=y-y%50;
					if (y%50>44) y=y-y%50+50;
					cldd = this.is_collided(x, y, this.w, this.h);
				}
				if (!cldd) {
					this.x = x;
					this.y = y;
					this.trigger("Moved", {x:dx, y:dy});
				}
			}
		});
	},
	setupMove: function(speed, keys) {
		this._speed = speed;
		for(var k in keys) {
			this._keys[Crafty.keys[k]] = keys[k];
		};
		return this;
	}
});
