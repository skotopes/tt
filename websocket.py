from hashlib import sha1, md5
from base64 import b64encode
import struct

class WebSocket(object):
	def __init__(self, connection):
		super(WebSocket, self).__init__()
		# Protocol internals
		self.method = None
		self.version = None
		self.headers = None
		self.handshaked = False
		self.data_buffer = ''
		self.msg_buffer = ''
		self.messages = []
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
		# crafting response
		response = 'HTTP/1.1 101 WebSocket Protocol Handshake\r\n'
		response += 'Upgrade: WebSocket\r\n'
		response += 'Connection: Upgrade\r\n'
		response += 'Sec-WebSocket-Origin: %s\r\n' % self.headers['Origin']
		response += 'Sec-WebSocket-Location: ws://%s/\r\n' % self.headers['Host'].strip()
		response += 'Sec-WebSocket-Protocol: sample\r\n'
		response += '\r\n'
		response += sign
		self.connection.write(response)
		self.handshaked = True
		self.data_buffer = ''

	def _doProcessData76(self):
		# \x00test\xff
		cnt = self.data_buffer.count('\xff')
		while(cnt>0):
			cnt-=1
			p = self.data_buffer.find('\xff') + 1
			self.messages.append(self.data_buffer[0:p].lstrip('\x00').rstrip('\xff'))
			self.data_buffer = self.data_buffer[p:]

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
		# Craft respnse
		response = 'HTTP/1.1 101 Switching Protocols\r\n'
		response += 'Upgrade: websocket\r\n'
		response += 'Connection: Upgrade\r\n'
		response += 'Sec-WebSocket-Accept: %s\r\n' % step2
		# chrome v20 strict
		if self.headers.has_key('Sec-WebSocket-Protocol'):
			response += 'Sec-WebSocket-Protocol: chat\r\n'
		response += '\r\n'
		self.connection.write(response)
		self.handshaked = True
		self.data_buffer = ''
	
	def _doMask13(self, data, mask_key):
		masked = bytearray(data)
		key = map(ord, mask_key)
		for i in range(len(data)):
			masked[i] = masked[i] ^ key[i%4]
		return masked
	
	def _doExtractMessage13(self):
		# First byte
		# Extract payload description
		ptr = 0
		first_byte = ord(self.data_buffer[ptr])
		fin = (first_byte >> 7) & 1
		rsv1 = (first_byte >> 6) & 1
		rsv2 = (first_byte >> 5) & 1
		rsv3 = (first_byte >> 4) & 1
		opcode = first_byte & 0xf
		if fin not in [0, 1]:
			raise Exception("websocket 13: fin wtf?")
		if rsv1 or rsv2 or rsv3:
			raise Exception("websocket 13: rsv not zero")
		if 2 < opcode < 8 or opcode > 0xA:
			raise Exception("websocket 13: invalid opcode")
		if opcode > 0x7 and fin == 0:
			raise Exception("websocket 13: invalid fin/opcode combination")
		ptr += 1
		
		# Second byte
		# Extract payload length and masking bit
		second_byte = ord(self.data_buffer[ptr])
		mask = (second_byte >> 7) & 1
		payload_length = second_byte & 0x7f
		if opcode > 0x7 and payload_length > 125:
			raise Exception("websocket 13: invalid opcode/payload length combination")
		ptr += 1
		
		# Insuring that we got enougth data to extract payload
		length = 0
		if 0 < payload_length < 125:
			length = payload_length
		elif payload_length == 126:
			if len(self.data_buffer[ptr:]) < 2:
				return False
			length = struct.unpack('!H', self.data_buffer[ptr:ptr+2])[0]
			ptr += 2
		elif payload_length == 126:
			if len(self.data_buffer[ptr:]) < 8:
				return False
			length = struct.unpack('!Q', self.data_buffer[ptr:ptr+8])[0]
			ptr += 8
		else:
			raise Exception("websocket 13: programming error, payload length != 7 bit")
		
		# Extract masking key
		if mask:
			if len(self.data_buffer[ptr:]) < 4:
				return False
			key = self.data_buffer[ptr:ptr+4]
			ptr += 4
		
		# Do we have something interesting?
		prepend = None
		if opcode == 0x8: # close
			prepend = 'close'
			self.close()
		elif opcode == 0x9: # ping
			prepend = 'ping'
		elif opcode == 0xA: # pong
			prepend = 'pong'
		
		if length > 0:
			if len(self.data_buffer[ptr:]) < length:
				return False
			if mask:
				self.msg_buffer += self._doMask13(self.data_buffer[ptr:ptr+length], key)
			else:
				self.msg_buffer += self.data_buffer[ptr:ptr+length]
			ptr += length
		
			if fin:
				if prepend:
					self.messages.append(prepend + ':' + self.msg_buffer)
				else:
					self.messages.append(self.msg_buffer)
				self.msg_buffer = ''
		
		# Ok, one more time?
		self.data_buffer = self.data_buffer[ptr:]
		return True
	
	def _doProcessData13(self):
		while len(self.data_buffer) > 2:
			if not self._doExtractMessage13():
				break

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
			raise Exception("websocket 13: data too big")
		self.connection.write(header + data)
	
	# common private methods
	def _extractHeaders(self):
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
		
		self.write = getattr(self, '_write%d' % self.version)
		self._doHandshake = getattr(self, '_doHandshake%d' % self.version)
		self._doProcessData = getattr(self, '_doProcessData%d' % self.version)
	
	_doHandshake = None
	
	_doProcessData = None
	
	def _onData(self, data):
		self.data_buffer += data
		try:
			if self.handshaked == False:
				if self.headers == None and self.data_buffer.find('\r\n\r\n') != -1:
					self._extractHeaders()
					self._doHandshake()
			else:
				self._doProcessData()
				# callbacks
				if len(self.messages) > 0:
					self.callbacks['data'](self.messages)
					self.messages = []
		except Exception, e:
			print 'websocket protocol error', e
			self.connection.close()
	
	def _onClose(self):	
		self.callbacks['close']()

	def _onPause(self, pause):
		self.w_paused = pause
		self.callbacks['pause'](pause)
	
	# common public methods
	write = None
	
	def close(self):
		self.connection.close()
	
	def pause(self, pause):
		self.r_paused = pause
		self.connection.pause(pause)
	
	def on(self, event, callback):
		self.callbacks[event] = callback
