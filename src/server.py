import sys
import json

from flask import Flask, request, jsonify, render_template
from flask_json_schema import JsonSchema, JsonValidationError
from flasgger import Swagger
from tinydb import TinyDB, Query
from jinja2 import BaseLoader, Environment
from python_json_config import ConfigBuilder


from channel_collection import ChannelCollection
from rule_evaluator import eval_rule
from crud import crud_collection, crud_element

builder = ConfigBuilder()
builder.merge_with_env_variables(["PAPAA"])
config = builder.parse_config('configs/config.json')

channel_collection = ChannelCollection(config)

db = TinyDB(config.db.path, create_dirs=True)
app = Flask(__name__)
schema = JsonSchema(app)
swagger = Swagger(app)


users_db = db.table('users')
user_schema = {
    'type': 'object',
    'additionalProperties': False,
    'required': ['username', 'attributes', 'contact'],
    'properties': {
        'username': { 'type': 'string' },
		'contact': { 'type': 'object' },
        'attributes': { 'type': 'object' }
    }
}

alerts_db = db.table('alerts')
alert_schema = {
    'type': 'object',
    'additionalProperties': False,
    'required': ['id','template'],
    'properties': {
        'id': { 'type': 'string' },
        'template': { 'type': 'string' },
        'attributes': {
			'type': 'object', 
			'required': ['severity'],
			'properties': {
				'severity': {
					'type': 'number',
					'minimum': 0,
					'maximum': 100
				}
			}
		}
    }
}

rules_db = db.table('rules')
rule_schema = {
    'type': 'object',
    'additionalProperties': False,
    'required': ['id'],
    'properties': {
        'id': { 'type': 'string' },
        'conditions': {
            'type': 'array',
            'items':{
                'type': 'object',
                'additionalProperties': False,
                'required': ['first','op','second'],
                'properties': {
					'first': { 
						'type': 'object',
						'additionalProperties': False,
						'required': ['object','value'],
						'properties': {
							'object': { 
								'type': 'string',
								'enum': ["Alert", "User", "Value"]
							},
							'value': { 'type': 'string' }
						}
					},
					'op': { 
						'type': 'string',
						'enum': ["contains","=="]
					},
					'second': { 
						'type': 'object',
						'additionalProperties': False,
						'required': ['object','value'],
						'properties': {
							'object': { 
								'type': 'string',
								'enum': ["Alert", "User", "Value"]
							},
							'value': { 'type': 'string' }
						}
					}
				}
			}
        }
    }
}

channels_db = db.table('channels')
channel_schema = {
    'type': 'object',
    'additionalProperties': False,
    'required': ['id', 'min_severity', 'channel'],
    'properties': {
        'id': { 'type': 'string' },
		'min_severity': {
			'type': 'number',
			'minimum': 0,
			'maximum': 100
		},
        'channel': { 'type': 'string' }
    }
}

@app.errorhandler(JsonValidationError)
def validation_error(e):
    return jsonify({ 'error': e.message, 'errors': [validation_error.message for validation_error  in e.errors]}), 400


@app.route('/models/users', methods=['POST','GET'])
@schema.validate(user_schema)
def users():
	return crud_collection(users_db, "username")


@app.route('/models/users/<string:username>', methods=['POST','GET', 'DELETE'])
@schema.validate(user_schema)
def user(username):
	return crud_element(users_db, "username",username)

@app.route('/models/alerts', methods=['POST','GET'])
@schema.validate(alert_schema)
def alerts():
	return crud_collection(alerts_db, "id")


@app.route('/models/alert/<string:id>', methods=['POST','GET', 'DELETE'])
@schema.validate(alert_schema)
def alert(id):
	return crud_element(alerts_db, "id",id)

@app.route('/models/rules', methods=['POST','GET'])
@schema.validate(rule_schema)
def rules():
	return crud_collection(rules_db, "id")


@app.route('/models/rules/<string:id>', methods=['POST','GET', 'DELETE'])
@schema.validate(rule_schema)
def rule(id):
	return crud_element(rules_db, "channel",id)

@app.route('/models/channels', methods=['POST','GET'])
@schema.validate(channel_schema)
def channels():
	return crud_collection(channels_db, "channel")


@app.route('/models/channels/<string:channel>', methods=['POST','GET', 'DELETE'])
@schema.validate(channel_schema)
def channel(channel):
	return crud_element(channels_db, "channel",channel)


@app.route('/alerts/<string:id>/dryrun', methods=['POST'])
def alert_dryrun(id):
	return _alert_trigger(id, lambda ch,t,c:  { 'channel': ch,'text': t,'contact': c})

@app.route('/alerts/<string:id>/trigger', methods=['POST'])
def alert_trigger(id):
	return _alert_trigger(id, lambda ch,t,c:  channel_collection.send_channel(ch,t,c))

def _alert_trigger(id, trigger):
	all_args = request.args.to_dict()
	if not alerts_db.contains(Query()["id"] == id):
		return jsonify({'success':False, 'message': "Object with id '{}' dose not exists.".format(id)}), 404,  {'ContentType':'application/json'} 
	alert = alerts_db.get(Query()["id"] == id)
	alert['attributes'].update(all_args)
	rules = rules_db.all()
	
	users = []
	for rule in rules:
		query = eval_rule(rule, alert)
		users.append(users_db.get(query))
	if not users:
		return jsonify({'success':False, 'message': "No users defined for alert."}), 200,  {'ContentType':'application/json'} 
	
	channel_list = channels_db.search(Query()['min_severity'] <= alert['attributes']['severity'])
	
	results = []
	for user in users:
		for channel in channel_list:
			data = {'alert': alert['attributes'], 'user': user['attributes'], 'channel': channel['channel']}
			text = render_template(alert['template'], data)
			results.append({'channel': channel['channel'], 'result': trigger(channel['channel'],text,user['contact'])})
	return jsonify(results), 200, {'ContentType':'application/json'}

	
def render_template(template, data):
	template_comp = Environment(loader=BaseLoader()).from_string(template)
	return template_comp.render(data)

if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)