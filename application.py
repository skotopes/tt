from flask import *

import config

app = Flask(__name__)

app.debug = config.APP_DEBUG
app.secret_key = config.APP_SECRET

@app.errorhandler(404)
def page_not_found(error):
	return render_template('404.html'), 404

@app.errorhandler(500)
def page_not_found(error):
	return render_template('500.html'), 500
