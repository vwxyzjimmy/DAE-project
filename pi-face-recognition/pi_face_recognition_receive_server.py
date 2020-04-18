import time
import threading
import socket
import sys
import os
import struct
import datetime
from datetime import datetime, timedelta
import mysql.connector

class ClientThread(threading.Thread):
	def __init__(self, num):
		threading.Thread.__init__(self)
		self.num = num
	def run(self):
		host = '140.116.39.249'
		port = 9999
		lastminute_new = datetime.now()
		while True:
			try:
				while True:
					tmp_photo = os.listdir('/home/pi/pi-face-recognition/pi-face-recognition/tmp_photo/')
					#time.sleep(0.05)
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


class ClientHandlerThread(threading.Thread):
	def __init__(self, num, SOCK, ADDR):
		threading.Thread.__init__(self)
		self.num = num
		self.sock = SOCK
		self.addr = ADDR
	def run(self):
		self.sock.settimeout(2)
		save_path = ''
		SIZE = 1024
		try:
			receive = self.sock.recv(SIZE)
			img_name_length = struct.unpack('i',receive[0:4])[0]
			img_name = struct.unpack((str(img_name_length) + 's'),receive[4:4+img_name_length])[0].decode('utf-8')
			data_length = struct.unpack('i',receive[4+img_name_length:8+img_name_length])[0]
			print("Server got:\r\n	img_name_length: {0}\r\n	img_name: {1}\r\n	data_length: {2}".format(img_name_length, img_name, data_length))
			start_rec_time = datetime.now()
			timeoutduration = timedelta(seconds=2)
			if data_length > 0:
				data = bytearray()
				#data.extend(receive[8+img_name_length:])
				#count = len(receive[8+img_name_length:])
				#data = receive[8+img_name_length:]
				save_path = '/home/nclabpc/nclab_photo/' + img_name
				f = open(save_path, 'wb')
				count = 0
				if_time_out = False
				recv_packet_size = 20000
				while (count < data_length):
					if (datetime.now()-start_rec_time) > timeoutduration:
						print("count: {0}, data_length: {1}\r\ntime out in receive".format(count, data_length))
						if_time_out = True
						break
					recv_size = 0
					if((data_length-count) > recv_packet_size):
						recv_size = recv_packet_size
					else:
						recv_size = data_length-count
					recv_data = self.sock.recv(recv_size)
					if(recv_data):
						f.write(recv_data)
						count += len(recv_data)
					#data += recv_data
					#data.extend(recv_data)
					#count = len(data)
				f.close()
				if if_time_out == False:
					#save_path = '/home/nclabpc/nclab_photo/' + img_name
					#save_path = str(os.getcwd()) + '/' + img_name
					print("Server get save_path:\r\b{0}".format(save_path))
				else:
					os.remove(save_path)
					fail_send = "fail"
					self.sock.send(fail_send.encode())
					print("fail img_name : {0}".format(img_name))
					save_path = ''
				if save_path != '':
					detect_command = save_path + "|" + str(self.addr)
					s_detect_command = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					s_detect_command.settimeout(2)
					s_detect_command.connect(('127.0.0.1', 9998))
					s_detect_command.send(detect_command.encode())
					got_rec_people = s_detect_command.recv(SIZE).decode()
					print("got_rec_people: {0}".format(got_rec_people))
					s_detect_command.close()
					tmp = img_name.split("_")
					Device = tmp[0]
					Time = tmp[1] + " " + tmp[2][:8]
					check_msg = tmp[2][8:]
					tmp = got_rec_people.split(" ")
					People_Count = int(tmp[0])
					if check_msg == "-check.png":
						got_rec_people = str(People_Count)
					self.sock.send(got_rec_people.encode())
					print("sock.send(got_rec_people.encode()): {0}".format(got_rec_people))
			else:
				print("receive: {0}, img_name_length: {1}, img_name: {2}, data_length: {3}".format(receive, img_name_length, img_name, data_length))
				print("time: {0}".format(img_name))
		except:
			print("except in ClientHandlerThread")
		self.sock.close()


class ServerThread(threading.Thread):
	def __init__(self, num):
		threading.Thread.__init__(self)
		self.num = num
	def run(self):
		global dot_count
		dot_count = 0
		nclab_people = mysql.connector.connect(host = "127.0.0.1", user = "root", password = "nckuesnclabdb", database = "DAE")
		cursor=nclab_people.cursor()
		while True:
			while True:
				#print("start server")
				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				s.bind(('140.116.39.249', 9999))
				#s.bind(('192.168.11.4', 9999))

				#print("start server ip: {0}:{1}".format('192.168.11.30', 9999))
				s.listen(10)
				s.settimeout(2)
				#print('Server socket accept')
				thread_count = 3
				while True:
					try:
						sock, addr = s.accept()
						thread_count += 1
						ClientHandlerThread(thread_count, sock, addr).start()
						'''
						sock.settimeout(2)
						save_path = ''
						SIZE = 1024

						receive = sock.recv(SIZE)
						img_name_length = struct.unpack('i',receive[0:4])[0]
						img_name = struct.unpack((str(img_name_length) + 's'),receive[4:4+img_name_length])[0].decode('utf-8')
						data_length = struct.unpack('i',receive[4+img_name_length:8+img_name_length])[0]
						#print("Server got:\r\n	img_name_length: {0}\r\n	img_name: {1}\r\n	data_length: {2}".format(img_name_length, img_name, data_length))
						start_rec_time = datetime.now()
						timeoutduration = timedelta(seconds=2)
						if data_length > 0:
							data = bytearray()
							#data.extend(receive[8+img_name_length:])
							#count = len(receive[8+img_name_length:])
							#data = receive[8+img_name_length:]
							save_path = '/home/nclabpc/nclab_photo/' + img_name
							f = open(save_path, 'wb')
							count = 0
							if_time_out = False
							recv_packet_size = 20000
							while (count < data_length):
								if (datetime.now()-start_rec_time) > timeoutduration:
									print("count: {0}, data_length: {1}\r\ntime out in receive".format(count, data_length))
									if_time_out = True
									break
								recv_size = 0
								if((data_length-count) > recv_packet_size):
									recv_size = recv_packet_size
								else:
									recv_size = data_length-count
								recv_data = sock.recv(recv_size)
								if(recv_data):
									f.write(recv_data)
									count += len(recv_data)
								#data += recv_data
								#data.extend(recv_data)
								#count = len(data)
							f.close()
							if if_time_out == False:
								#save_path = '/home/nclabpc/nclab_photo/' + img_name
								#save_path = str(os.getcwd()) + '/' + img_name
								print("Server get save_path:\r\b{0}".format(save_path))
							else:
								os.remove(save_path)
								fail_send = "fail"
								sock.send(fail_send.encode())
								print("fail img_name : {0}".format(img_name))
								#time.sleep(0.5)
								save_path = ''
							if save_path != '':
								detect_command = save_path + "|" + str(addr)
								s_detect_command = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
								s_detect_command.settimeout(2)
								s_detect_command.connect(('127.0.0.1', 9998))
								s_detect_command.send(detect_command.encode())
								got_rec_people = s_detect_command.recv(SIZE).decode()
								print("got_rec_people: {0}".format(got_rec_people))
								s_detect_command.close()
								tmp = img_name.split("_")
								Device = tmp[0]
								Time = tmp[1] + " " + tmp[2][:8]
								check_msg = tmp[2][8:]
								tmp = got_rec_people.split(" ")
								People_Count = int(tmp[0])
								if check_msg == "-check.png":
									got_rec_people = str(People_Count)
								sock.send(got_rec_people.encode())
								print("sock.send(got_rec_people.encode()): {0}".format(got_rec_people))

						else:
							print("receive: {0}, img_name_length: {1}, img_name: {2}, data_length: {3}".format(receive, img_name_length, img_name, data_length))
							print("time: {0}".format(img_name))
						'''
					except Exception as e:
						print('                                                 ', end='\r')
						error_text = "Exception: " + str(e) + ", reconnecting "
						for i in range(dot_count):
							error_text = error_text + "."
						dot_count = dot_count + 1
						if dot_count > 3:
							dot_count = 0
						print(error_text, end='\r')

				s.close()


print('receive_socket')
receive_socket = ServerThread(0)
receive_socket.start()
print('recv_socket start')

while True:
	time.sleep(1)
