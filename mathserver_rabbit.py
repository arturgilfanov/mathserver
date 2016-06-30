import pika
from multiprocessing import Process, freeze_support, cpu_count
from datetime import datetime
from solverslibrary import solvers
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
rabbit = config['Rabbit']

hostname = rabbit['host']
portnum = int(rabbit['port'])
exchange_name = rabbit['exchange']
username = rabbit['username']
password = rabbit['password']

def solve(solver, message, parameters):
    if type(message)==str:
        pass
    else:
        message = message.decode('utf-8')
    f=open('./io_json/'+solver+str(parameters[2])+'.txt','w')
    f.write(message)
    f.close()
    out = solvers[solver](message)
    credentials = pika.PlainCredentials(username, password)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=hostname, port=portnum, credentials=credentials))
    channel=connection.channel()
    channel.basic_publish(exchange=exchange_name,
                          routing_key=parameters[0],
                          properties=pika.BasicProperties(correlation_id=parameters[1]), body=out)
    connection.close()
    f=open('./io_json/'+solver+str(parameters[2])+'_out.txt','w')
    f.write(out)
    f.close()
    print('Task for '+solver+' is done at '+str(datetime.now()))

nwork = cpu_count()
workers = []
for i in range(nwork):
    workers.append(Process(target=None, args=()))
current = -1

def callback(ch, method, properties, body):
    solver = method.routing_key
    print('Request has been received for '+solver+' at '+str(datetime.now()))
    global current
    global workers
    current = current + 1
    if current == nwork: current = 0
    parameters=[properties.reply_to, properties.correlation_id, current]
    while workers[current].is_alive():
        current = current + 1
        if current == nwork: current = 0
    workers[current] = Process(target=solve, args=(solver, body, parameters,))
    print('Worker No '+str(current)+' has accepted the task for '+solver)
    workers[current].start()

if __name__ == '__main__':
    freeze_support()
    credentials = pika.PlainCredentials(username, password)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=hostname, port=portnum, credentials=credentials))
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange_name,type='direct')
    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue
    for key in solvers.keys():
        channel.queue_bind(exchange=exchange_name,
                           queue=queue_name,
                           routing_key=key)
    channel.basic_consume(callback,queue=queue_name, no_ack=True)
    print(' Mathserver is running ')
    print(' [*] Waiting for messages from RabbitMQ. To exit press CTRL+C')
    channel.start_consuming()
