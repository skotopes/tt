from application import *

@app.route("/")
def index():
	return render_template('index.html', host=request.host.split(':')[0])
