#!/bin/python

import socket, time, subprocess, os, traceback

import psycopg2

import util

class DB(object):
	def execute(self, sql):
		cursor = self.connection.cursor()
		cursor.execute(sql)
		items = cursor.fetchall()
		return items

	def __init__(self):
		self.connection = psycopg2.connect(
			host="localhost",
			user=util.configuration["pgadmin"],
			password=util.configuration["pgpassword"],
			database=util.configuration["pgdb"]
		)
		self.tables = {}
		for table in self.execute("SELECT * FROM pg_tables;"):
			if table[0] == "public":
				self.tables[table[1]] = [table_columns[3] for table_columns in self.execute("SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '" + table[1] + "';")]
		for key, value in self.tables.iteritems():
			print key + ": " + str(value)

class API(object):
	def __init__(self):
		self.directory = util.configuration["public-directory"]
		self.password = util.configuration["api-password"]
		self.port = util.configuration["port"]
		self.running = True

		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.server.bind(("", self.port))
		self.server.listen(10)

		self.headers = {
			"Accept-Ranges": "bytes",
			"Content-Type": "text"
		}

		self.routes = {}

	def respond(self, status, message, content="", headers={}):
		header_text = ""
		for key, value in self.headers.iteritems():
			header_text += key + ": " + value + "\r\n"
		for key, value in headers.iteritems():
			header_text += key + ": " + value + "\r\n"
		return "HTTP/1.0 " + status + " " + message + "\r\n" + header_text + "\r\n\r\n" + content

	def route(self, method, path, callback):
		self.routes[method + " " + path] = callback

	def start(self):
		print "API running on port " + str(self.port) + "."
		print "Routes:"
		client_tries = 0
		for key, value in self.routes.iteritems():
			print "\t" + key
		while self.running:
			try:
				client, address = self.server.accept()
				print address
				client.settimeout(10)
				data = client.recv(4096)
				if not data:
					client.close()
					continue
				print "RECV: " + data
				lines = data.split("\n")
				print data.split("\r\n\r\n")
				init = lines[0].split(" ")

				# Default
				response = self.respond("404", "Not Found", "<h1>404 Not Found</h1>")
				if len(init) < 3:
					response = self.respond("400", "Bad Request", "<h1>400 Bad Request</h1>")
				else:
					route = init[0] + " " + init[1]
					clean_path = self.directory + init[1].replace("..", "")
					if route in self.routes:
						response = self.respond("200", "OK", self.routes[route]())
					elif os.path.isdir(clean_path):
						clean_path = os.path.join(clean_path, "index.html")
					if os.path.isfile(clean_path):
						with open(clean_path, "r") as f:
							response = self.respond("200", "OK", f.read())
				client.send(response)
				client.close()
			except:
				client_tries += 1
				if client_tries > 3:
					self.running = False
				traceback.print_exc()

if __name__ == "__main__":
	api = API()

	def procs():
		p = subprocess.Popen("ps -aux", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		o, e = p.communicate()
		return o

	api.route("GET", "/procs", procs)

	def die(content):
		if content == api.password:
			api.running = False
			return "Goodbye!"
		return "I'm alive!"

	api.route("GET", "/die", die)

	db = DB()

	api.start()
