from channels import *
import pkgutil
import inspect
from channel_interface import _Channel

class ChannelCollection(object):
	def __init__(self, config):
		self.channels = {cls.__name__: cls(config) for cls in _Channel.__subclasses__()}
	
	def send_channel(self, name, text, contact):
		if name not in self.channels:
			return {'success': False, 'message': "Channel with name {} not found. Available channels:.".format(name, self.channels.keys())}
		return self.channels[name].send(text, contact)
