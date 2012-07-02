from hashlib import sha1, md5
from base64 import b64encode
import struct

class WebSocket(object):
	# draft 76 basics
	HANDSHAKE76 = "\
HTTP/1.1 101 WebSocket Protocol Handshake\r\n\
Upgrade: WebSocket\r\n\
Connection: Upgrade\r\n\
Sec-WebSocket-Origin: %s\r\n\
Sec-WebSocket-Location: ws://%s/\r\n\
Sec-WebSocket-Protocol: sample\r\n\r\n%s"

	HANDSHAKE13 = '\
HTTP/1.1 101 Switching Protocols\r\n\
Upgrade: websocket\r\n\
Connection: Upgrade\r\n\
Sec-WebSocket-Accept: %s\r\n\
Sec-WebSocket-Protocol: chat\r\n\r\n'

	def __init__(self, connection):
		super(WebSocket, self).__init__()
		# Protocol internals
		self.method = None
		self.version = None
		self.headers = None
		self.handshaked = False
		self.data_buffer = ''
		self.callbacks = {}
		# Initialising primary connection callbacks
		self.connection = connection
		self.connection.on('data', self._onData)
		self.connection.on('close', self._onClose)
		self.connection.on('pause', self._onPause)
		self.w_paused = False
		self.r_paused = True

	# proto v76 obsolet
	def _extractKey76(self, key):
		# http://stackoverflow.com/questions/4372657/websocket-handshake-problem-using-python-server
		spaces = key.count(" ")
		return int("".join([c for c in key if c.isdigit()])) / (spaces-1) # that's fucking brilliant

	def _doHandshake76(self):
		num1 = self._extractKey76(self.headers['Sec-WebSocket-Key1'])
		num2 = self._extractKey76(self.headers['Sec-WebSocket-Key2'])
		pack = struct.pack('>II8s', num1, num2, self.data_buffer)
		sign = md5(pack).digest()
		self.connection.write(self.HANDSHAKE76 % (self.headers['Origin'], self.headers['Host'].strip(), sign))
		self.handshaked = True
		self.data_buffer = ''

	def _doProcessData76(self):
		d = []
		# \x00test\xff
		cnt = self.data_buffer.count('\xff')
		while(cnt>0):
			cnt-=1
			p = self.data_buffer.find('\xff') + 1
			d.append(self.data_buffer[0:p].lstrip('\x00').rstrip('\xff'))
			self.data_buffer = self.data_buffer[p:]
		if len(d) > 0:
			self.callbacks['data'](d)

	def _write76(self, data):
		if type(data) == str:
			self.connection.write('\x00%s\xff' % data)
		elif type(data) == list or type(data) == tuple:
			d = []
			for i in data:
				d.append('\x00%s\xff' % data)
			self.connection.write(''.join(d))

	# proto v13 latest
	def _doHandshake13(self):
		step1 = sha1(self.headers['Sec-WebSocket-Key'].lstrip(' ') + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11')
		step2 = b64encode(step1.digest())
		self.connection.write(self.HANDSHAKE13 % step2)
		self.handshaked = True
		self.data_buffer = ''
	
	def _doMask13(self, data, mask_key):
		masked = bytearray(data)
		key = map(ord, mask_key)
		for i in range(len(data)):
			masked[i] = masked[i] ^ key[i%4]
		return masked
	
	def _doExtractMessage(self):
		first_byte = ord(self.data_buffer[0])
		fin = (first_byte >> 7) & 1
		rsv1 = (first_byte >> 6) & 1
		rsv2 = (first_byte >> 5) & 1
		rsv3 = (first_byte >> 4) & 1
		opcode = first_byte & 0xf
		if fin not in [0, 1]:
			raise Exception()
		if rsv1 or rsv2 or rsv3:
			raise Exception()
		if 2 < opcode < 8 or opcode > 0xA:
			raise Exception()
		if opcode > 0x7 and fin == 0:
			raise Exception()
		second_byte = ord(self.data_buffer[1])
		mask = (second_byte >> 7) & 1
		payload_length = second_byte & 0x7f
		if opcode > 0x7 and payload_length > 125:
			raise Exception()
		if mask:
			key = self.data_buffer[2:6]
		msg = self._doMask13(self.data_buffer[6:payload_length+6], key)
		self.data_buffer = self.data_buffer[payload_length+6:]
		return msg
			
	def _doProcessData13(self):
		m = []
		while len(self.data_buffer) > 2:
			m.append(self._doExtractMessage())
		self.callbacks['data'](m)

	def _write13(self, data):
		header = ''	
		header += chr((
						(0x1 << 7)
						| (0 << 6)
						| (0 << 5)
						| (0 << 4)
						| 0x1
					))
		length = len(data)
		mask_bit = 0
		if length < 126:
			header += chr(mask_bit | length)
		elif length < (1 << 16):
			header += chr(mask_bit | 126) + struct.pack('!H', length)
		elif length < (1 << 63):
			header += chr(mask_bit | 127) + struct.pack('!Q', length)
		else:
			# mb too big ?
			raise Exception()
 		self.connection.write(header + data)
	
	# common private methods
	def _onData(self, data):
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
				# Detect protocol
				if self.headers.has_key('Sec-WebSocket-Version'):
					self.version = int(self.headers['Sec-WebSocket-Version'])
				elif self.headers.has_key('Sec-WebSocket-Key1') and self.headers.has_key('Sec-WebSocket-Key2'):
					self.version = 76
				# Handshake with proper version
				if self.version == 13:
					self._doHandshake13()
				elif self.version == 76:
					self._doHandshake76()
				else:
					print "Unknown protocol version", self.headers
					self.connection.close()
		else:
			# process data
			if self.version == 76:
				self._doProcessData76()
			elif self.version == 13: 
				self._doProcessData13()
	
	def _onClose(self):	
		self.callbacks['close']()

	def _onPause(self, pause):
		self.w_paused = pause
		self.callbacks['pause'](pause)
	
	# common public methods
	def write(self, data):
		if self.version == 76:
			self._write76(data)
		elif self.version == 13:
			self._write13(data)

	def close(self):
		self.connection.close()

	def pause(self, pause):
		self.r_paused = pause
		self.connection.pause(pause)
	
	def on(self, event, callback):
		self.callbacks[event] = callback

