from Queue import Queue
from threading import Thread
from collections import deque, namedtuple
from math import sqrt, atan2, cos, sin, pi
from time import sleep, time
from message import Message
from field import Field
from random import randrange

(MOVE_ARM, HOOK_UP, HOOK_DOWN, GRAB, DROP, NOTHING) = range(10, 16)
(TAKE_OFF, PASS_ON, LOAD_SHIP, KEEP_BUSY) = range(20,24)

class Crane:
	def __init__(self, id, position, rangeSight, reach, height, neighbours, map):
		self.id = id
		self.position = position
		self.rangeSight = rangeSight
		self.reach = reach
		self.height = height
		self.angle = 0 # in radians, clockwise
		self.hookDistance = 1
		self.hookHeight   = height
		self.neighbours   = neighbours
		self.map = map

		self.crate = None

		self.messages = Queue()
		self.tasks = deque()
		self.instructions = deque()

		self.directToShip = 0 #boolean value if the crane has direct access to the ship
		self.toShip = []
		self.wanted = set() #all packages wanted by ship
		self.onMyArea = {} #packages on my field after examineSurroundings
		self.inWay  = {}

		self.thread = self.createThread()
		self.running = True
		self.thread.start()

	def moveArm(self, alfa, dist):
		alfaStep = 0.03 * (-1 if alfa < 0 else 1)
		distStep = 0.03 * (-1 if dist < 0 else 1)

		while abs(alfa) > abs(alfaStep):
			self.angle += alfaStep
			alfa -= alfaStep
			if abs(dist) > abs(distStep):
				self.hookDistance += distStep
				dist -= distStep
			sleep(0.03)
		self.angle += alfa

		while abs(dist) > abs(distStep):
			self.hookDistance += distStep
			dist -= distStep
			sleep(0.03)
		self.hookDistance += dist
	
	def hookDown(self, dist):
		distStep = 0.5
		while dist > distStep:
			self.hookHeight -= distStep
			dist -= distStep
			sleep(0.03)
		self.hookHeight -= dist
		sleep(0.03)

	def hookUp(self, dist):
		distStep = 0.5
		while dist > distStep:
			self.hookHeight += distStep
			dist -= distStep
			sleep(0.03)
		self.hookHeight += dist
		sleep(0.03)

	def grab(self):
		sleep(0.03)
		y = int(round(sin(self.angle)*self.hookDistance)) + self.position[0]
		x = int(round(cos(self.angle)*self.hookDistance)) + self.position[1]
		print self.id, "grab from", (y,x)
		self.crate = self.map.map[y][x].removeCrateFromTop()
	
	def drop(self):
		sleep(0.03)
		y = int(round(sin(self.angle)*self.hookDistance)) + self.position[0]
		x = int(round(cos(self.angle)*self.hookDistance)) + self.position[1]
		print self.id, "drop on", (y,x)
		self.map.map[y][x].putCrateOnTop(self.crate)
		self.crate = None

	def doNothing(self):
		for i in range(0,5):
			self.angle += 0.03
			sleep(0.05)

	def moveContainer(self, pos1, pos2):
		def calcAngleAndShift(pos, armAngle, hookDist):
			(dy, dx) = (pos[0] - self.position[0], pos[1] - self.position[1])
			rotate = ((atan2(dy,dx) - armAngle + pi) % (2*pi)) - pi
			hookShift = sqrt(dy*dy + dx*dx) - hookDist
			return (rotate, hookShift)

		(rotate1, shift1) = calcAngleAndShift(pos1, self.angle, self.hookDistance)
		(rotate2, shift2) = calcAngleAndShift(pos2, self.angle+rotate1, self.hookDistance+shift1)
		stack1Size = 1
		stack2Size = 0

		return [
			(HOOK_UP, [self.height - self.hookHeight]),
			(MOVE_ARM, [rotate1, shift1]), 
			(HOOK_DOWN, [self.height - stack1Size]),
			(GRAB, []),
			(HOOK_UP, [self.height - self.hookHeight]),
			(MOVE_ARM, [rotate2, shift2]), 
			(HOOK_DOWN, [self.height - stack2Size]),
			(DROP, [])
		]

	def takeOff(self, pos):
		free = None
		while True:
			freeY = randrange(-self.reach, self.reach+1) + self.position[0]
			freeX = randrange(-self.reach, self.reach+1) + self.position[1]
			free = (freeY, freeX)
			if free != pos and self.map.inRange(free) and self.map.map[freeY][freeX].type == Field.STORAGE_TYPE:
				break
		return self.moveContainer(pos, free)

	def passOn(self, pos, crane):
		rect = self.map.commonArea(self, crane)
		(topLeft, h, w) = rect
		common = None
		while True:
			commonY = topLeft[0] + randrange(0, h)
			commonX = topLeft[1] + randrange(0, w)
			common = (commonX,commonY)
			if common != self.position and common != crane.position and self.map.inRange(common) and self.map.map[commonY][commonX].type == Field.STORAGE_TYPE:
				break

		print "common field", self.id, crane.id, "-", common
		return self.moveContainer(pos, common)
	
	def loadShip(self, pos):
		randY = randrange(-self.reach, self.reach)
		shipPos = (self.position[0] + randY, self.map.colNum-1)
		return self.moveContainer(pos, shipPos)
	
	def keepBusy(self):
		return [(NOTHING, [])]

	def informOthers(self):
		for c in self.neighbours:
			if c not in self.toShip:
				c.addMessage(Message(self, Message.HAVE_SHIP_PATH, []))

	def startMeasureTime(self, containerId, craneId):
		self.inWay[containerId] = (craneId, time())

	def stopMeasureTime(self, containerId, stop):
		(craneId, start) = self.inWay[containerId]
		measure = start - stop
		del (self.inWay[containerId])
		return (craneId, measure)

	def addMessage(self, msg):
		self.messages.put(msg)

	def addNeighbour(self, n):
		self.neighbours.append(n)

	def examineSurroundings(self):
		self.onMyArea.clear()
		for y in xrange(self.position[0]-self.reach, self.position[0]+self.reach+1):
			for x in xrange(self.position[1]-self.reach, self.position[1]+self.reach+1):
				if( x < self.map.colNum and y < self.map.rowNum):
					if(self.map.fieldType(y, x) == Field.STORAGE_TYPE):
						field = self.map.field(y, x).getAllCratesIds()
						for i in xrange(len(field)):
							self.onMyArea[field[i]] = (y, x)
			if self.position[1] + self.reach >= self.map.colNum-1:
				if self.directToShip == 0:
					self.directToShip = 1 #maybe should be in init in order to not check it whole time

	def readMessage(self, msg):
		if msg.type == Message.SEARCH_PACKAGE:
			self.wanted.update(msg.data)
			print "got message: ship needs %s \n" % (self.wanted)
			for pkg in msg.data:
				if pkg in self.onMyArea:
					print "%s is on %s" % (pkg, self.onMyArea[pkg])

		elif msg.type == Message.PACKAGE_DELIVERED:
			if msg.data.containerId in self.inWay:
				self.stopMeasureTime(msg.data.stop)
			self.wanted.discard(msg.data.containerId)

		elif msg.type == Message.HAVE_SHIP_PATH:
			self.toShip.append(msg.sender)
			self.informOthers()

	def readMessages(self, left=5):
		while (left > 0 and not self.messages.empty()):
			self.readMessage(self.messages.get())
			left -= 1

	def doInst(self, inst):
		cmd = {
			MOVE_ARM:  self.moveArm,
			HOOK_UP:   self.hookUp,
			HOOK_DOWN: self.hookDown,
			GRAB:	   self.grab,
			DROP:	   self.drop,
			NOTHING:   self.doNothing
		}.get(inst[0])
		cmd(*inst[1])
	
	def decomposeTask(self, task):
		dec = {
			TAKE_OFF:  self.takeOff,
			PASS_ON:   self.passOn,
			LOAD_SHIP: self.loadShip,
			KEEP_BUSY: self.keepBusy
		}.get(task[0])
		return dec(*task[1])

	def isInArea(self, pos):
		(x, y) = self.position
		return max(abs(pos[0]-x), abs(pos[1]-y)) <= self.reach

	def getPackageLevel(self, crateId):
		(y,x) = self.onMyArea[crateId]
		return self.map.map[y][x].getCratePosition(crateId)

	def getPackageToDeliver(self):
		res = None
		resLvl = 10000
		for pkg in self.wanted:
			if pkg in self.onMyArea:
				isMine = True
				pkg_pos = self.onMyArea[pkg]
				if pkg_pos[1] == self.map.colNum-1:
					isMine = False
				else:
					for c in self.toShip:
						if c.isInArea(pkg_pos):
							isMine = False
							break
				if isMine:
					pkgLvl = self.getPackageLevel(pkg)
					if resLvl > pkgLvl:
						res = pkg
						resLvl = pkgLvl
		return res


	def doWork(self):
		if self.directToShip == 1:
			self.directToShip = 2
			print self.id, "I'm near ship!"
			self.informOthers()
		
		if not self.tasks and not self.instructions:
			if self.toShip or self.directToShip:
				pkg = self.getPackageToDeliver()
				if pkg:
					pkg_pos = self.onMyArea[pkg]
					tasks = [(TAKE_OFF, [pkg_pos])] * self.getPackageLevel(pkg)
					if self.directToShip:
						tasks.append((LOAD_SHIP, [pkg_pos]))
					else:
						nextCrane = self.toShip[0]
						tasks.append((PASS_ON, [pkg_pos, nextCrane]))
					self.tasks.extend(tasks)
				else:
					self.tasks.append((KEEP_BUSY, []))
			else:
				self.tasks.append((KEEP_BUSY, []))

		if not self.instructions:
			task = self.tasks.popleft()
			inst = self.decomposeTask(task)
			self.instructions.extend(inst)

		self.doInst(self.instructions.popleft())
	
	def mainLoop(self):
		while self.running:
			self.examineSurroundings()
			self.readMessages()
			self.doWork()

	def createThread(self):
		return Thread(target=self.mainLoop, args=[])

	def stop(self):
		self.running = False

