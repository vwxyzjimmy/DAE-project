#!/usr/bin/env python3
"""
This is a program for recording your IR-device signal.

@author: FATESAIKOU
@argv[1]: data input pin(BOARD)
@argv[2]: the output filename for key_map
"""

import RPi.GPIO as GPIO
import time
import sys
import json

def initEnv(pin1):
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    GPIO.setup(pin1, GPIO.IN)

def endEnv():
    GPIO.cleanup()


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
        '''
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

def main():
    PIN = 31
    OUT_FILE = "/home/pi/pi-voice-recognition/key_map2.json"
    initEnv(PIN)

    keys = {}
    while True:
        key_name = input('Please input key name(exit for terminating this program):')
        if key_name == 'exit':
            break
        tmp = getSignal(PIN)
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
        record_array.append(round(tmp[0],6))
        record_array.append(round(tmp[1],6))
        for i in range(2, len(tmp)):
            if tmp[i] >= (avg_tmp + 0.3*avg_tmp):
                record_array.append(round(high_avg,6))
            else:
                record_array.append(round(low_avg,6))
        keys[key_name] = record_array
        print("len(keys[key_name]): {0}".format(len(keys[key_name])))
    endEnv()

    src = open(OUT_FILE, 'w')
    src.write(json.dumps(keys))
    src.close()

if __name__ == "__main__":
    main()
