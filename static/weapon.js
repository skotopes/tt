Crafty.c("Weapon", {
	init: function() {
		this._delay = 0;
		
		this.bind("EnterFrame", function (delta) {
			if (this._delay > 0)
				this._delay--;
		}).bind("KeyDown",function(e) {
			if (this._delay > 0) 
				return;
			// 10 frame delay
			this._delay = 10;
			if (e.key == Crafty.keys['SPACE']) {
				ws.send('fire:' + this._team);
				rx = this.x + 25;
				ry = this.y + 25;
				rr = this.rotation;
				Crafty.e("2D, DOM, MoveCollision, Color")
					.origin('center')
					.color('red')
					.attr({ x: rx, y: ry, w: 4, h: 4, rotation: rr, _speed: 10, _parent: this })
					.trackCollision()
					.bind("EnterFrame", function (delta) {
						// calculate x,y displacement
						dx = Math.round(Math.sin(this.rotation * (Math.PI / 180)) * 1000 * this._speed) / 1000;
						dy = - Math.round(Math.cos(this.rotation * (Math.PI / 180)) * 1000 * this._speed) / 1000;
						// new position
						x = this.x + dx;
						y = this.y + dy;
						// check collisions
						cldd = this.is_collided(x, y, this.w, this.h);
						// apply if everyting is fine
						if (!cldd || cldd == this._parent) {
							this.x = x;
							this.y = y;
							this.trigger("Moved", {x:dx, y:dy});
						} else {
							cldd.trigger("Hit", this._parent);
							this.destroy();
						}
						if (x<0 || x> CANVAS_WIDTH || y<0 || y>CANVAS_HEIGHT) {
							this.destroy();
						}
					});
			}
		})
	}
});
