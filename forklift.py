from Queue import Queue
from threading import Thread
from time import sleep, time
from collections import deque
from math import pi
from message import Message
from field import Field

(EXPLORE) = range(300, 301)

class Forklift:
	def __init__(self, id, pos, map):
		self.id = id
		self.position = pos
		self.dir = (0,1)
		self.angle = 0
		self.crate = None
		self.map = map
		self.messages = Queue()
		self.way = deque()
		self.wanted = set() #all packages wanted by ship
		self.myIsland = id

		self.toVisit = set() # all unvisited island fields
		self.founded = {} # founded packages on current island
		self.freeFields = set() # fields of island free of packages stacks
		self.currentTask = EXPLORE # current forklift task

		self.thread = self.createThread()
		self.running = True
		self.thread.start()

		self.map[self.position].objectsList = [self]

	def fixPos(self):
		self.position = (int(round(self.position[0])), int(round(self.position[1])))
		self.map[(self.position[0] - self.dir[0]), (self.position[1] - self.dir[1])].objectsList = []
		self.map[self.position].objectsList = [self]

	def fixAngle(self):
		fixedValues = {(0,1): 0, (0,-1): pi, (1,0):pi/2, (-1,0):3*pi/2}
		self.angle = fixedValues[self.dir]

	def forward(self):
		SPEED = 0.02
		for i in range(0, int(1.0/SPEED)):
			y = self.position[0] + self.dir[0] * SPEED
			x = self.position[1] + self.dir[1] * SPEED
			self.position = (y,x)
			sleep(0.02)
		self.fixPos()

	def turnLeft(self):
		ANG = 0.02
		for i in range(0, int(pi/2 / ANG)):
			self.angle -= ANG
			sleep(0.02)
		self.dir = (-self.dir[1], self.dir[0])
		self.fixAngle()

	def turnRight(self):
		ANG = 0.02
		for i in range(0, int(pi/2 / ANG)):
			self.angle += ANG
			sleep(0.02)
		self.dir = (self.dir[1], -self.dir[0])
		self.fixAngle()

	def grab(self):
		sleep(1)
		y=self.position[0] + self.dir[0]
		x=self.position[1] + self.dir[1]
		self.crate = self.map[y,x].discardCrateFromTop()
		
	def drop(self):
		sleep(1)
		y=self.position[0] + self.dir[0]
		self.map[y,x].putCrateOnTop(self.crate)
		self.crate = None
	
	def addMessage(self, msg):
		self.messages.put(msg)

	def readMessage(self, msg):
		if msg.type == Message.SEARCH_PACKAGE:
			self.wanted.update(msg.data)
			print "got message: ship needs %s \n" % (self.wanted)

	def readMessages(self, left=5):
		while (left > 0 and not self.messages.empty()):
			self.readMessage(self.messages.get())
			left -= 1

	def examineSurroundings(self):
		a = 1
		for y in range(self.position[0]-a, self.position[0]+a+1):
			for x in range(self.position[1]-a, self.position[1]+a+1):
				if self.map.inMapBounds((y,x)) and self.map.fieldType(y,x) == Field.ROAD_TYPE:
					self.toVisit.discard((y,x))
					crates = self.map[y,x].getAllCratesIds()
					if crates:
						for c in crates:
							self.founded[c] = (y,x)
					else:
						self.freeFields.add((y,x))

	def continueWay(self):
		if self.way:
			nxt = self.way[0]
			nxt = (nxt[0] - int(self.position[0]), nxt[1] - int(self.position[1]))
			if nxt == self.dir:
				self.way.popleft()
				if self.way:
					self.forward()
			else:
				cp = self.dir[0]*nxt[1] - self.dir[1]*nxt[0]
				if len(self.way) > 1 or self.currentTask != EXPLORE:
					if cp == 1:
						self.turnLeft()
					else:
						self.turnRight()
			print("Forklift", self.id, "-", self.position, self.dir, 180.0*(self.angle/pi))

	def findNearestUnvisitedField(self):
		nearest = None
		minDist = 1000000000

		for pos in self.toVisit:
			dist = (self.position[0]-pos[0])**2 + (self.position[1] - pos[1])**2
			if dist < minDist:
				nearest = pos
				minDist = dist

		return nearest

	
	def findPath(self, pos): # bfs
		v = dict()
		q = deque([self.position])
		
		while q:
			c = q.popleft()
			n = [x for x in self.map.edge[c] if (x == pos or x in self.freeFields) and x not in v]
			
			for x in n:
				v[x] = c
				if x == pos: break
			
			q.extend(n)
		
		q.clear()
		while pos != self.position:
			q.appendleft(pos)
			pos = v[pos]
		
		return q

	def doNothing(self):
		time.sleep(0.2)
	

	def doWork(self):
		if len(self.way) > 1:
			self.continueWay()
		elif self.currentTask == EXPLORE:
			if self.toVisit:
				pos = self.findNearestUnvisitedField()
				self.way = self.findPath(pos)

				print ">>>>>%d WAY: %s" % (self.id,  self.way)
		else:
			self.doNothing()


	def mainLoop(self):
		print '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!MY ID: %s, MY POS: %s' % (self.id, self.position)

		self.toVisit = set(self.map.island[self.myIsland-1])
		self.toVisit.discard(self.position)

		while self.running:
			while self.running and self.map.pause:
				sleep(0.1)
				
			self.readMessages()
			self.examineSurroundings()			
			self.doWork()

	def createThread(self):
		return Thread(target=self.mainLoop, args=[])

	def stop(self):
		self.running = False

