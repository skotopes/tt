Crafty.c("MoveCollision", {
	_objects: [],
	init: function() {
		this.bind("Remove", function (delta) {
			this._objects.pop(this);
		});
	},
	is_collided: function(x,y,w,h) {
		for (var i=0; i<this._objects.length; i++) {
			ob = this._objects[i];
			if (ob == this)
				continue;
			if (ob.intersect(x,y,w,h)) {
				return ob;
			}
		}
		return false;
	},
	trackCollision: function() {
		this._objects.push(this);
		return this;
	}
});
