from thor import TcpServer, loop
from md5 import md5
from os import path
import struct

import config

class WebSocket(object):

	# draft 76 basics
	HANDSHAKE = "\
HTTP/1.1 101 WebSocket Protocol Handshake\r\n\
Upgrade: WebSocket\r\n\
Connection: Upgrade\r\n\
Sec-WebSocket-Origin: %s\r\n\
Sec-WebSocket-Location: ws://%s/\r\n\
Sec-WebSocket-Protocol: sample\r\n\r\n%s"

	def __init__(self, connection):
		super(WebSocket, self).__init__()
		# Protocol internals
		self.method = None
		self.headers = None
		self.handshaked = False
		self.data_buffer = ''
		# callbacks: hashmap with something like O(1) or O(n) if hash function is bad
		# PS: i know about complexity
		self.callbacks = {}
		# Initialising primary connection callbacks
		self.connection = connection
		self.connection.on('data', self.onData)
		self.connection.on('close', self.onClose)
		self.connection.on('pause', self.onPause)

	def _extractKey(self, key):
		# http://stackoverflow.com/questions/4372657/websocket-handshake-problem-using-python-server
		spaces = key.count(" ")
		return int("".join([c for c in key if c.isdigit()])) / (spaces-1) # that's fucking brilliant

	def _doHandshake(self):
		num1 = self._extractKey(self.headers['Sec-WebSocket-Key1'])
		num2 = self._extractKey(self.headers['Sec-WebSocket-Key2'])
		pack = struct.pack('>II8s', num1, num2, self.data_buffer)
		sign = md5(pack).digest()
		self.connection.write(self.HANDSHAKE % (self.headers['Origin'], self.headers['Host'].strip(), sign))
		self.handshaked = True
		self.data_buffer = ''

	@property
	def data_buffer_unpacked(self):
		d = []
		# \x00test\xff
		cnt = self.data_buffer.count('\xff')
		while(cnt>0):
			cnt-=1
			p = self.data_buffer.find('\xff') + 1
			d.append(self.data_buffer[0:p].lstrip('\x00').rstrip('\xff'))
			self.data_buffer = self.data_buffer[p:]
		return d

	def onData(self, data):
		self.data_buffer += data
		if self.handshaked == False:
			if self.headers == None and self.data_buffer.find('\r\n\r\n') != -1:
				# parse header section
				method = None
				headers = {}
				(raw_headers, self.data_buffer) = self.data_buffer.split('\r\n\r\n')
				for l in raw_headers.split('\r\n'):
					if not method:
						method = l
						continue
					k,v = l.split(':', 1)
					headers[k] = v
				# Commit extracted data 
				self.method = method
				self.headers = headers
				# Try to perform handshake
				self._doHandshake()
		else:
			self.callbacks['data'](self.data_buffer_unpacked)

	def onClose(self):	
		self.callbacks['close']()

	def onPause(self, pause):
		print "pause"

	# Public methods
	def pause(self, pause):
		self.connection.pause(pause)
	
	def on(self, event, callback):
		self.callbacks[event] = callback

	def write(self, data):
		if type(data) == str:
			self.connection.write('\x00%s\xff' % data)
		elif type(data) == list or type(data) == tuple:
			d = []
			for i in data:
				d.append('\x00%s\xff' % data)
			self.connection.write(''.join(d))

class GameClient(object):
	def __init__(self, server, connection):
		super(GameClient, self).__init__()
		# internals
		self.number = None
		self.teamid = None
		self.x = 0
		self.y = 0
		self.server = server
		# io initialisation
		self.io = WebSocket(connection)
		self.io.on('data', self.onData)
		self.io.on('close', self.onClose)
		self.io.pause(False)
		
	def onData(self, data):
		for d in data:
			if d.startswith('iwannaplay'):
				self.register()
			elif d.startswith('pos'):
				(self.x,self.y) = d.split(':')[1:]
				self.server.updateClientPos(self)
			elif d.startswith('fire'):
				self.server.fire(self)
	
	def onClose(self):
		print 'client gone'
		if self.number:
			self.server.unregister(self)

	def register(self):
		self.server.register(self)
		if not self.number:
			self.io.write('fuckoff')
			print 'we are not in mood', self.number
		else:
			self.io.write('level:%s' % self.server.getLevel(self))
			self.io.write('okay:%d:%d' % (self.teamid, self.number))
			print 'client registred', self.number

	def move(self):
		pass

	def otherMove(self):
		pass

class GameServer(object):
	"""docstring for GameServer"""
	def __init__(self):
		super(GameServer, self).__init__()
		self.tcp_server = None

		self.sequence = 0
		self.players = []
		self.teams = [ 
			{ 'w':0, "p":[] },
			{ 'w':0, "p":[] },
			{ 'w':0, "p":[] },
			{ 'w':0, "p":[] }
		]
	
	def run(self):
		self.tcp_server = TcpServer("127.0.0.1", 18888)
		self.tcp_server.on('connect', self.on_connect)
		loop.run()

	def on_connect(self, connection):
		GameClient(self, connection)

	# game logic
	def register(self, client):
		for i in self.teams:
			if len(i['p']) == 0:
				self.sequence += 1
				self.players.append(client)
				i['p'].append(client)
				client.number = self.sequence
				client.teamid = self.teams.index(i)
				break # ok? please?
	
	def unregister(self, client):
		self.teams[client.teamid]['p'].remove(client)
		self.players.remove(client)
	
	def updateClientPos(self, client):
		print client.x, client.y
	
	def getLevel(self, client):
		f = open(path.join(config.LEVELS_DIR, '0001.l'))
		return f.read()
		
	def fire(self, client):
		pass