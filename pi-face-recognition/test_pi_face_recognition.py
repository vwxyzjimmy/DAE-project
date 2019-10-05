import time
import threading
import socket
import sys
import os
import struct

class ClientThread(threading.Thread):
	def __init__(self, num):
		threading.Thread.__init__(self)
		self.num = num
	def run(self):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		host = '192.168.137.1'
		port = 9999
		print('Client socket create 1')
		s.connect((host, port))
		print('Client socket connect')
		fhead = 'test messege'
		#while True:
		s.send(fhead.encode())
		print('Client s.send(fhead)')


class ServerThread(threading.Thread):
	def __init__(self, num):
		threading.Thread.__init__(self)
		self.num = num
	def run(self):
		print("start server")
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		print('Server socket create 0')
		s.bind(('192.168.137.1', 9999))
		print('Server socket bind')
		s.listen(5)
		print('Server socket listen')
		sock, addr = s.accept()
		print('Server socket accept')
		save_path = ''
		#while True:
		SIZE = 1024
		receive = sock.recv(SIZE)
		print('Server sock.recv(SIZE) : {0}'.format(receive.decode()))


receive_socket = ServerThread(0)
receive_socket.start()

#send_socket = ClientThread(0)
#send_socket.start()

while True:
	time.sleep(1)
