import time
import threading
import socket
import sys
import os
import struct
import datetime
from datetime import datetime, timedelta

class ClientThread(threading.Thread):
	def __init__(self, num):
		threading.Thread.__init__(self)
		self.num = num
	def run(self):
		host = '140.116.179.183'
		port = 9999
		lastminute_new = datetime.now()
		while True:
			try:
				while True:
					tmp_photo = os.listdir('/home/pi/pi-face-recognition/pi-face-recognition/tmp_photo/')
					time.sleep(0.5)
					if (len(tmp_photo) > 0):
						print('len(tmp_photo): {0}'.format(len(tmp_photo)))
						time.sleep(1)
						for i in range(len(tmp_photo)):
							photo_dir = '/home/pi/pi-face-recognition/pi-face-recognition/tmp_photo/' + str(tmp_photo[i])
							img_name = str(tmp_photo[i])
							img_name_length = len(img_name)
							print('Client send img_name: {0}'.format(img_name))
							f = open(photo_dir, 'rb')
							data = f.read()
							data_length = f.tell()
							f.close()
							os.remove(photo_dir)

							pack_img_name_length = struct.pack('i', img_name_length)
							form_1 = str(img_name_length) + 's'
							pack_img_name = struct.pack(form_1, img_name.encode('utf-8'))
							pack_data_length = struct.pack('i', data_length)
							info = pack_img_name_length + pack_img_name + pack_data_length
							fhead = info + data

							s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
							s.connect((host, port))
							s.send(fhead)
							print('Client send fhead')
							s.close()
					else:
						#print("nowtime")
						nowtime = datetime.now()
						#print("nowtime.strftime: {0}".format(nowtime.strftime('%Y-%m-%d %H:%M:%S')))
						tmp = nowtime - lastminute_new
						#print("lastminute_new.strftime: {0}".format(lastminute_new.strftime('%Y-%m-%d %H:%M:%S')))
						if ((nowtime - lastminute_new) > timedelta(minutes=1)):
							#print("test")
							lastminute_new = nowtime
							send_time = nowtime.strftime('%Y-%m-%d %H:%M:%S')
							time_length = len(send_time)
							print("send_time: {0}, time_length: {1}".format(send_time, time_length))
							pack_time_length = struct.pack('i', time_length)
							form_1 = str(time_length) + 's'
							pack_time = struct.pack(form_1, send_time.encode('utf-8'))
							data_length = 0
							pack_data_length = struct.pack('i', data_length)
							info = pack_time_length + pack_time + pack_data_length
							print("info: {0}, pack_time_length: {1}, pack_time: {2}, pack_data_length: {3}".format(info, pack_time_length, pack_time, pack_data_length))

							s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
							s.connect((host, port))
							s.send(info)
							print('Client send fhead')
							s.close()
						pass
			except:
				print('reconnecting...')

class ServerThread(threading.Thread):
	def __init__(self, num):
		threading.Thread.__init__(self)
		self.num = num
	def run(self):
		while True:
			while True:
				#print("start server")
				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				s.bind(('140.116.179.183', 9999))
				#s.bind(('192.168.11.4', 9999))

				#print("start server ip: {0}:{1}".format('192.168.11.30', 9999))
				s.listen(5)
				s.settimeout(10)
				#print('Server socket accept')
				save_path = ''
				SIZE = 1024
				while True:
					try:
						sock, addr = s.accept()
						receive = sock.recv(SIZE)
						print("addr: {0}".format(str(addr)))
						img_name_length = struct.unpack('i',receive[0:4])[0]
						img_name = struct.unpack((str(img_name_length) + 's'),receive[4:4+img_name_length])[0].decode('utf-8')
						print('Server img_name: {0}'.format(img_name))
						data_length = struct.unpack('i',receive[4+img_name_length:8+img_name_length])[0]
						if data_length > 0:
							count = len(receive[8+img_name_length:])
							data = receive[8+img_name_length:]
							while (count < data_length):
								data += sock.recv(SIZE)
								count = len(data)
							save_path = '/home/nclabpc/nclab_photo/' + img_name
							#save_path = str(os.getcwd()) + '/' + img_name
							print("Server get save_path: {0}".format(save_path))
							if save_path != '':
								f = open(save_path, 'wb')
								f.write(data)
								print("Server write data")
								f.close()
								detect_command = save_path + ":" + str(addr)
								print("detect_command: {0}".format(detect_command))

								s_detect_command = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
								s_detect_command.connect(('127.0.0.1', 9998))
								s_detect_command.send(detect_command.encode())
								got_rec = s_detect_command.recv(SIZE).decode()
								print("got_rec: {0}".format(got_rec))
								s_detect_command.close()

						else:
							print("receive: {0}, img_name_length: {1}, img_name: {2}, data_length: {3}".format(receive, img_name_length, img_name, data_length))
							print("time: {0}".format(img_name))

						'''
						count = len(receive[8+img_name_length:])
						data = receive[8+img_name_length:]
						while (count < data_length):
							data += sock.recv(SIZE)
							count = len(data)

						save_path = 'D:/nclab_photo/' + img_name
						#save_path = str(os.getcwd()) + '/' + img_name
						print("Server get save_path: {0}".format(save_path))
						if save_path != '':
							f = open(save_path, 'wb')
							f.write(data)
							print("Server write data")
							f.close()
						'''
					except:
						print('reconnecting')

				s.close()


print('receive_socket')
receive_socket = ServerThread(0)
receive_socket.start()
print('recv_socket start')

while True:
	time.sleep(1)
