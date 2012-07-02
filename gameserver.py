from thor import TcpServer, loop
from websocket import WebSocket
from os import path

import config

class GameClient(object):
	def __init__(self, server, connection):
		super(GameClient, self).__init__()
		# internals
		self.number = None
		self.teamid = None
		self.buffer = []
		self.x = 0
		self.y = 0
		self.r = 0
		self.server = server
		# io initialisation
		self.io = WebSocket(connection)
		self.io.on('data', self._onData)
		self.io.on('close', self._onClose)
		self.io.on('pause', self._onPause)
		self.io.pause(False)
	
	def _onData(self, data):
		for d in data:
			if d.startswith('iwannaplay'):
				self._register()
			elif d.startswith('pos'):
				self._position(d)
			elif d.startswith('fire'):
				self._fire()
			elif d.startswith('hit'):
				self._hit(d)
			else:
				print "UNKNOWN ACTION", d
	
	def _onClose(self):
		print 'client gone'
		if self.number:
			self.server.unregister(self)

	def _onPause(self, pause):
		if pause == False:
			for d in self.buffer:
				self.io.write(d)

	def _write(self, data):
		if self.io.w_paused:
			if len(self.buffer) > 70:
				# Sloooowpoke
				self.io.close()
				return
			self.buffer.append(data)
		else:
			self.io.write(data)

	def _register(self):
		self.server.register(self)
		if not self.number:
			self._write('fuckoff')
			print 'we are not in mood', self.number
		else:
			self._write('level:%s' % self.server.getLevel(self))
			self._write('okay:%d:%d' % (self.teamid, self.number))
			stats = self.server.getStats()
			self._write('stats:%d:%d:%d:%d' % (stats[0], stats[1], stats[2], stats[3]))
			self.server.updatePosClient(self)
			print 'client registred', self.number

	def _position(self, d):
		(x,y,r) = d.split(':')[1:]
		x = int(x)
		y = int(y)
		r = int(r)
		if self.x!=x or self.y!=y or self.r!=r:
			self.x = x
			self.y = y
			self.r = r
			self.server.updateClientPos(self)
		
	def _fire(self):
		self.server.updateFire(self)
	
	def _hit(self, d):
		(who, by) = d.split(':')[1:]
		who = int(who)
		by = int(by)
		self.server.updateHit(who, by)
	
	def anyHit(self, who, by):
		self._write('hit:%d:%d' % (who, by))
	
	def updateOpponent(self, client):
		self._write('op_update:%d:%d:%d:%d' % (client.teamid, client.x, client.y, client.r))

	def updateOpponentFire(self, client):
		self._write('op_fire:%d' % (client.teamid))

	def removeOpponent(self, client):
		self._write('op_remove:%d' % client.teamid)
	
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
		self.loop = loop
		self.tcp_server = TcpServer("0.0.0.0", 18888)
		self.tcp_server.on('connect', self.on_connect)
	
	def run(self):
		self.loop.run()

	def on_connect(self, connection):
		GameClient(self, connection)

	def getStats(self):
		r = []
		for t in self.teams:
			r.append(t['w'])
		return r
	
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
		for p in self.players:
			p.removeOpponent(client)

	def getLevel(self, client):
		f = open(path.join(config.LEVELS_DIR, '0001.l'))
		return f.read()
	
	# we'd like to know about other
	def updatePosClient(self, client):
		for c in self.players:
			if client.number == c.number:
				continue
			client.updateOpponent(c)
	
	# other would like to know about us
	def updateClientPos(self, client):
		for c in self.players:
			if client.number == c.number:
				continue
			c.updateOpponent(client)
	
	def updateFire(self, client):
		for c in self.players:
			if client.number == c.number:
				continue
			c.updateOpponentFire(client)
			
	def updateHit(self, who, by):
		self.teams[by]['w'] += 1
		for c in self.players:
			c.anyHit(who, by)
