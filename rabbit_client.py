import pika
import uuid
import numpy as np
import json

class Client(object):
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
                host='localhost'))
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue
        self.channel.queue_bind(exchange='polygon',queue=self.callback_queue, routing_key=self.callback_queue)
        self.channel.basic_consume(self.on_response, queue=self.callback_queue, no_ack=True)
        
    def readfile(self,filename):
        f = open(filename,'r')
        self.out = f.read()
        #self.out = ''
        f.close()

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='polygon',
                                   routing_key='pumpmodes',
                                   properties=pika.BasicProperties(
                                         reply_to = self.callback_queue,
                                         correlation_id = self.corr_id,
                                         ),
                                   body=self.out)
        print(self.callback_queue, self.corr_id)
        while self.response is None:
            self.connection.process_data_events()
        resp_str=self.response.decode("utf-8")
        print(resp_str)
        return None

rpc = Client()
rpc.readfile("./pumpmodes2/error_input.txt")
print("Requesting")
rpc.call()
