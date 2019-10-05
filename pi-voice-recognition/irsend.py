import RPi.GPIO as GPIO
import time
import sys
import json

def initEnv(irtransmit_pin, irreceive_pin, state_pin, send_pin):
    GPIO.setmode(GPIO.BOARD)
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
            record_array.append(round(tmp[0],6))
            record_array.append(round(tmp[1],6))
            for i in range(2, len(tmp)):
                if tmp[i] >= (avg_tmp + 0.3*avg_tmp):
                    record_array.append(round(high_avg,6))
                else:
                    record_array.append(round(low_avg,6))

            key_name = "close"
            keys = {}
            keys[key_name] = record_array
            tmp2 = []
            for i in range(len(tmp)):
                tmp2.append(round(tmp[i],6))
            key_name = "ori_close"
            keys[key_name] = tmp2

            print("len(keys[key_name]): {0}".format(len(keys[key_name])))

            OUT_FILE = "/home/pi/pi-voice-recognition/key_map2.json"
            src = open(OUT_FILE, 'w')
            src.write(json.dumps(keys))
            src.close()
        except:
            print("fail record")

    else:
        print("change mode to send2")



def main():
    irtransmit_PIN = 29
    irreceive_PIN = 31
    state_PIN = 35
    send_PIN = 37

    initEnv(irtransmit_PIN, irreceive_PIN, state_PIN, send_PIN)
    p = GPIO.PWM(irtransmit_PIN, 38000)
    p.ChangeDutyCycle(0)
    p.start(0)
    SIGNAL_MAP = "/home/pi/pi-voice-recognition/key_map2.json"
    src = open(SIGNAL_MAP, 'r')
    signal_map = json.loads(src.read())
    src.close()
    send_pin_state = GPIO.input(send_PIN)
    while True:
        '''
        key_name = input('Please input key name to send(exit for terminating this program):')
        if key_name == 'exit':
            break
        '''
        if GPIO.input(state_PIN) == 1:
            print("GPIO.input(state_PIN): {0}".format(GPIO.input(state_PIN)))
            record(irreceive_PIN, state_PIN)
            SIGNAL_MAP = "/home/pi/pi-voice-recognition/key_map2.json"
            src = open(SIGNAL_MAP, 'r')
            signal_map = json.loads(src.read())
            src.close()

        else:
            if send_pin_state != GPIO.input(send_PIN):
                send_pin_state = GPIO.input(send_PIN)
                time.sleep(0.5)
                for i in range(1):
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
                                #print("float(t): {0}".format(float(t)))
                    print("send {0}th, count: {1}".format(i, count))
                    p.ChangeDutyCycle(0)
                    time.sleep(0.3)

    p.stop()
    endEnv()

if __name__ == "__main__":
    main()
