# USAGE
# python pi_face_recognition.py --cascade haarcascade_frontalface_default.xml --encodings encodings.pickle

# import the necessary packages
import speech_recognition as sr
import jieba
import time
import threading
import sys
from time import sleep
sys.path.insert(0, '../')
from SX127x.LoRa import *
from SX127x.LoRaArgumentParser import LoRaArgumentParser
from SX127x.board_config import BOARD
from gtts import gTTS
from pygame import mixer
import RPi.GPIO as GPIO
import json

from imutils.video import VideoStream
from imutils.video import FPS
import face_recognition
import argparse
import imutils
import pickle
import cv2
import socket
import os
import struct
import datetime
from datetime import datetime, timedelta

from picamera.array import PiRGBArray
from picamera import PiCamera

import smbus2
sys.modules['smbus'] = smbus2
from RPLCD.i2c import CharLCD

def initEnv(irtransmit_pin, irreceive_pin, state_pin, send_pin):
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(irtransmit_pin, GPIO.OUT)
    GPIO.setup(irreceive_pin, GPIO.IN)
    GPIO.setup(state_pin, GPIO.IN)
    GPIO.setup(send_pin, GPIO.IN)

def endEnv():
    GPIO.cleanup()

def getSignal(irreceive_pin, state_pin):
    start, stop = 0, 0
    signals = []
    get = GPIO.input(irreceive_pin)
    print("get: {0}".format(get))
    start = time.time()
    while True:
        get2 = GPIO.input(irreceive_pin)
        if get2 != get:
            end = time.time()
            duration = end - start
            start = end
            signals.append(duration)
            get = get2
        if ((time.time() - start) > 0.1) and len(signals) > 0:
            print("len(signals[1:]): {0}".format(len(signals[1:])))
            tmp = signals[1:]
            signals = []
            return tmp
        if GPIO.input(state_pin) == 0:
            print("change mode to send1")
            tmp = []
            return tmp

def record(irreceive_pin, state_pin):
    tmp = getSignal(irreceive_pin, state_pin)
    if (GPIO.input(state_pin) == 1) and (len(tmp) > 0):
        try:
            low = []
            high = []
            avg_tmp = sum(tmp[2:len(tmp)])/(len(tmp)-2)
            print("avg_tmp: {0}".format(avg_tmp))
            for i in range(2, len(tmp)):
                if tmp[i] >= (avg_tmp + 0.3*avg_tmp):
                    high.append(tmp[i])
                else:
                    low.append(tmp[i])

            low_avg = sum(low)/(len(low))
            high_avg = sum(high)/(len(high))
            print("low_avg: {0}".format(low_avg))
            print("high_avg: {0}".format(high_avg))
            record_array = []
            record_array.append(round(tmp[0],10))
            record_array.append(round(tmp[1],10))
            for i in range(2, len(tmp)):
                if tmp[i] >= (avg_tmp + 0.3*avg_tmp):
                    record_array.append(round(high_avg,10))
                else:
                    record_array.append(round(low_avg,10))

            key_name = "close"
            keys = {}
            keys[key_name] = record_array
            key_name = "ori_close"
            keys[key_name] = tmp
            print("len(keys[key_name]): {0}".format(len(keys[key_name])))
            LCD_set("Sig len:"+str(len(keys[key_name])), "Time: {}".format(time.strftime("%H:%M:%S")))
            OUT_FILE = "/home/pi/pi-voice-recognition/key_map2.json"
            src = open(OUT_FILE, 'w')
            src.write(json.dumps(keys))
            src.close()
        except:
            print("fail record")

    else:
        print("change mode to send2")

class IRThread(threading.Thread):
    def __init__(self, num):
        threading.Thread.__init__(self)
        self.num = num

    def run(self):
        global button_pin_state
        irtransmit_PIN = 5
        irreceive_PIN = 6
        state_PIN = 19
        send_PIN = 26
        initEnv(irtransmit_PIN, irreceive_PIN, state_PIN, send_PIN)
        p = GPIO.PWM(irtransmit_PIN, 38000)
        p.ChangeDutyCycle(0)
        p.start(0)
        send_pin_state = GPIO.input(send_PIN)
        while True:
            if GPIO.input(state_PIN) == 1:
                time.sleep(1)
                button_pin_state = 1
                print("GPIO.input(state_PIN): {0}".format(GPIO.input(state_PIN)))
                record(irreceive_PIN, state_PIN)
                SIGNAL_MAP = "/home/pi/pi-voice-recognition/key_map2.json"
                src = open(SIGNAL_MAP, 'r')
                signal_map = json.loads(src.read())
                src.close()

            else:
                SIGNAL_MAP = "/home/pi/pi-voice-recognition/key_map2.json"
                src = open(SIGNAL_MAP, 'r')
                signal_map = json.loads(src.read())
                src.close()
                button_pin_state = 0
                if send_pin_state != GPIO.input(send_PIN):
                    button_pin_state = 1
                    send_pin_state = GPIO.input(send_PIN)
                    time.sleep(1)
                    LCD_set("Send sig:"+str(len(signal_map["ori_close"])), "Time: {}".format(time.strftime("%H:%M:%S")))
                    for i in range(3):
                        time.sleep(0.3)
                        count = 0
                        key_name = "ori_close"
                        for name in signal_map.keys():
                            if key_name == name:
                                high_low = True
                                start = time.time()
                                for t in signal_map[key_name]:
                                    if high_low == False:
                                        p.ChangeDutyCycle(0)
                                        high_low = True
                                    else:
                                        p.ChangeDutyCycle(33)
                                        high_low = False
                                    start = time.time()
                                    while (time.time() - start) < float(t):
                                        pass
                                    count = count + 1
                        print("send {0}th, count: {1}".format(i, count))
                        p.ChangeDutyCycle(0)
                    button_pin_state = 0

        p.stop()
        endEnv()

class LoRaRcvCont(LoRa):
    def __init__(self, verbose=False):
        super(LoRaRcvCont, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0] * 6)

    def on_rx_done(self):
        global send_receive_flag
        global lora_receive_msg
        BOARD.led_on()
        print("\nRxDone")
        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True)
        lora_receive_msg = ''.join([chr(c) for c in payload])
        print("Receive lora_receive_msg: {0}".format(lora_receive_msg))
        #print(bytes(payload).decode())
        self.set_mode(MODE.SLEEP)
        self.reset_ptr_rx()
        BOARD.led_off()
        self.set_mode(MODE.RXCONT)

    def on_tx_done(self):
        global send_receive_flag
        global lora_send_msg
        if send_receive_flag == "send":
            send_msg = lora_send_msg
            send_receive_flag = "receive"
            self.set_mode(MODE.STDBY)
            self.clear_irq_flags(TxDone=1)
            sys.stdout.flush()
            self.tx_counter += 1
            BOARD.led_off()
            data = [int(hex(ord(c)), 0) for c in send_msg]
            #self.write_payload([0x0f])
            self.write_payload(data)
            BOARD.led_on()
            self.set_mode(MODE.TX)

    def on_cad_done(self):
        print("\non_CadDone")
        print(self.get_irq_flags())

    def on_rx_timeout(self):
        print("\non_RxTimeout")
        print(self.get_irq_flags())

    def on_valid_header(self):
        print("\non_ValidHeader")
        print(self.get_irq_flags())

    def on_payload_crc_error(self):
        print("\non_PayloadCrcError")
        print(self.get_irq_flags())

    def on_fhss_change_channel(self):
        print("\non_FhssChangeChannel")
        print(self.get_irq_flags())

    def start(self):
        global send_receive_flag
        global lora_send_msg

        send_receive_flag = "receive"
        while True:

            if send_receive_flag == "receive":
                self.set_mode(MODE.SLEEP)
                self.set_dio_mapping([0] * 6)

                self.reset_ptr_rx()
                self.set_mode(MODE.RXCONT)
                sleep(.5)
                rssi_value = self.get_rssi_value()
            else:
                print("send_receive_flag == send : {0}".format(lora_send_msg))
                self.set_mode(MODE.SLEEP)
                self.set_dio_mapping([1,0,0,0,0,0])
                self.tx_counter = 0
                BOARD.led_on()
                self.write_payload([0x0f])
                #self.write_payload([0x0f, 0x65, 0x6c, 0x70])
                self.set_mode(MODE.TX)

            '''
            status = self.get_modem_status()
            sys.stdout.flush()
            sys.stdout.write("\r%d %d %d" % (rssi_value, status['rx_ongoing'], status['modem_clear']))
            '''

class LoraThread(threading.Thread):
    def __init__(self, num):
        threading.Thread.__init__(self)
        self.num = num

    def run(self):
        BOARD.setup()
        parser = LoRaArgumentParser("Continous LoRa receiver.")

        lora = LoRaRcvCont(verbose=False)
        args = parser.parse_args(lora)

        lora.set_mode(MODE.STDBY)
        lora.set_pa_config(pa_select=1)
        lora.set_freq(434.0)
        #lora.set_rx_crc(True)
        #lora.set_coding_rate(CODING_RATE.CR4_6)
        #lora.set_pa_config(max_power=0, output_power=0)
        #lora.set_lna_gain(GAIN.G1)
        #lora.set_implicit_header_mode(False)
        #lora.set_low_data_rate_optim(True)
        #lora.set_pa_ramp(PA_RAMP.RAMP_50_us)
        #lora.set_agc_auto_on(True)

        print("lora: {0}".format(lora))
        assert(lora.get_agc_auto_on() == 1)
        time.sleep(1)
        try:
            lora.start()
        except KeyboardInterrupt:
            sys.stdout.flush()
            print("")
            sys.stderr.write("KeyboardInterrupt\n")
        finally:
            sys.stdout.flush()
            print("")
            lora.set_mode(MODE.SLEEP)
            print(lora)
            BOARD.teardown()

def callback(recognizer, audio):
    global get_voice
    global receive
    receive = ""
    # recognize speech using Google Speech Recognition
    try:
        print("Google Speech Recognition thinks you said:")
        receive = str(recognizer.recognize_google(audio, language="zh-TW"))
        print(receive)
        get_voice = True
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print("No response from Google Speech Recognition service: {0}".format(e))

class SoundtotextThread(threading.Thread):
    def __init__(self, num):
        threading.Thread.__init__(self)
        self.num = num

    def run(self):
        #obtain audio from the microphone
        global send_receive_flag
        global lora_send_msg
        global button_pin_state
        global get_voice
        global receive
        get_voice = False
        receive = ""
        ready_record = False
        r=sr.Recognizer()
        with sr.Microphone() as source:
            print("Please wait. Calibrating microphone...")
            #listen for 5 seconds and create the ambient noise energy level
            r.adjust_for_ambient_noise(source, duration=5)
        stop_listening = r.listen_in_background(sr.Microphone(), callback)
        ready_record = True
        seg_list = jieba.cut("初始化麥克風")
        receive_seg_list = ",".join(seg_list)
        print("seg_list: {0}".format(receive_seg_list))
        LCD_set("Dictionary Ready", "Time: {}".format(time.strftime("%H:%M:%S")))

        while True:
            if button_pin_state == 1:
                stop_listening(wait_for_stop=False)
                print("stop recording")
                try:
                    mixer.music.stop()
                except:
                    pass
            else:
                if ready_record == False:
                    stop_listening(wait_for_stop=True)
                    print("Say somethings")
                    ready_record = True
            while (button_pin_state == 1):
                time.sleep(1)

            if get_voice == True:
                seg_list = jieba.cut(receive)
                receive_seg_list = ",".join(seg_list)
                print("seg_list: {0}".format(receive_seg_list))
                seg_str = receive_seg_list.split(",")
                light = 0
                on_off = 0
                send_content = ""
                for i in seg_str:
                    if i == "關燈":
                        print("關燈")
                        on_off = 0
                        for j in seg_str:
                            if j == "第一排" or j == "第一盞":
                                light = 1
                                break
                            elif j == "第二排" or j == "第二盞":
                                light = 2
                                break
                            elif j == "第三排" or j == "第三盞":
                                light = 3
                                break
                            elif (j == "全部") or (j == "所有"):
                                light = 0
                                break
                        send_content = "Device1 turn_off light " + str(light)
                        break
                    elif i == "開燈":
                        print("開燈")
                        on_off = 1
                        for j in seg_str:
                            if j == "第一排" or j == "第一盞":
                                light = 1
                                break
                            elif j == "第二排" or j == "第二盞":
                                light = 2
                                break
                            elif j == "第三排" or j == "第三盞":
                                light = 3
                                break
                            else:
                                light = 0
                        send_content = "Device1 turn_on light " + str(light)
                        break
                lora_send_msg = send_content
                if lora_send_msg != "":
                    input_text = 'Last_Call'
                    tts=gTTS(text=input_text, lang='zh-tw')
                    download_path = "/home/pi/" + input_text + ".mp3"
                    #tts.save(download_path)
                    mixer.init()
                    mixer.music.load(download_path)
                    mixer.music.play()
                    global lora_receive_msg
                    lora_receive_msg = ""
                    print("send: {0}".format(lora_send_msg))
                    send_receive_flag = "send"
                    tmp = datetime.now()
                    while lora_receive_msg == "":
                        if (datetime.now() - tmp)>5:
                            tmp = tmp = datetime.now()
                            print("send: {0}".format(lora_send_msg))
                            send_receive_flag = "send"
                    print("Receive lora respones: {0}".format())
                    print("The {0}th light is {1} (off/on)".format(light, on_off))
                get_voice = False
                ready_record = False
            '''
            get_voice = False

            while (get_voice == False):
                try:
                    #audio=r.listen(source, timeout = 10)
                    audio=r.listen(source)
                    print("Get voice")
                    get_voice = True
                except:
                    print("No voice")
                    get_voice = False
            '''

class ClientThread(threading.Thread):
    def __init__(self, num):
        threading.Thread.__init__(self)
        self.num = num
    def run(self):
        host = '192.168.11.4'
        port = 9999
        lastminute_new = datetime.now()
        global button_pin_state
        while True:
            try:
                while (button_pin_state == 1):
                    time.sleep(1)
                tmp_photo = os.listdir('/home/pi/pi-face-recognition/pi-face-recognition/tmp_photo/')
                time.sleep(1)
                if (len(tmp_photo) > 0):
                    print('len(tmp_photo): {0}'.format(len(tmp_photo)))
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
            except:
                print('reconnecting...')

class ServerThread(threading.Thread):
    def __init__(self, num):
        threading.Thread.__init__(self)
        self.num = num
    def run(self):
            try:
            	while True:
                    #print("start server")
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.bind(('192.168.11.4', 9999))
                    s.listen(5)
                    s.settimeout(10)
                    sock, addr = s.accept()
                    #print('Server socket accept')
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
                    	#save_path = str(os.getcwd()) + '/' + img_name
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

class OpencvThread(threading.Thread):
    def __init__(self, num):
        threading.Thread.__init__(self)
        self.num = num

    def run(self):
        global send_receive_flag
        global lora_send_msg
        global lora_receive_msg
        global button_pin_state
        if_msg_send = False
        start_play_time = 0
        last_send_time = 0
        already_close = False
        input_text = 'Last_Call'
        download_path = "/home/pi/" + input_text + ".mp3"
        mixer.init()
        mixer.music.load(download_path)

        '''
        # construct the argument parser and parse the arguments
        ap = argparse.ArgumentParser()
        ap.add_argument("-c", "--cascade", required=True,
        	help = "path to where the face cascade resides")
        ap.add_argument("-e", "--encodings", required=True,
        	help="path to serialized db of facial encodings")
        args = vars(ap.parse_args())
        '''
        # load the known faces and embeddings along with OpenCV's Haar
        # cascade for face detection
        print("[INFO] loading encodings + face detector...")
        encodings = "/home/pi/pi-face-recognition/pi-face-recognition/encodings.pickle"
        cascade = "/home/pi/pi-face-recognition/pi-face-recognition/haarcascade_frontalface_default.xml"
        '''
        data = pickle.loads(open(args["encodings"], "rb").read())
        detector = cv2.CascadeClassifier(args["cascade"])
        '''
        data = pickle.loads(open(encodings, "rb").read())
        detector = cv2.CascadeClassifier(cascade)

        # initialize the video stream and allow the camera sensor to warm up
        print("[INFO] starting video stream...")

        camera = PiCamera()
        camera.resolution = (640, 480)
        camera.framerate = 32
        rawCapture = PiRGBArray(camera, size=(640, 480))

        #vs = VideoStream(usePiCamera=True).start()
        #vs = VideoStream(usePiCamera=True)

        print("start camera")
        time.sleep(2.0)
        # start the FPS counter
        fps = FPS().start()
        #frame = vs.read()
        camera.capture(rawCapture, format="bgr")
        frame = rawCapture.array
        rawCapture.truncate(0)

        gray_before = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # loop over frames from the video file stream
        no_people_detect = 0
        people_detect = time.time()

        while True:
            # grab the frame from the threaded video stream and resize it
            # to 500px (to speedup processing)
            if button_pin_state == 1:
                while True:
                    time.sleep(1)
                    if button_pin_state == 0:
                        print("restart camera")
                        break
            #frame = vs.read()
            camera.capture(rawCapture, format="bgr")
            frame = rawCapture.array
            rawCapture.truncate(0)
            time.sleep(0.3)

            # convert the input frame from (1) BGR to grayscale (for face
            # detection) and (2) from BGR to RGB (for face recognition)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            gray_after = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            gray = gray_after - gray_before
            gray_before = gray_after

            kernel_5 = cv2.getStructuringElement(cv2.MORPH_RECT,(9, 9))
            kernel_13 = cv2.getStructuringElement(cv2.MORPH_RECT,(13, 13))

            gray = cv2.erode(gray,kernel_5)

            gray = cv2.dilate(gray,kernel_13)

            height, width = gray.shape
            area = 0
            for i in range(height//13):
                for j in range(width//13):
                    if gray[13*i, 13*j] > 10:
                        area += 1
                    if area!= 0:
                        break
                if area!= 0:
                    break
            if area!= 0:
                #print("Someone here")
                LCD_set("Someone here", "Time: {}".format(time.strftime("%H:%M:%S")))
            elif already_close == True:
                LCD_set("Turn off", "Time: {}".format(time.strftime("%H:%M:%S")))
            else:
                #print("No one here")
                LCD_set("No one here", "Time: {}".format(time.strftime("%H:%M:%S")))

            cv2.imshow("Frame_ori", frame)
            #cv2.imshow("Frame", gray)

            if area != 0:
                start_play_time = 0
                people_detect = time.time()
                already_close = False
                if mixer.music.get_busy() == 1:
                    mixer.music.fadeout(3000)
            else:
                no_people_detect = time.time() - people_detect
            if already_close == True:
                print("Turnoff anything")
                no_people_detect = 0

            if (no_people_detect > 10) and (already_close == False):
                no_people_detect = 0
                print("No_people_detect > 60s")
                LCD_set("Play music", "Time: {}".format(time.strftime("%H:%M:%S")))
                if start_play_time == 0:
                    mixer.music.play()
                    start_play_time = time.time()

            if (time.time() - start_play_time > 20) and (start_play_time != 0):
                start_play_time = 0
                if mixer.music.get_busy() == 1:
                    mixer.music.fadeout(3000)
                    print("fadeout the music")
                if if_msg_send == False:
                    lora_receive_msg = ""
                    lora_send_msg = "Device1 turn_off light 0"
                    send_receive_flag = "send"
                    last_send_time = time.time()
                    print("send: {0}".format(lora_send_msg))
                    people_detect = time.time()
                    if_msg_send = True

            if if_msg_send == True:
                if lora_receive_msg == "":
                    lora_send_msg = "Device1 turn_off light 0"
                    if ((time.time() - last_send_time) > 5) and (last_send_time != 0):
                        last_send_time = time.time()
                        send_receive_flag = "send"
                        print("send: {0}".format(lora_send_msg))
                else:
                    if_msg_send = False
                    last_send_time = 0
                    already_close = True
                    print("Receive lora respones: {0}".format(lora_receive_msg))

            '''
            # detect faces in the grayscale frame
            rects = detector.detectMultiScale(gray, scaleFactor=1.1,
            	minNeighbors=5, minSize=(30, 30),
            	flags=cv2.CASCADE_SCALE_IMAGE)

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
            	matches = face_recognition.compare_faces(data["encodings"],
            		encoding)
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
            	cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            	y = top - 15 if top - 15 > 15 else top + 15
            	cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
            	save_name = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime( time.time())) + '-' + str(name) + '.jpg'
            	save_path = str(os.getcwd()) + '/tmp_photo/' + str(save_name)
            	cv2.imwrite(save_path, frame)
            	#cv2.imwrite(save_name, frame)
            	print('save image to: {0}'.format(save_path))
            	time.sleep(1)
            '''
            # display the image to our screen
            key = cv2.waitKey(1) & 0xFF

            # if the `q` key was pressed, break from the loop
            if key == ord("q"):
            	break

            # update the FPS counter
            #fps.update()

        # stop the timer and display FPS information
        fps.stop()
        print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
        print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

        # do a bit of cleanup
        cv2.destroyAllWindows()
        vs.stop()
def LCD_init():
    global lcd
    global lcd_busy
    global last_firstline
    global last_secondline
    last_firstline = ""
    last_secondline = ""
    lcd_busy = False
    lcd = CharLCD('PCF8574', address=0x27, port=1, backlight_enabled=True)

def LCD_reset():
    global lcd
    global lcd_busy
    while lcd_busy == True:
        pass
    lcd_busy = True
    lcd.clear()
    lcd.cursor_pos = (0, 0)
    lcd.write_string("Date: {}".format(time.strftime("%Y/%m/%d")))
    lcd.cursor_pos = (1, 0)
    lcd.write_string("Time: {}".format(time.strftime("%H:%M:%S")))
    time.sleep(0.06)
    print("set lcd")
    lcd_busy = False

def LCD_set(firstline = "", secondline = ""):
    global lcd
    global lcd_busy
    while lcd_busy == True:
        pass
    global last_firstline
    global last_secondline
    lcd_busy = True
    lcd.clear()
    if (last_firstline != firstline) and (firstline != ""):
        last_firstline = firstline
        lcd.cursor_pos = (0, 0)
        lcd.write_string(firstline)

    if (last_secondline != secondline) and (secondline !=""):
        last_firstline = secondline
        lcd.cursor_pos = (1, 0)
        lcd.write_string(secondline)

    lcd_busy = False

def main():

    LCD_init()
    LCD_reset()
    # construct the argument parser and parse the arguments
    global button_pin_state
    button_pin_state = 1
    LoraThread(0).start()
    time.sleep(0.5)
    IRThread(1).start()
    SoundtotextThread(2).start()
    while button_pin_state == 1:
        time.sleep(1)
        pass
    print("start video")
    OpencvThread(3).start()
    ClientThread(4).start()

    while True:
        time.sleep(1)
        pass

if __name__ == "__main__":
    try:
        main()
    except:
        pass
    finally:
        GPIO.cleanup()
