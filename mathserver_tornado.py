# -*- coding: utf-8 -*-
"""
Created on Tue May 10 00:00:53 2016

@author: Artur
"""
import tornado.web
import tornado.ioloop
import tornado.websocket
import tornado.httpserver
import websocket
from datetime import datetime
import uuid
from multiprocessing import Process, cpu_count
from solverslibrary import solvers

import configparser

config = configparser.ConfigParser()
config.read('config.ini')
torn = config['Tornado']

portnum = torn['port']

def solve(solver, message, corr_id):
    if type(message)==str:
        pass
    else:
        message = message.decode('utf-8')
    out = solvers[solver](message)
    ws = websocket.create_connection("ws://localhost:" + portnum + "/mathserver?" + solver + "?" + corr_id)
    ws.send(out)
    ws.close()

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')

class WebSocket(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True
    
    def open(self):
        print("WebSocket opened")
        corr_id = str(uuid.uuid4())
        self.application.webSocketsPool.append([self,corr_id,-1]) #websocket object, correlation_id and worker number

    def on_message(self, message):
        global current
        global workers
        uri = self.ws_connection.request.uri.split('?')
        if len(uri) == 3: #if message is responce then send message to client
            solver = uri[1]
            corr_id = uri[2]
            print('Task for '+solver+' is done at '+str(datetime.now()))
            for key, value in enumerate(self.application.webSocketsPool):
                if value[1] == corr_id:
                    self.application.webSocketsPool[key][0].write_message(message)
                    self.application.webSocketsPool[key][2]= -1
        else: #if message is request for solver then start process
            solver = uri[1]
            print('Request has been received for '+solver+' at '+str(datetime.now()))
            for key, value in enumerate(self.application.webSocketsPool):
                if value[0] == self:
                    current = current + 1
                    if current == nwork: current = 0
                    while workers[current].is_alive(): #find for free worker
                        current = current + 1
                        if current == nwork: current = 0
                    corr_id = self.application.webSocketsPool[key][1]
                    self.application.webSocketsPool[key][2] = current
                    print('Worker No '+str(current)+' has accepted the task for '+solver)
                    workers[current] = Process(target=solve, args=(solver, message, corr_id,))
                    workers[current].start()

    def on_close(self):
        print("WebSocket closed")
        global workers
        for key, value in enumerate(self.application.webSocketsPool): #if connection is closed then kill child process and delete connection from websocket pool 
            if value[0] == self:
                if value[2] != -1 and workers[value[2]].is_alive():
                    workers[value[2]].terminate()
                del self.application.webSocketsPool[key]


class Application(tornado.web.Application):
    def __init__(self):
        self.webSocketsPool = []
        handlers = ((r'/', MainHandler),(r'/mathserver/?', WebSocket),(r'/static/(.*)', tornado.web.StaticFileHandler,{'path': 'static/'}),)
        tornado.web.Application.__init__(self, handlers, debug=True)

nwork = cpu_count()
workers = []
for i in range(nwork):
    workers.append(Process(target=None, args=()))
current = -1

if __name__ == '__main__':
    application = Application()
    print(' Mathserver is running')
    print(' [*] Waiting for websocket connections. To exit press CTRL+C')
    application.listen(int(portnum))
    tornado.ioloop.IOLoop.instance().start()

