#!/bin/python

import socket, time, subprocess, os

class API(object):
  def __init__(self, directory, password):
    self.directory = directory
    self.password = password

    self.running = True

    self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.server.bind(("", 4096))
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
    self.routes[method + path] = callback;
    
  def start(self):
    print "API running on port 4096."
    print "Routes:"
    for key, value in self.routes.iteritems():
      print "\t" + key
    while self.running:
      try:
        self.server.settimeout(10)
        client, address = self.server.accept()
        print "Connection from " + address
        client.settimeout(10)
        data = client.recv(4096)
        if not data:
          client.close()
          continue
	print "RECV: " + data
        lines = data.split("\n")
        init = lines[0].split(" ")
        if len(init) < 3:
          response = self.respond(400, "Bad Request", "<h1>400 Bad Request</h1>")
        else:
          route = init[0] + init[1]
          clean_path = self.directory + init[1].replace("..", "")
          if route in self.routes:
            response = self.respond(200, "OK", self.routes[route]())
          elif os.path.isfile(clean_path):
            with open(clean_path, "r") as f:
              response = self.respond(200, "OK", f.read())
          else:
            reponse = self.respond(404, "Not Found", "<h1>404 Not Found</h1>")
        client.send(response)
        client.close()
      except Exception as e:
        raise e

if __name__ == "__main__":
  api = API("./", "aq12ws")
  
  def procs():
    p = subprocess.Popen("ps -aux", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    o, e = p.communicate()
    return o

  api.route("GET", "/procs", procs)

  def die(content):
    if content == api.password:
      api.running = false
      return "Goodbye!"
    return "I'm alive!"
    
  api.route("POST", "/die", die)

  api.start()
  
