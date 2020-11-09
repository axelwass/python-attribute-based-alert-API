from operator import eq
from functools import reduce
from tinydb import Query

ops = {
	"==": eq
}

def eval_element(element,alert):
	if element['object'] == "User":
		return Query()['attributes'][element['value']]
	elif element['object'] == "Alert":
		return alert['attributes'][element['value']]
	else:
		return element['value']

def eval_rule(rule, alert):
	qs = []
	for condition in rule['conditions']:
		first = eval_element(condition['first'], alert)
		second = eval_element(condition['second'], alert)
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
