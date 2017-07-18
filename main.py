#!/bin/python3.4

import socket, time, subprocess, os, traceback, queue, threading

import psycopg2, jinja2

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
		for key, value in self.tables.items():
			print(key + ": " + str(value))

class Route(object):
	def __init__(self, method, path, callback, requires={}):
		self.method = method
		self.path = path
		self.callback = callback
		self.requires = requires

class API(object):
	def __init__(self):
		self.directory = util.configuration["public-directory"]
		self.password = util.configuration["api-password"]
		self.port = util.configuration["port"]
		self.running = True

		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.server.bind(("", self.port))
		self.server.listen(util.configuration["number_of_total_connections"])

		self.headers = {
			"Accept-Ranges": "bytes",
			"Content-Type": "text"
		}

		self.routes = {}

		self.queue = queue.Queue(maxsize=util.configuration["number_of_total_connections"])
		self.threads = []

		for i in range(util.configuration["number_of_threads"]):
			thread = threading.Thread(target=self.client_thread)
			thread.setDaemon(True)
			thread.start()
			self.threads.append(thread)

	def route(self, method, path, callback, requires={}):
		self.routes[method + " " + path] = Route(method, path, callback, requires)

	def exit(self):
		self.running = False
		for thread in self.threads:
			thread.join()

	def client_thread(self):
		client_tries = 0
		while self.running:
			try:
				print("Running:" + str(self.running))
				client, address = self.queue.get()
				print(address)
				client.settimeout(10)
				data = client.recv(4096).decode("utf-8")
				if not data:
					client.close()
					break

				print("RECV: " + data)
				lines = data.split("\n")
				print(data.split("\r\n\r\n"))
				http_header = lines[0].split(" ")

				# Default
				response = self.respond("404", "Not Found", "<h1>404 Not Found</h1>")

				if len(http_header) < 3:
					response = self.respond("400", "Bad Request", "<h1>400 Bad Request</h1>")
				else:
					route = http_header[0] + " " + http_header[1]
					clean_path = self.directory + http_header[1].replace("..", "")

					if route in self.routes:
						response = self.respond("200", "OK", self.routes[route].callback())
					elif os.path.isdir(clean_path):
						clean_path = os.path.join(clean_path, "index.html")
					if os.path.isfile(clean_path):
						with open(clean_path, "r") as f:
							response = self.respond("200", "OK", f.read())

				client.send(response.encode("utf-8"))
				client.close()
			except:
				client_tries += 1
				if client_tries > 3:
					break
				traceback.print_exc()

	def respond(self, status, message, content="", headers={}):
		header_text = ""
		for key, value in self.headers.items():
			header_text += key + ": " + value + "\r\n"
		for key, value in headers.items():
			header_text += key + ": " + value + "\r\n"
		return "HTTP/1.1 " + str(status) + " " + message + "\r\n" + header_text + "\r\n\r\n" + content

	def start(self):
		print("API running on port " + str(self.port) + ".")
		print("Routes:")
		for path, route in self.routes.items():
			print("\t" + path)

		server_tries = 0
		while self.running:
			try:
				print(self.running)
				self.queue.put(self.server.accept())
			except:
				server_tries += 1
				if server_tries > 3:
					self.exit()
				traceback.print_exc()

jinja2_env = jinja2.Environment(
	loader=jinja2.FileSystemLoader("jinja2_templates/"),
	autoescape=jinja2.select_autoescape(["html"])
)
def render_template(template, **kwargs):
	return jinja2_env.get_template(template).render(kwargs)

if __name__ == "__main__":
	api = API()

	def procs():
		p = subprocess.Popen("ps -aux", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		o, e = p.communicate()
		return o.decode("utf-8")
	api.route("GET", "/procs", procs)

	def die():
		api.running = False
		return "<h1>Goodbye!</h1>"
	api.route("GET", "/die", die)

	routes_html = render_template("routes.html", routes=api.routes)
	def routes():
		return routes_html
	api.route("GET", "/routes", routes)

	db = DB()

	api.start()
	api.queue.join()
