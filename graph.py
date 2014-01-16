#!/usr/bin/python
#
# Serial reader and grapher
#  with IIR Filter
#
# Sam Mitchell Finnigan, 2013
#

import signal
import serial
import threading
import sys
import collections
import random
import time

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

# Run test using random data
test = True if (len(sys.argv) > 1 and sys.argv[1] == '--test') else False

# Serial device configuration
DEVICE   = '/dev/tty.usbserial'
BAUD     = 115200

# Async fixed-length deque for last 300 samples from serial
SAMPLES = 380
raw_lock = threading.Lock()
raw_samples = collections.deque(maxlen=SAMPLES)

# Values of iir (for graphing purposes only)
iir_values = collections.deque(maxlen=SAMPLES)
# Rectified Difference (for event detection)
diff_values = collections.deque(maxlen=SAMPLES)

# IIR Filter Vars
order = 8 				# 2^3
m = 1 					# response
n = 7
acc = 0					# accumulator
iir_last = 0			# P0

threshold = 4
# current PIR value provided by deque: raw_samples[-1]



# Thread for emulating serial read
class randThread(threading.Thread):
	current = 0
	baseline = 300
	running = True

	def __init__(self):
		threading.Thread.__init__(self)

	def run(self):
		global raw_lock

		while self.running:
			line = self.randLine()
			#print line 				# ssssh!
			
			raw_lock.acquire()			# Get lock to synchronize threads
			raw_samples.append(line)	# append line to deque
			doIIR()						# Run infinite impulse response filter
			raw_lock.release()			# Free lock to release next thread

	def stop(self):
		self.running = False

	def randLine(self):

		# Noise function
		self.current += (random.randint(0,6)) - 3
		
		# Emulate serial speed at 8Hz
		time.sleep(0.12)
		
		if(self.current > 50):
			self.current = 50		# Max
		if(self.current > 0):
			return self.baseline + self.current

		return self.baseline + abs(self.current)




# Thread for doing serial read for real
class serialThread(threading.Thread):
	running = True

	def __init__(self):
		threading.Thread.__init__(self)

		# Init serial
		self.ser = serial.Serial(DEVICE, BAUD)		# Attempt to open serial port (or die)
		
		if False:									# TODO Does this work?
			self.ser.close()
			sys.exit(1)
	
		# Write serial connection name to show success
		print "Serial interface started on " + self.ser.name

	def run(self):
		global d_lock

		while self.running:
			line = self.serialLine()

			if line:							# if line isn't empty ''
				#print line 					# sssh!

				raw_lock.acquire()
				raw_samples.append( int(line) )	# Stick it on the deque
				doIIR()
				raw_lock.release()
		

	# Gracefully stop this thread
	def stop(self):
		self.running = False
		self.ser.close()

	# Read line from serial port and put message on queue
	def serialLine(self):
	
		line = self.ser.readline()				# read from serial
		return line[4:7]						# strip 'PIR,' prefix and newline



# Run Infinite Impulse Response Filter on input
def doIIR():

	global iir_last, acc

	acc = int(
		( ((order * m) * raw_samples[-1] ) 
		 	+ ((order - m) * acc) ) 
		/ order 
	)

	iir_last = int( (acc + order-1) / order )

	diff_values.append( abs(iir_last - iir_values[-1]) )
	iir_values.append(iir_last)

	print raw_samples[-1], acc, iir_last, diff_values[-1]



# GLUT main loop
def display():
	glClear(GL_COLOR_BUFFER_BIT)
	
	# Draw vertices onto graph
	raw_lock.acquire()							# Lock deque before enumerating it
	
	glColor3f(1.0, 0.0, 0.0)					# red for raw
	
	glBegin(GL_LINE_STRIP)						# Draw raw values
	for x,y in enumerate(raw_samples):
		glVertex2f(10.0 + x, -150.0 + y)
	glEnd()


	glColor3f(1.0, 1.0, 1.0)					# white for iir
	
	glBegin(GL_LINE_STRIP)						# Draw iir values
	for x,y in enumerate(iir_values):
		glVertex2f(10.0 + x, -150.0 + y)
	glEnd()


	glColor3f(0.19, 0.46, 0.69)					# blue for rectified difference
	
	glBegin(GL_LINE_STRIP)						# Draw diffed values
	for x,y in enumerate(diff_values):
		glVertex2f(10.0 + x, 10.0 + y)
	glEnd()

	raw_lock.release()							# Unlock deque when done

	glFlush()



def reshape(w, h):
	glViewport(0, 0, w, h)
	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()
	gluOrtho2D(0.0, w, 0.0, h)



# GLUT Keyboard callback 
def keyboard(key, x, y):
	if key == chr(27): 		# ESC
		thread.stop()
		print ' - Thread stop flagged'
		sys.exit(0)



# SIGINT handler
def signal_handler(signal, frame):
	print ' - Ctrl+C pressed, exiting'
	thread.stop()
	sys.exit(0)


# Main method 
# Initialize GLUT (ugh. Python, Y U no use GLFW?)
def main():
	global thread

	# Initialise deque with samples of 0
	for i in range(0, SAMPLES):
		raw_samples.append(0)
		iir_values.append(0)
		diff_values.append(0)
	
	# Init GL
	glutInit(sys.argv)
	glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)

	glutInitWindowSize(400, 300)
	glutInitWindowPosition(100, 100)
	glutCreateWindow('PIR Data')
	glClearColor(0.0, 0.0, 0.0, 0.0)

	glutDisplayFunc(display)
	glutIdleFunc(display)
	glutReshapeFunc(reshape)
	glutKeyboardFunc(keyboard)

	# start readserial thread
	thread.start()

	# start glut
	glutMainLoop()

	# No code past here will ever run
	#  ... god I hate GLUT.


# Run main
if __name__ == "__main__":

	# Globally instantiate listener thread
	thread = randThread() if test else serialThread()
	signal.signal(signal.SIGINT, signal_handler)
	main()

