from thor import TcpServer, loop
from md5 import md5
import struct

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
		# callbacks: hashmap with something like O(1) or O(n) in worst key
		self.callbacks = {}
		# Initialising primary connection callbacks
		self.connection = connection
		self.connection.on('data', self.on_data)
		self.connection.on('close', self.on_close)
		self.connection.on('pause', self.on_pause)
	
	def pause(self, pause):
		self.connection.pause(pause)
	
	def on(self, event, callback):
		self.callbacks[event] = callback
	
	def do_extractkey(self, key):
		# http://stackoverflow.com/questions/4372657/websocket-handshake-problem-using-python-server
		spaces = key.count(" ")
		return int("".join([c for c in key if c.isdigit()])) / (spaces-1) # that's fucking brilliant
	
	def write(self, data):
		if type(data) == str:
			self.connection.write('\x00%s\xff' % data)
		elif type(data) == list or type(data) == tuple:
			d = []
			for i in data:
				d.append('\x00%s\xff' % data)
			self.connection.write(''.join(d))

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

	def do_handshake(self):
		num1 = self.do_extractkey(self.headers['Sec-WebSocket-Key1'])
		num2 = self.do_extractkey(self.headers['Sec-WebSocket-Key2'])
		pack = struct.pack('>II8s', num1, num2, self.data_buffer)
		sign = md5(pack).digest()
		self.connection.write(self.HANDSHAKE % (self.headers['Origin'], self.headers['Host'].strip(), sign))
		self.handshaked = True
		self.data_buffer = ''
	
	def on_data(self, data):
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
				self.do_handshake()
		else:
			self.callbacks['data'](self.data_buffer_unpacked)

	def on_close(self):	
		self.callbacks['close']()

	def on_pause(self, pause):
		print "pause"

class GameClient(object):
	def __init__(self, server, connection):
		super(GameClient, self).__init__()
		# internals
		self.number = None
		self.server = server
		# io initialisation
		self.io = WebSocket(connection)
		self.io.on('data', self.on_data)
		self.io.on('close', self.on_close)
		self.io.pause(False)
		
	def on_data(self, data):
		for d in data:
			if d.startswith('iwannaplay'):
				self.number = self.server.register(self)
				if not self.number:
					self.io.write('fuckoff')
					print 'we are not in mood', self.number
				else:
					self.io.write('okay:%d' % self.number)
					print 'client registred', self.number
			elif d.startswith('pos'):
				self.server.update_pos(self)
			elif d.startswith('fire'):
				self.server.fire(self)
	
	def on_close(self):
		print 'client gone'
		if self.number:
			self.server.unregister(self)

class GameServer(object):
	"""docstring for GameServer"""
	def __init__(self):
		super(GameServer, self).__init__()
		self.tcp_server = None
		self.active_clients = {}
		self.sequence = 0
	
	def run(self):
		self.tcp_server = TcpServer("127.0.0.1", 18888)
		self.tcp_server.on('connect', self.on_connect)
		loop.run()

	def on_connect(self, connection):
		GameClient(self, connection)

	# game logic
	def register(self, client):
		if len(self.active_clients) >= 4:
			return None
		self.sequence += 1
		self.active_clients[self.sequence] = client
		return self.sequence
	
	def unregister(self, client):
		self.active_clients.pop(client.number)
	
	def update_pos(self, client):
		pass
	
	def fire(self, client):
		pass