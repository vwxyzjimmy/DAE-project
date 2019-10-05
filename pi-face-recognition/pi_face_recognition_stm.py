# USAGE
# python pi_face_recognition.py --cascade haarcascade_frontalface_default.xml --encodings encodings.pickle

# import the necessary packages
from imutils.video import VideoStream
from imutils.video import FPS
import face_recognition
import argparse
import imutils
import pickle
import time
import cv2
import threading
import socket
import sys
import os
import struct
import datetime
from datetime import datetime, timedelta
from PIL import Image
import numpy as np
import struct
import pickle

class ClientThread(threading.Thread):
	def __init__(self, num):
		threading.Thread.__init__(self)
		self.num = num
	def run(self):
		host = '192.168.11.30'
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
			try:
				while True:
					s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					s.bind(('192.168.11.30', 9999))
					s.listen(5)
					s.settimeout(10)
					sock, addr = s.accept()
					save_path = ''

					SIZE = 1024
					receive = sock.recv(SIZE)
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

						save_path = 'D:/nclab_photo/' + img_name
						print("Server get save_path: {0}".format(save_path))
						if save_path != '':
							f = open(save_path, 'wb')
							f.write(data)
							print("Server write data")
							f.close()
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
					s.close()
			except:
				print('reconnecting')

class TestThread(threading.Thread):
	def __init__(self, num):
		threading.Thread.__init__(self)
		self.num = num
	def run(self):
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.bind(('192.168.43.143', 8088))
		SIZE = 1024
		count = 0
		while True:
			receive = ""
			receive, addr = s.recvfrom(SIZE)
			ip = addr[0]
			port = addr[1]
			if len(receive) > 0:
				print("receive.decode(): {0}, ip: {1}, port: {2}".format(receive.decode(), ip, port))
				count = count + 1
			else:
				pass
			if count > 9:
				count = 0
				while True:
					tar_addr = (str(ip), port)
					send_data = []
					#s.sendto(send_data.encode(), tar_addr)
					global img_array
					global img_array_send
					while img_array_send == True:
						pass
					if img_array_send == False:
						count_col = 0
						print("start to send")
						while count_col < 272:
							teset = bytes(img_array[(1440*count_col):1440*(count_col+1)])
							try:
								s.sendto(teset, tar_addr)
								s.settimeout(0.1)
							except:
								pass
							receive = []
							try:
								receive, addr = s.recvfrom(SIZE)
							except:
								pass
							while len(receive) < 1:
								try:
									receive, addr = s.recvfrom(SIZE)
								except:
									try:
										s.sendto(teset, tar_addr)
									except:
										pass
							try:
								if (receive[0:10]).decode() == "show_count":
									receive_show_count = int((receive[11:(len(receive)-2)]).decode())
									print("count_col: {0}".format(count_col))
									count_col = receive_show_count + 1
							except:
								pass

						img_array_send = True
						s.settimeout(None)
		s.close()

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--cascade", required=True,
	help = "path to where the face cascade resides")
ap.add_argument("-e", "--encodings", required=True,
	help="path to serialized db of facial encodings")
args = vars(ap.parse_args())

# load the known faces and embeddings along with OpenCV's Haar
# cascade for face detection
print("[INFO] loading encodings + face detector...")
data = pickle.loads(open(args["encodings"], "rb").read())
detector = cv2.CascadeClassifier(args["cascade"])

# initialize the video stream and allow the camera sensor to warm up
print("[INFO] starting video stream...")
vs = VideoStream(src=0, resolution=(480, 272)).start()
# vs = VideoStream(usePiCamera=True).start()
time.sleep(2.0)

# start the FPS counter
fps = FPS().start()

frame = vs.read()
frame = imutils.resize(frame, width=500)
gray_before = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

'''
print('recv_socket')
recv_socket = ServerThread(0)
recv_socket.start()
print('recv_socket start')
'''

time.sleep(1)

print('send_socket')
send_socket = TestThread(0)
send_socket.start()
print('recv_socket start')
global img_array
global img_array_send
img_array = []
img_array_send = True
# loop over frames from the video file stream
while True:

	# grab the frame from the threaded video stream and resize it
	# to 500px (to speedup processing)
	frame = vs.read()

	frame = imutils.resize(frame, width=480, height=272)

	# convert the input frame from (1) BGR to grayscale (for face
	# detection) and (2) from BGR to RGB (for face recognition)
	rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	'''
	gray_after = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

	gray = gray_after - gray_before
	gray_before = gray_after

	kernel_5 = cv2.getStructuringElement(cv2.MORPH_RECT,(5, 5))
	kernel_13 = cv2.getStructuringElement(cv2.MORPH_RECT,(13, 13))

	gray = cv2.erode(gray,kernel_5)

	gray = cv2.dilate(gray,kernel_13)
	'''
	if img_array_send == True:
		# detect faces in the grayscale frame
		rects = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE)

		# OpenCV returns bounding box coordinates in (x, y, w, h) order
		# but we need them in (top, right, bottom, left) order, so we
		# need to do a bit of reordering
		boxes = [(y, x + w, y + h, x) for (x, y, w, h) in rects]

		# compute the facial embeddings for each face bounding box
		encodings = face_recognition.face_encodings(rgb, boxes)
		names = []

		# loop over the facial embeddings
		for encoding in encodings:
			# attempt to match each face in the input image to our known
			# encodings
			matches = face_recognition.compare_faces(data["encodings"], encoding, tolerance=0.5)
			name = "Unknown"

			# check to see if we have found a match
			if True in matches:
				# find the indexes of all matched faces then initialize a
				# dictionary to count the total number of times each face
				# was matched
				matchedIdxs = [i for (i, b) in enumerate(matches) if b]
				counts = {}

				# loop over the matched indexes and maintain a count for
				# each recognized face face
				for i in matchedIdxs:
					name = data["names"][i]
					counts[name] = counts.get(name, 0) + 1

				# determine the recognized face with the largest number
				# of votes (note: in the event of an unlikely tie Python
				# will select first entry in the dictionary)
				name = max(counts, key=counts.get)

			# update the list of names
			names.append(name)

		# loop over the recognized faces

		for ((top, right, bottom, left), name) in zip(boxes, names):
			# draw the predicted face name on the image
			cv2.rectangle(frame, (left, top), (right, bottom), (255, 255, 255), 2)
			y = top - 15 if top - 15 > 15 else top + 15
			cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
			save_name = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime( time.time())) + '-' + str(name) + '.jpg'
			save_path = str(os.getcwd()) + '/tmp_photo/' + str(save_name)
			crop_size = (480,272)
			frame = cv2.resize(frame, crop_size, interpolation = cv2.INTER_CUBIC)
			'''
			cv2.imwrite(save_path, frame)
			time.sleep(1)
			print('save image to: {0}'.format(save_path))

			frame_rgb = Image.open(save_path)
			frame_rgb = frame_rgb.convert("RGB")
			'''
			frame_rgb = Image.fromarray(frame)
			frame_rgb = frame_rgb.convert("RGB")
			rgb_data = frame_rgb.getdata()
			if img_array_send == True:
				img_array = []
				#img_array = bytearray()
				for i in range(len(rgb_data)):
					img_array.append(0)
					img_array.append(0)
					img_array.append(0)
					count = 3
					for j in rgb_data[i]:
						#img_array.append(struct.pack("B", j))
						img_array[len(img_array)-count] = int(j)
						#img_array.append(int(j))
						count = count - 1
				img_array_send = False

	# display the image to our screen
	cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF

	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break

	# update the FPS counter
	fps.update()

# stop the timer and display FPS information
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()
