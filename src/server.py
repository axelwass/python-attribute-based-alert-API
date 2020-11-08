from functools import reduce
from flask import Flask, request, jsonify, render_template
#from twilio.rest import Client
from flask_json_schema import JsonSchema, JsonValidationError
from flask_swagger import swagger
from tinydb import TinyDB, Query

from operator import eq, contains


db = TinyDB('./db/data.json', create_dirs=True)
#client = Client('TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN')
app = Flask(__name__)
schema = JsonSchema(app)

users_db = db.table('users')
user_schema = {
    'type': 'object',
    'additionalProperties': False,
    'required': ['username'],
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

chanels_db = db.table('chanels')
chanel_schema = {
    'type': 'object',
    'additionalProperties': False,
    'required': ['id', 'min_severity', 'module'],
    'properties': {
        'id': { 'type': 'string' },
		'min_severity': {
			'type': 'number',
			'minimum': 0,
			'maximum': 100
		},
        'module': { 'type': 'string' }
    }
}

@app.errorhandler(JsonValidationError)
def validation_error(e):
    return jsonify({ 'error': e.message, 'errors': [validation_error.message for validation_error  in e.errors]}), 400


def crud_collection(db, id):
	if request.method == 'POST':
		req_data = request.get_json()
		if db.contains(Query()[id] == req_data[id]):
			return jsonify({'success':False, 'message': "Object with id '{}' already exists.".format(req_data[id])}), 409,  {'ContentType':'application/json'} 
		else:
			db.insert(req_data)
			return jsonify({'success':True}), 201, {'ContentType':'application/json'}
	elif request.method == 'GET':
		return jsonify(db.all()), 200, {'ContentType':'application/json'} 


def crud_element(db, id, id_value):
	if not db.contains(Query()[id] == id_value):
		return jsonify({'success':False, 'message': "Object with id '{}' dose not exists.".format(id_value)}), 404,  {'ContentType':'application/json'} 
	if request.method == 'POST':
		req_data = request.get_json()
		db.upsert(req_data, Query()[id] == id_value)
		return jsonify({'success':True}), 200, {'ContentType':'application/json'}
	elif request.method == 'GET':
		return jsonify(db.get(Query()[id] == id_value)), 200, {'ContentType':'application/json'} 
	elif request.method == 'DELETE':
		db.remove(Query()[id] == id_value)
		return jsonify({'success':True}), 200, {'ContentType':'application/json'}


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
	return crud_element(rules_db, "id",id)

@app.route('/models/chanels', methods=['POST','GET'])
@schema.validate(chanel_schema)
def chanels():
	return crud_collection(chanels_db, "id")


@app.route('/models/chanels/<string:id>', methods=['POST','GET', 'DELETE'])
@schema.validate(chanel_schema)
def chanel(id):
	return crud_element(chanels_db, "id",id)
	
@app.route('/alerts/<string:id>/dryrun', methods=['POST'])
def alert_dryrun(id):
	all_args = request.args.to_dict()
	if not alerts_db.contains(Query()["id"] == id):
		return jsonify({'success':False, 'message': "Object with id '{}' dose not exists.".format(id)}), 404,  {'ContentType':'application/json'} 
	alert = alerts_db.get(Query()["id"] == id)
	alert['attributes'].update(all_args)
	rules = rules_db.all()
	
	users = []
	for rule in rules:
		query = parse_rule(rule, alert)
		users.append(users_db.get(query))
	chanels = chanels_db.get(Query()['min_severity'] <= alert['attributes']['severity'])
	return jsonify({"alert": alert,"users":users, "chanels": chanels}), 200, {'ContentType':'application/json'}

	
	
# --- Rule Parser!
ops = {
	"==": eq
}

def parse_element(element,alert):
	if element['object'] == "User":
		return Query()['attributes'][element['value']]
	elif element['object'] == "Alert":
		return alert['attributes'][element['value']]
	else:
		return element['value']

def parse_rule(rule, alert):
	qs = []
	for condition in rule['conditions']:
		first = parse_element(condition['first'], alert)
		second = parse_element(condition['second'], alert)
		if condition['op'] == 'contains':
			if condition['first']['object'] == 'User' and condition['second']['object'] != 'User':
				qs.append(first.any(second))
			elif condition['first']['object'] != 'User' and condition['second']['object'] == 'User':
				qs.append(second.one_of(first))
			else:
				return where(None)
		else:
			opf = ops.get(condition['op'], None)
			if opf is None:
				return where(None)
			qs.append(opf(first, second))
	return reduce(lambda a, b: a & b, qs)


if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)