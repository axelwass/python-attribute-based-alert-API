from flask import request, jsonify
from tinydb import Query

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