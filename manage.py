#!/usr/bin/env python

from optparse import OptionParser
from application import app
from views import *

import config

class Main(object):
	def __init__(self):
		self.parser = OptionParser("usage: %prog [options] arg")
		self.parser.add_option("-v", "--verbose", action="store_true", dest="verbose")
		self.parser.add_option("-f", "--force", action="store_true", dest="force")
		(self.options, self.args) = self.parser.parse_args()
	
	def __call__(self):
		actions = []
		for i in Main.__dict__.keys():
			if i.startswith('action'):
				actions.append(i.lstrip('action'))

		if len(self.args) == 0:
			self.parser.error("No action specified\nAvaliabel actions: %s" % ' '.join(actions))

		if self.args[0] not in actions:
			self.parser.error("action %s not supported.\nuse one of that: %s" % (self.args[0], actions))
		else:
			getattr(self, 'action'+self.args[0])(*self.args[1:])

	def actionStartWeb(self):
		app.run()

	def actionStartGS(self):
		from gameserver import GameServer
		gs = GameServer()
		gs.run()
	
if __name__ == '__main__':
	Main()()
