import socket, time, subprocess

class API(object)
  def __init__(self, directory, password):
    self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.server.bind(("", 4096))
    self.server.listen(10)
  
    self.headers = {
      "Accept-Ranges": "bytes",
      "Content-Type": "text"
    }
    
    self.routes = {}
  
  def response(self, status, message, content, headers=):
  
  
  def route(self, method, path, callback):
    self.routes[method + path] = callback;
    
  def start(self):
    while True:
      time.sleep(10)
      try:
        self.server.settimeout(10)
        client, address = self.server.accept()
        print "Connection from " + address
        client.settimeout(10)
        data = client.recv(4096)
        if not data:
          client.close()
          continue
        lines = data.split("\n")
        init = lines[0].split(" ")
        if len(init) < 3:
          
      except Exception as e:
        print e
        continue

if __name__ == "__main__":
  api = API("./", "aq12ws")
  
  def procs():
    p = subprocess.Popen("ps -aux", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    o, e = p.communicate()
    return o
    
  api.route("GET", "/procs", procs)
  
  api.start()
  
