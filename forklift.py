from Queue import Queue
from threading import Thread
from time import sleep, time
from collections import deque
from math import pi

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

		self.thread = self.createThread()
		self.running = True
		self.thread.start()

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
		self.crate = self.map[y,x].removeCrateFromTop()
		
	def drop(self):
		sleep(1)
		y=self.position[0] + self.dir[0]
		self.map[y,x].putCrateOnTop(self.crate)
		self.crate = None
	
	def addMessage(self, msg):
		self.messages.put(msg)

	def readMessage(self, msg):
		pass

	def readMessages(self, left=5):
		while (left > 0 and not self.messages.empty()):
			self.readMessage(self.messages.get())
			left -= 1

	def examineSurroundings(self):
		pass

	def continueWay(self):
		if self.way:
			nxt = self.way[0]
			nxt = (nxt[0] - int(self.position[0]), nxt[1] - int(self.position[1]))
			if nxt == self.dir:
				self.forward()
				self.way.popleft()
			else:
				cp = self.dir[0]*nxt[1] - self.dir[1]*nxt[0]
				if cp == 1:
					self.turnLeft()
				else:
					self.turnRight()
			print("Forklift", self.id, "-", self.position, self.dir, 180.0*(self.angle/pi))

	def doWork(self):
		self.continueWay()

	def mainLoop(self):
		
		# just for test:
		self.position=(0,2)
		self.way = deque([(0,3), (0,4), (0,5), (0,4)] * 2 + [(1,4), (1,5), (0,5)])
		
		while self.running:
			while self.running and self.map.pause:
				sleep(0.1)
			
			self.examineSurroundings()
			self.readMessages()
			self.doWork()

	def createThread(self):
		return Thread(target=self.mainLoop, args=[])

	def stop(self):
		self.running = False

