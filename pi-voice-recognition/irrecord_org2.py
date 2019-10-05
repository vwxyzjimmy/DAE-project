import RPi.GPIO as GPIO
import math
import os
from datetime import datetime
from time import sleep

# This is for revision 1 of the Raspberry Pi, Model B
# This pin is also referred to as GPIO23
INPUT_WIRE = 31
INPUT_WIRE_2 = 33

GPIO.setmode(GPIO.BOARD)
GPIO.setup(INPUT_WIRE, GPIO.IN)
GPIO.setup(INPUT_WIRE_2, GPIO.IN)

keys = {}

while True:
	value = 1
	# Loop until we read a 0
	while value:
		value = GPIO.input(INPUT_WIRE)

	# Grab the start time of the command
	startTime = datetime.now()

	# Used to buffer the command pulses
	command = []

	# The end of the "command" happens when we read more than
	# a certain number of 1s (1 is off for my IR receiver)
	numOnes = 0

	# Used to keep track of transitions from 1 to 0
	previousVal = 0

	while True:
        key_name = input('Please input key name(exit for terminating this program):')

		if value != previousVal:
			# The value has changed, so calculate the length of this run
			now = datetime.now()
			pulseLength = now - startTime
			startTime = now

			command.append((previousVal, pulseLength.microseconds))

		if value:
			numOnes = numOnes + 1
		else:
			numOnes = 0

		# 10000 is arbitrary, adjust as necessary
		if numOnes > 10000:
			break

		previousVal = value
		value = GPIO.input(INPUT_WIRE)
	decode_array = [[], []]
	#print("----------Start----------")
	for (val, pulse) in command:
		#print(val, pulse)
		decode_array[0].append(val)
		decode_array[1].append(pulse)
	decode_binary = []
	for i in range(2, len(decode_array[0])-1):
		if decode_array[0][i] == 0:
			if (decode_array[1][i+1] > 2*decode_array[1][i]):
				decode_binary.append(1)
			else:
				decode_binary.append(0)
	decode_hex = []
	str_decode_hex = "0x"
	for i in range(len(decode_binary)):
		if (i%4 == 0) and (i <= (len(decode_binary) - 4)):
			hex_num = hex(decode_binary[i]*8 + decode_binary[i+1]*4 + decode_binary[i+2]*2 + decode_binary[i+3]*1)
			decode_hex.append(hex_num)
			hex_str = ""
			if hex_num == hex(0):
				hex_str = "0"
			else:
				hex_str = str(hex_num).lstrip("0x")
			str_decode_hex = str_decode_hex + hex_str

	#print("-----------End-----------\n")
	#print("Size of array is " + str(len(command)))
	#print("decode_binary: {0}".format(decode_binary))
	#print("Size of decode_binary is " + str(len(decode_binary)))
	#print("decode_hex: {0}".format(decode_hex))
	#print("Size of decode_hex is " + str(len(decode_hex)))
	print("str_decode_hex: {0}".format(len(str_decode_hex)))
	if (len(str_decode_hex)>2):
		print("str_decode_hex: {0}".format(str_decode_hex))

    SIGNAL_MAP = "/home/pi/pi-voice-recognition/key_map_hex.json"

    src = open(OUT_FILE, 'w')
    src.write(json.dumps(keys))
    src.close()
