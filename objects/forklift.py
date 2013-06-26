from Queue import Queue
from threading import Thread
from time import sleep, time
from collections import deque
from math import pi
from message import Message
from field import Field

(EXPLORE, GRAB, TO_CRANE, DROP, NEGOTIATE) = range(300, 305)

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
		self.movementTotal = 0
		self.turnTotal = 0

		self.toVisit = set() # all unvisited island fields
		self.founded = {} # founded packages on current island
		self.freeFields = set() # fields of island free of packages stacks
		self.currentTask = EXPLORE # current forklift task

		self.field = None 

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
		SPEED = 0.04
		for i in range(0, int(1.0/SPEED)):
			y = self.position[0] + self.dir[0] * SPEED
			x = self.position[1] + self.dir[1] * SPEED
			self.position = (y,x)
			sleep(0.02)
		self.fixPos()
		self.movementTotal += 1

	def turnLeft(self):
		ANG = 0.04
		for i in range(0, int(pi/2 / ANG)):
			self.angle -= ANG
			self.turnTotal += ANG
			sleep(0.02)
		self.dir = (-self.dir[1], self.dir[0])
		self.fixAngle()

	def turnRight(self):
		ANG = 0.04
		for i in range(0, int(pi/2 / ANG)):
			self.angle += ANG
			self.turnTotal += ANG
			sleep(0.02)
		self.dir = (self.dir[1], -self.dir[0])
		self.fixAngle()

	def grab(self):
		sleep(1)
		y=self.position[0] + self.dir[0]
		x=self.position[1] + self.dir[1]
		self.crate = self.map[y,x].removeCrateFromTop()
		if not self.map[y,x].getAllCratesIds:
			self.freeFields.add((y,x))
		
	def drop(self):
		sleep(1)
		y=self.position[0] + self.dir[0]
		x=self.position[1] + self.dir[1]
		self.map[y,x].putCrateOnTop(self.crate)
		self.freeFields.discard((y,x))
		self.crate = None
	
	def addMessage(self, msg):
		self.messages.put(msg)

	def readMessage(self, msg):
		if msg.type == Message.SEARCH_PACKAGE:
			self.wanted.update(msg.data)

	def readMessages(self, left=5):
		while (left > 0 and not self.messages.empty()):
			self.readMessage(self.messages.get())
			left -= 1

	def examineSurroundings(self):
		a = 1
		for y in range(self.position[0]-a, self.position[0]+a+1):
			for x in range(self.position[1]-a, self.position[1]+a+1):
				self.toVisit.discard((y,x))

				if (y,x) == self.position:
					continue
				
				if self.map.inMapBounds((y,x)) and self.map.fieldType(y,x) == Field.ROAD_TYPE:
					crates = self.map[y,x].getAllCratesIds()
					if crates:
						for c in crates:
							if c not in self.founded:
								self.founded[c] = (y,x)
								print "FOUNDED %d AT %s" % (c, (y,x))
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
			print("Forklift", self.id, "-", self.position, self.dir, 180.0*(self.angle/pi), self.toVisit)

	def findPath(self, goal):
		v = dict()
		q = deque([self.position])
		
		pos = None
		
		while q and not pos:
			c = q.popleft()

			for x in [(c[0]+a[0], c[1]+a[1]) for a in [(0,1), (1,0), (0,-1), (-1,0)]]:
				if goal(x):
					v[x] = c
					pos = x
				elif x not in v and x in self.freeFields:
					v[x] = c
					q.append(x)

		if pos == None:
			return None
		
		q.clear()
		while pos != self.position:
			q.appendleft(pos)
			pos = v[pos]
		
		return q

	def doNothing(self):
		sleep(0.2)
	

	def doWork(self):
		# i have some way to go
		if self.way:
			self.continueWay()

		# i'm near wanted package
		elif self.currentTask == NEGOTIATE:
			#### NEGOTIATIONS will be here: ####
			crane = None
			####################################

			# this will be changed after implementing negotiations
			self.wayToCrane = self.findPath(lambda x: self.map[x] and self.map[x].type == Field.STORAGE_TYPE)
			self.currentTask = GRAB

		# i have to grab something
		elif self.currentTask == GRAB:
			self.grab()
			if self.crate.id in self.wanted:
				self.currentTask = TO_CRANE
				self.way = self.wayToCrane
			else:
				self.field = (self.position[0] + self.dir[0], self.position[1] + self.dir[1])
				self.way = self.findPath(lambda x: x != self.field and self.map.inMapBounds(x) and x not in self.wayToCrane and self.map[x].countCrates() < Field.STACK_MAX_SIZE)
				self.currentTask = DROP

		elif self.currentTask == DROP:
			self.drop()
			self.currentTask = GRAB
			self.way = self.findPath(lambda x: x == self.field)


		# i'm near crane now
		elif self.currentTask == TO_CRANE:
			self.wanted.discard(self.crate.id)
			# pass package to crane
			self.drop()
			self.currentTask = EXPLORE
			
		# no tasks:
		else:
			self.way = self.findPath(lambda x: x in self.toVisit)

			if self.way:
				self.currentTask = EXPLORE
			else:
				# looking for interested fields on my island
				fields = [self.founded[w] for w in self.wanted if w in self.founded and self.map[self.founded[w]].type == Field.ROAD_TYPE]
				self.way = self.findPath(lambda x: x in fields)
				if self.way:
					self.currentTask = NEGOTIATE
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

