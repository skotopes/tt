from os import path

# Application
APP_SECRET		= '36163ab22ba7d71060450bd8e68b0aa61840e6e4453348770af28a462deca9c2ed560f4f80b6b534'
APP_DEBUG		= True

if path.isfile('config_local.py'):
	execfile('config_local.py')
