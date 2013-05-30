from Queue import Queue
from threading import Thread, Timer
from collections import deque, namedtuple
from time import sleep, time
from message import Message
import time
import threading
import thread

class Ship:

	def __init__(self, cranes, crates, topRow, bottomRow):
		self.topRow = topRow  # top row of the ship (ship's bow)
		self.bottomRow = bottomRow  # bottom row of the ship (ship's stern)
		self.cranes = cranes
		self.crates = crates
		self.running = True
		self.messages = Queue()
		self.createThread().start()

	def sendMessage(self):
		part = 4
		a = 0
		b = len(self.crates) % part
		while( b <= len(self.crates)):
			msg = Message(self, Message.SEARCH_PACKAGE, self.crates[a:b])
			a = b + 1
			b = b + part
			time.sleep(2)
			for i in xrange(len(self.cranes)):
				self.cranes[i].addMessage(msg)
	
	def readMessage(self, msg):
		print "SHIP: crane", msg.sender.id, "sent message:", msg.data

	def readMessages(self, left=5):
		while (left > 0 and not self.messages.empty()):
			self.readMessage(self.messages.get())
			left -= 1  
		
	def mainLoop(self):
		part = 5
		count = len(self.crates)/part
		i=0
		thread.start_new_thread(self.sendMessage, ())
		while (self.running):
			self.readMessages()
		
	def createThread(self):
		return Thread(target=self.mainLoop, args=[])

	def addMessage(self, msg):
		self.messages.put(msg)

	def stop(self):
		self.running = False


