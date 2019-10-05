#!/usr/bin/env python3
"""
This is a program for recognizing infrared signal.

@author: FATESAIKOU
@argv[1]: data input pin(BOARD)
@argv[2]: signal key map
"""

import RPi.GPIO as GPIO
import time
import sys
import json

def initEnv(pin):
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    GPIO.setup(pin, GPIO.IN)

def endEnv():
    GPIO.cleanup()

'''
def getSignal(pin):
    start, stop = 0, 0
    signals = []
    while GPIO.input(pin) == 1:
        None
    while True:
        if GPIO.input(pin) == 1:
            start = time.time()
            while GPIO.input(pin) == 1:
                stop = time.time()
                duringUp = stop - start
                if duringUp > 0.1 and len(signals) > 0:
                    print("len(signals): {0}".format(len(signals)))
                    return signals
            signals.append(duringUp)
        else:
            start = time.time()
            while GPIO.input(pin) == 0:
                stop = time.time()
                duringUp = stop - start
                if duringUp > 0.1 and len(signals) > 0:
                    print("len(signals): {0}".format(len(signals)))
                    return signals
            signals.append(duringUp)
'''
def getSignal(pin):
    start, stop = 0, 0
    signals = []
    get = GPIO.input(pin)
    print("get: {0}".format(get))
    start = time.time()
    while True:
        get2 = GPIO.input(pin)
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


def compairSignal(s1, s2, rang):
    min_len = min(len(s1), len(s2))
    print("min_len: {0}".format(min_len))
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
    PIN = 31

    SIGNAL_MAP = "/home/pi/pi-voice-recognition/key_map2.json"

    src = open(SIGNAL_MAP, 'r')
    signal_map = json.loads(src.read())
    src.close()

    initEnv(PIN)

    while True:
        print("Please press key")
        s = getSignal(PIN)
        print("Youy press: %s" % ( decodeSingal(s, signal_map, 0.0005) ))

    endEnv()

if __name__ == "__main__":
    main()
