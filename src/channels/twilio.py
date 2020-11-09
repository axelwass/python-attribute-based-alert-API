from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from channel_interface import _Channel

class TwilioSmsChannel(_Channel):

	def __init__(self, config):
		self.from_phone = config.twilio.from_phone
		self.client = Client(config.twilio.sid, config.twilio.token)

	def send(self, text, contact):
		if 'phone' not in contact:
			return {'success': False, 'message': "User dose not have a phone number"}
		try:

			message = self.client.messages.create(
					to= contact['phone'],
					body= text,
					from_= self.from_phone
			)
		except TwilioRestException as e:
			return {'success': False, 'message': "Error calling Twilio: {}".format(e.msg)}
		
		return {'success': True, 'contact': contact['phone'], 'message_id': message.sid}
		

class TwilioTtsChannel(_Channel):
	def __init__(self, config):
		self.from_phone = config.twilio.from_phone
		self.client = Client(config.twilio.sid, config.twilio.token)
	
	def send(self, text, contact):
		if 'phone' not in contact:
			return {'success': False, 'message': "User dose not have a phone number"}
			
		try:
			twiml_response = VoiceResponse()
			twiml_response.say(text)
			twiml_response.hangup()
			twiml_xml = twiml_response.to_xml()
			call = self.client.calls.create(
					to=contact['phone'],
					twiml= twiml_xml ,
					from_=self.from_phone
			)
			
		except TwilioRestException as e:
			return {'success': False, 'message': "Error calling Twilio: {}".format(e.msg)}
		
		return {'success': True, 'contact': contact['phone'], 'call_id': call.sid}