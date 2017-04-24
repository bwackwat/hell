import json

configuration = {}

with open("configuration.json", "r") as file:
	global configuration
	configuration= json.loads(file.read())