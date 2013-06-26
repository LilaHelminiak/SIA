from Queue import Queue
from threading import Thread, Timer
from collections import deque, namedtuple
from time import sleep, time
from message import Message
import time
import threading
import thread


class Ship:

	def __init__(self, map, cranes, forklifts, crates, topRow, bottomRow, cratesPerMessage, timeInterval):
		self.map = map
		self.topRow = topRow  # top row of the ship (ship's bow)
		self.bottomRow = bottomRow  # bottom row of the ship (ship's stern)
		self.cratesPerMessage = cratesPerMessage
		self.timeInterval = timeInterval
		self.agents = cranes + forklifts
		self.crates = crates
		self.hatchRow = int((topRow + bottomRow) / 2)
		self.bridgeCraneRow = self.hatchRow
		self.bridgeCraneState = 0 # 0 - choosing crate, 1 - moving to crate, 2 - moving to hatch
		self.bridgeCraneCrate = None
		self.cratesForBridgeCrane = 0
		self.neededCrates = []
		self.infoData = []  # (crateId, requestTime, deliveryTime, waitTime, craneId)
		for crate in crates:
			self.infoData.append([crate, None, None, None, None])
		self.startTime = time.time()
		self.running = True
		self.messages = Queue()
		self.createBridgeCraneThread().start()
		self.createThread().start()
		#self.bridgeCraneThread = self.createBridgeCraneThread()
		#self.bridgeCraneThread.start()

	def readMessage(self, msg):
		print "SHIP: crane", msg.sender.id, "sent message:", msg.data
		if msg.type == Message.PACKAGE_LOADED:
			t = time.time()
			self.neededCrates.remove(msg.data)
			infoIndex = [tup[0] for tup in self.infoData].index(msg.data)
			self.infoData[infoIndex][2] = t - self.startTime
			self.infoData[infoIndex][3] = self.infoData[infoIndex][2] - self.infoData[infoIndex][1]
			self.infoData[infoIndex][4] = msg.sender.id
			self.cratesForBridgeCrane += 1
			for c in self.agents:
				c.addMessage(Message(self, Message.PACKAGE_DELIVERED, [msg.data, t]))

	def readMessages(self, left=5):
		while (left > 0 and not self.messages.empty()):
			self.readMessage(self.messages.get())
			left -= 1

	def closestCrateRow(self):
		bestRow = self.map.rowNum + 1
		bestDist = self.map.rowNum * 10
		col = self.map.colNum - 1
		for row in xrange(self.topRow, self.bottomRow + 1):
			if self.map[(row, col)].countCrates() == 0:
				continue
			if abs(self.bridgeCraneRow - row) + abs(self.hatchRow - row) < bestDist:
				bestDist = abs(self.bridgeCraneRow - row) + abs(self.hatchRow - row)
				bestRow = row
		return bestRow

	def bridgeCraneLoop(self):
		col = self.map.colNum - 1
		while self.running:
			sleep(0.02)
			if self.map.pause == True:
				continue
			elif self.cratesForBridgeCrane == 0:
				sleep(1)
				continue
			elif self.bridgeCraneState == 0:
				crateRow = self.closestCrateRow()
				if(crateRow > self.map.rowNum):
					sleep(1)
					continue
				self.map[(crateRow, col)].lock.acquire(True)
				self.bridgeCraneState = 1
				continue
			elif self.bridgeCraneState == 1:
				if self.bridgeCraneRow == crateRow or abs(self.bridgeCraneRow - crateRow) < 0.02:
					self.bridgeCraneRow = crateRow
					self.bridgeCraneCrate = self.map[(crateRow, col)].removeCrateFromTop()
					self.map[(crateRow, col)].lock.release()
					self.bridgeCraneState = 2
				else:
					if self.bridgeCraneRow < crateRow:
						self.bridgeCraneRow += 0.02
					else:
						self.bridgeCraneRow -= 0.02
			elif self.bridgeCraneState == 2:
				if self.bridgeCraneRow == self.hatchRow or abs(self.bridgeCraneRow - self.hatchRow) < 0.02:
					self.bridgeCraneRow = self.hatchRow
					self.bridgeCraneCrate = None
					self.cratesForBridgeCrane -= 1
					self.bridgeCraneState = 0
				else:
					if self.bridgeCraneRow < self.hatchRow:
						self.bridgeCraneRow += 0.02
					else:
						self.bridgeCraneRow -= 0.02
			else:
				sleep(0.02)

	def mainLoop(self):
		a = 0
		b = min(self.cratesPerMessage, len(self.crates))
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
			if a != b and b <= len(self.crates) and time.time() - lastSendTime >= self.timeInterval:
				msg = Message(self, Message.SEARCH_PACKAGE, self.crates[a:b])
				self.neededCrates += self.crates[a:b]
				for i in xrange(a, b):
					self.infoData[i][1] = time.time() - self.startTime
				a = b
				b = min(b + self.cratesPerMessage, len(self.crates))
				for i in xrange(len(self.agents)):
					self.agents[i].addMessage(msg)
				lastSendTime = time.time()
			self.readMessages()
		
	def createThread(self):
		return Thread(target=self.mainLoop, args=[])

	def createBridgeCraneThread(self):
		return Thread(target=self.bridgeCraneLoop, args=[])

	def addMessage(self, msg):
		self.messages.put(msg)

	def stop(self):
		self.running = False

