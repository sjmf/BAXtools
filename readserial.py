#!/usr/bin/python
#
# Serial reader
#

import signal
import serial
import sys

# Serial device
DEVICE   = '/dev/tty.usbserial'
BAUD     = 115200

# Main method 
def main():
	
	# Attempt to open serial port (or die)
	ser = serial.Serial(DEVICE, BAUD)
	if False:
		ser.close()
		sys.exit(1)
	
	print ser.name

	# main loop
	while True:

		# read from serial
		line = ser.readline()

#		Use print if line is not including \n
		print(line[4:])
		
	ser.close()


def signal_handler(signal, frame):
	print ' - Ctrl+C pressed, exiting'
	sys.exit(0)


# Run main
if __name__ == "__main__":
	signal.signal(signal.SIGINT, signal_handler)
	main()


