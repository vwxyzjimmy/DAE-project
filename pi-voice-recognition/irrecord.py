#!/usr/bin/env python3
"""
This is a program for recording your IR-device signal.

@author: FATESAIKOU
@argv[1]: data input pin(BOARD)
@argv[2]: the output filename for key_map
"""
import threading
import RPi.GPIO as GPIO
import time
import sys
import json

class receive_ir_Thread(threading.Thread):
    def __init__(self, num):
        threading.Thread.__init__(self)
        self.num = num
    def run(self):
        print("Thread", self.num)
        while True:
            print("receive_ir_Thread receiving...")
            keys = get_Signal(31)
            src = open("/home/pi/pi-voice-recognition/key_map.json", 'r')
            signal_map = json.loads(src.read())
            src.close()
            command = decodeSingal(keys, signal_map, 0.0001)
            print("receive command: {0}".format(command))

class send_ir_Thread(threading.Thread):
    def __init__(self, num):
        threading.Thread.__init__(self)
        self.num = num
    def run(self):
        print("Thread", self.num)
        while True:
            src = open("/home/pi/pi-voice-recognition/key_map.json", 'r')
            signal_map = json.loads(src.read())
            src.close()
            for i in signal_map.keys():
                send_Signal(29, signal_map[i])
                print("{0} command has been send".format(i))
            time.sleep(2)

class record_ir_Thread(threading.Thread):
    def __init__(self, num):
        threading.Thread.__init__(self)
        self.num = num
    def run(self):
        print("Thread", self.num)
        keys = {}
        while True:
            key_name = input('Please input key name to record (exit for terminating this program):')
            if key_name == 'exit':
                break
            keys[key_name] = get_Signal(31)
        src = open("/home/pi/pi-voice-recognition/key_map.json", 'w')
        src.write(json.dumps(keys))
        src.close()

def initEnv(pin1, pin2):
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(pin1, GPIO.IN)
    GPIO.setup(pin2, GPIO.OUT)

def endEnv():
    GPIO.cleanup()

def get_Signal(pin):
    start, stop = 0, 0
    signals = []
    while GPIO.input(pin) == 0:
        None
    while True:
        if GPIO.input(pin) == 1:
            start = time.time()
            while GPIO.input(pin) == 1:
                stop = time.time()
                duringUp = stop - start
                if duringUp > 0.1 and len(signals) > 0:
                    print("len(signals): {0}".format(len(signals)))
                    return signals[2:]
            signals.append(duringUp)
        else:
            start = time.time()
            while GPIO.input(pin) == 0:
                stop = time.time()
                duringUp = stop - start
                if duringUp > 0.1 and len(signals) > 0:
                    print("len(signals): {0}".format(len(signals)))
                    return signals[2:]
            signals.append(duringUp)

def send_Signal(pin, keys_map):
    start, stop = 0, 0
    print("len(keys_map): {0}".format(len(keys_map)))
    for i in range(len(keys_map)):
        start = time.time()
        if i%2 == 0:
            GPIO.output(pin, GPIO.HIGH)
            while((time.time() - start) <  keys_map[i]) :
                pass
            GPIO.output(pin, GPIO.LOW)
        else:
            GPIO.output(pin, GPIO.LOW)
            while((time.time() - start) <  keys_map[i]) :
                pass
            GPIO.output(pin, GPIO.HIGH)

def compairSignal(s1, s2, rang):
    min_len = min(len(s1), len(s2))

    for i in range(min_len):
        if abs(s1[i] - s2[i]) > rang:
            return False
    return True

def decodeSingal(s, signal_map, rang):
    for name in signal_map.keys():
        if compairSignal(s, signal_map[name], rang):
            return name
    return None

def main():
    initEnv(31, 29)
    key_name = input('Please input operation(record / send&&receive): ')
    if key_name == "record":
        threads0 = record_ir_Thread(0)
        threads0.start()
    elif key_name == "send&&receive":
        threads1 = receive_ir_Thread(0)
        threads2 = send_ir_Thread(1)
        threads1.start()
        #threads2.start()
    while True:
        time.sleep(3)
    endEnv()
if __name__ == "__main__":
    main()
