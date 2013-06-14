from Queue import Queue
from threading import Thread, Timer
from collections import deque, namedtuple
from time import sleep, time
from message import Message
import time
import threading
import thread

class Ship:

	def __init__(self, map, cranes, crates, topRow, bottomRow, timeInterval):
		self.map = map
		self.topRow = topRow  # top row of the ship (ship's bow)
		self.bottomRow = bottomRow  # bottom row of the ship (ship's stern)
		self.timeInterval = timeInterval
		self.cranes = cranes
		self.crates = crates
		self.neededCrates = []
		self.infoData = []  # (crateId, requestTime, deliveryTime, waitTime, craneId)
		for crate in crates:
			self.infoData.append([crate, None, None, None, None])
		self.startTime = time.time()
		self.running = True
		self.messages = Queue()
		self.createThread().start()

	def readMessage(self, msg):
		print "SHIP: crane", msg.sender.id, "sent message:", msg.data
		if msg.type == Message.PACKAGE_LOADED:
			t = time.time()
			self.neededCrates.remove(msg.data)
			infoIndex = [tup[0] for tup in self.infoData].index(msg.data)
			self.infoData[infoIndex][2] = t - self.startTime
			self.infoData[infoIndex][3] = self.infoData[infoIndex][2] - self.infoData[infoIndex][1]
			self.infoData[infoIndex][4] = msg.sender.id
			for c in self.cranes:
				c.addMessage(Message(self, Message.PACKAGE_DELIVERED, [msg.data, t]))

	def readMessages(self, left=5):
		while (left > 0 and not self.messages.empty()):
			self.readMessage(self.messages.get())
			left -= 1
		
	def mainLoop(self):
		part = 4
		a = 0
		b = len(self.crates) % part
		lastSendTime = time.time()
		blimeyTheMapHasPaused = False
		timeWhenPauseStarted = 0.0
		while (self.running):
			if self.map.pause == True:
				if blimeyTheMapHasPaused == True:
					continue
				blimeyTheMapHasPaused = True
				timeWhenPauseStarted = time.time()
				continue
			elif blimeyTheMapHasPaused == True: # The map is no longer paused
				blimeyTheMapHasPaused = False
				lastSendTime += (time.time() - timeWhenPauseStarted)
			if b <= len(self.crates) and time.time() - lastSendTime >= self.timeInterval:
				msg = Message(self, Message.SEARCH_PACKAGE, self.crates[a:b])
				self.neededCrates += self.crates[a:b]
				for i in xrange(a, b):
					self.infoData[i][1] = time.time() - self.startTime
				a = b
				b = b + part
				for i in xrange(len(self.cranes)):
					self.cranes[i].addMessage(msg)
				lastSendTime = time.time()
			self.readMessages()
		
	def createThread(self):
		return Thread(target=self.mainLoop, args=[])

	def addMessage(self, msg):
		self.messages.put(msg)

	def stop(self):
		self.running = False


