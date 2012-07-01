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
		self.x = 0
		self.y = 0
		self.r = 0
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
				(x,y,r) = d.split(':')[1:]
				self.x = int(x)
				self.y = int(y)
				self.r = int(r)
				self.server.updateClientPos(self)
			elif d.startswith('fire'):
				self.server.updateFire(self)
			elif d.startswith('hit'):
				(who, by) = d.split(':')[1:]
				who = int(who)
				by = int(by)
				self.server.updateHit(who, by)
			else:
				print "UNKNOWN ACTION"
	
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
			stats = self.server.getStats()
			self.io.write('stats:%d:%d:%d:%d' % (stats[0], stats[1], stats[2], stats[3]))
			self.server.updatePosClient(self)
			print 'client registred', self.number

	def anyHit(self, who, by):
		self.io.write('hit:%d:%d' % (who, by))
	
	def updateOpponent(self, client):
		self.io.write('op_update:%d:%d:%d:%d' % (client.teamid, client.x, client.y, client.r))

	def updateOpponentFire(self, client):
		self.io.write('op_fire:%d' % (client.teamid))

	def removeOpponent(self, client):
		self.io.write('op_remove:%d' % client.teamid)
	
class GameServer(object):
	"""docstring for GameServer"""
	def __init__(self, nl=False):
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
		if nl:
			self.loop = loop.make()
			self.tcp_server = TcpServer("0.0.0.0", 18888, self.loop)
		else:
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
