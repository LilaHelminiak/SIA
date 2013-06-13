from Queue import Queue
from threading import Thread
from collections import deque, namedtuple
from math import sqrt, atan2, cos, sin, pi
from time import sleep, time
from message import Message
from field import Field
from random import randrange, choice, gauss

(MOVE_ARM, HOOK_UP, HOOK_DOWN, GRAB, DROP, SEND_MSG, START_MEASURE) = range(10, 17)
(TAKE_OFF, PUT_SMWHR, PASS_ON, LOAD_SHIP, KEEP_BUSY, INFORM_SHIP, MEASURE_TIME) = range(20,27)
INFINITY = 10000000

class Crane:
	def __init__(self, id, position, rangeSight, reach, height, map):
		self.id = id
		self.position = position
		self.rangeSight = rangeSight
		self.reach = reach
		self.height = height
		self.angle = 0 # in radians, clockwise
		self.hookDistance = 1
		self.hookHeight   = height
		self.neighbours   = []
		self.map = map

		self.crate = None
		self.averageTime = 0
		self.passedPackages = 0

		self.messages = Queue()
		self.negotiate = Queue()
		self.tasks = deque()
		self.instructions = deque()

		self.directToShip = 0 #boolean value if the crane has direct access to the ship
		self.toShip = []
		self.hops = INFINITY # number of agents between crane and ship on the way
		self.wanted = set() #all packages wanted by ship
		self.onMyArea = {} #packages on my field after examineSurroundings
		self.inWay  = {}
		self.negotiations = False #checks if negotiations are on 

		self.thread = self.createThread()
		self.running = True
		self.thread.start()

	def getHookPosition(self):
		y = int(round(sin(self.angle)*self.hookDistance)) + self.position[0]
		x = int(round(cos(self.angle)*self.hookDistance)) + self.position[1]
		return (y,x)

	# atomic functions that crane can do at once
	def moveArmInst(self, alfa, dist):
		self.angle += alfa
		self.hookDistance += dist

	def hookDownInst(self, dist):
		self.hookHeight -= dist

	def hookUpInst(self, dist):
		self.hookHeight += dist
	
	def grabInst(self):
		self.hookHeight = abs(round(self.hookHeight))
		pos = self.getHookPosition()
		self.crate = self.map[pos].removeCrateFromTop()
		print self.id, "grab from", pos, ", hook height:", self.hookHeight, "id: ", self.crate.id
	
	def dropInst(self):
		self.hookHeight = abs(round(self.hookHeight))
		pos = self.getHookPosition()
		self.map[pos].putCrateOnTop(self.crate)
		print self.id, "drop on", pos, ", hook height:", self.hookHeight, "id: ", self.crate.id
		self.crate = None

	def sendMessageInst(self, receiver, message):
		receiver.addMessage(message)

	def startMeasureTimeInst(self, containerId, craneId):
		self.inWay[containerId] = time()
	
	def doAtomicInst(self, inst):
		cmd = {
			MOVE_ARM:  self.moveArmInst,
			HOOK_UP:   self.hookUpInst,
			HOOK_DOWN: self.hookDownInst,
			GRAB:      self.grabInst,
			DROP:      self.dropInst,
			SEND_MSG:  self.sendMessageInst,
			START_MEASURE: self.startMeasureTimeInst
		}.get(inst[0])
		cmd(*inst[1])
	
	# these functions decompose crane actions to more atomic instructions
	def moveArmDecompose(self, alfa, dist):
		aStep, aDir = 0.04, 1 if alfa > 0 else -1
		dStep, dDir = 0.04, 1 if dist > 0 else -1
		inst = []
		aL = [aStep] * int(abs(alfa)/aStep) + [abs(alfa) % aStep]
		dL = [dStep] * int(abs(dist)/dStep) + [abs(dist) % dStep]
		if len(aL) > len(dL):
			dL.extend([0] * (len(aL) - len(dL)))
		elif len(aL) < len(dL):
			aL.extend([0] * (len(dL) - len(aL)))
		for (a, d) in zip(aL, dL):
			inst.append((MOVE_ARM, [a*aDir, d*dDir]))
		return inst
	
	def hookDownDecompose(self, dist):
		dStep = 0.7
		return [(HOOK_DOWN, [dStep])] * int(dist/dStep) + [(HOOK_DOWN, [dist % dStep])]
			
	def hookUpDecompose(self, dist):
		dStep = 0.7
		return [(HOOK_UP, [dStep])] * int(dist/dStep) + [(HOOK_UP, [dist % dStep])]

	def grabDecompose(self):
		return [(GRAB,[])]
			
	def dropDecompose(self):
		return [(DROP,[])]
			
	def sendMessageDecompose(self, receiver, message):
		return [(SEND_MSG,[receiver, message])]
			
	def startMeasureTimeDecompose(self, containerId, craneId):
		return [(START_MEASURE, [containerId])]
			
	# this function decompose "move crate from pos1 to pos2" action
	# to atomic instructions
	def calcAngleAndShift(self, pos, armAngle, hookDist):
		(dy, dx) = (pos[0] - self.position[0], pos[1] - self.position[1])
		rotate = ((atan2(dy,dx) - armAngle + pi) % (2*pi)) - pi
		hookShift = sqrt(dy*dy + dx*dx) - hookDist
		return (rotate, hookShift)

	def pickUpDecompose(self, pos1):
		(rotate1, shift1) = self.calcAngleAndShift(pos1, self.angle, self.hookDistance)
		stack1Size = self.map[pos1].countCrates()

		return (
			self.hookUpDecompose(self.height - self.hookHeight) +
			self.moveArmDecompose(rotate1, shift1) +
			self.hookDownDecompose(self.height - stack1Size) +
			self.grabDecompose()
		)

	def putDownDecompose(self, pos2):
		(rotate2, shift2) = self.calcAngleAndShift(pos2, self.angle, self.hookDistance)
		stack2Size = self.map[pos2].countCrates()

		return (
			self.hookUpDecompose(self.height - self.hookHeight) +
			self.moveArmDecompose(rotate2, shift2) +
			self.hookDownDecompose(self.height - stack2Size) +
			self.dropDecompose()
		)

	# functions of tasks that crane has to do
	def takeOff(self, pos):
		return self.pickUpDecompose(pos)

	def putSomewhere(self):
		pos = self.getHookPosition()
		free = None
		while True:
			freeY = randrange(-self.reach, self.reach+1) + self.position[0]
			freeX = randrange(-self.reach, self.reach+1) + self.position[1]
			free = (freeY, freeX)
			f = self.map[free]
			commonFields = [field for cranes in self.neighbours for field in self.map.commonStorageFields(self, cranes)]				
			if free != pos and f and f.type == Field.STORAGE_TYPE and f.countCrates() < f.STACK_MAX_SIZE:# and (free not in commonFields):
				break
		print '%s drops garbage' % (self.id)
		return self.putDownDecompose(free)

	def passOn(self, crane):
		commonFields = self.map.commonStorageFields(self,crane)
		rect = self.map.commonArea(self, crane)
		(topLeft, h, w) = rect
		common = (commonFields[randrange(0, len(commonFields))])
		i = 0
		pos = self.getHookPosition()
		while self.map.distance(pos, common) > self.map.distance(pos, commonFields[i]):
			msg = Message(self, Message.NEGOTIATE_FIELD, [common,  commonFields[i]])		       
			self.sendMessageInst(crane, msg)
			while(self.negotiate.empty()):
			    sleep(0.2)
			    self.readMessages()
			ans = self.negotiate.get()
			if ans.type == Message.NEGOTIATE_ANSWER:
			    if ans.data[0] == 'yes':
				rc=common
				common = commonFields[i]
				print 'negotiations (%s and %s): successfull. Common field is %s instead for %s' % (self.id, crane.id, common, rc)
				break
			if i+1 < len(commonFields):
			    i = i+1
			else:
			    break
			
		return self.putDownDecompose(common)
	
	def loadShip(self):
		pos = self.getHookPosition()
		shipPos = None
		while True:
			shipY = pos[0]
			if pos[0] == self.position[0]:
				if pos[0] + 1 < self.map.rowNum:
					shipY = pos[0]+1
				else:
					shipY = pos[0]-1
			shipX = self.map.colNum-1
			shipY = self.position[0]+randrange(-self.reach, self.reach)
			shipPos = (shipY, shipX)
			f = self.map[shipPos]
			if shipPos != self.position and f and f.type == Field.SHIP_TYPE and f.isStackable() and f.countCrates() < f.STACK_MAX_SIZE:
				break
		return self.putDownDecompose(shipPos)

	
	def keepBusy(self):
		rotate = ((pi/2 - self.angle + pi) % (2*pi)) - pi
		return (
			self.hookUpDecompose(self.height - self.hookHeight) +
			self.moveArmDecompose(rotate, 0)
		)

	def informShip(self, pkg):
		msg = Message(self, Message.PACKAGE_LOADED, pkg)
		return [(SEND_MSG, [self.map.ship, msg]) ]

	def startMeasureTime(self, packageId, craneId):
		return [(START_MEASURE, [packageId, craneId]) ]
		
	def decomposeTask(self, task):
		dec = {
			TAKE_OFF:  self.takeOff,
			PUT_SMWHR: self.putSomewhere,
			PASS_ON:   self.passOn,
			LOAD_SHIP: self.loadShip,
			KEEP_BUSY: self.keepBusy,
			INFORM_SHIP: self.informShip,
			MEASURE_TIME: self.startMeasureTime
		}.get(task[0])
		return dec(*task[1])

	####################################

	def informOthers(self, recipients):
		for c in recipients:
			if c not in self.toShip:
				c.addMessage(Message(self, Message.HAVE_SHIP_PATH, self.hops))

	def stopMeasureTime(self, containerId, stop):
		start = self.inWay[containerId]
		measure = stop - start
		self.averageTime = self.averageTime * self.passedPackages + measure / (self.passedPackages+1)
		self.passedPackages += 1
		del (self.inWay[containerId])
		print "%d my time: %f" % (self.id,self.averageTime)

	def addMessage(self, msg):
		self.messages.put(msg)
		
	def addNegotiate(self, msg):
		print "%s sentds to %s %s)" % (msg.sender.id, self.id, msg.data)
		self.negotiate.put(msg)

	def addNeighbours(self, l):
		self.neighbours.extend(l)

	def examineSurroundings(self):
		self.onMyArea.clear()
		for y in xrange(self.position[0]-self.reach, self.position[0]+self.reach+1):
			for x in xrange(self.position[1]-self.reach, self.position[1]+self.reach+1):
				if( x < self.map.colNum and y < self.map.rowNum):
					pos = (y,x)
					field = self.map[pos]

					if field.type == Field.SHIP_TYPE:
						if self.directToShip == 0:
							self.directToShip = 1

					elif field.type == Field.STORAGE_TYPE:
						for cid in field.getAllCratesIds():
							self.onMyArea[cid] = pos

	def readMessage(self, msg):
		if msg.type == Message.SEARCH_PACKAGE:
			self.wanted.update(msg.data)
			print "got message: ship needs %s \n" % (self.wanted)
			for pkg in msg.data:
				if pkg in self.onMyArea:
					print "%s is on %s" % (pkg, self.onMyArea[pkg])

		elif msg.type == Message.PACKAGE_DELIVERED:
			(p, t) = msg.data
			if p in self.inWay:
				self.stopMeasureTime(p, t)
			self.wanted.discard(p)

		elif msg.type == Message.HAVE_SHIP_PATH:
			if msg.data+1 < self.hops:
				self.hops = msg.data + 1
				self.toShip = [msg.sender]
				self.informOthers(self.neighbours)
				print(">>> %d: new best way by %d in %d step[s]" % (self.id, msg.sender.id, self.hops))
			elif msg.data+1 == self.hops:
				if msg.sender not in self.toShip:
					self.toShip.append(msg.sender)
					self.informOthers(self.neighbours)
					print(">>> %d: next best way by %d in %d step[s]" % (self.id, msg.sender.id, self.hops))
		
		elif msg.type == Message.NEGOTIATE_FIELD:
			old_field = msg.data[0]
			new_field = msg.data[1]
			print "%s negotiates, old %s vs new %s" % (self.id, old_field, new_field)
			if self.directToShip == 0:
				goal_field = self.map.commonStorageFields(self, msg.sender)[0]
				if(self.map.distance(old_field, goal_field) >= self.map.distance(new_field, goal_field)):
					response = Message(self, Message.NEGOTIATE_ANSWER, ["yes"] )
				else:
					response = Message(self, Message.NEGOTIATE_ANSWER, ["no"] )
			else:
				print "#####old field dist: %s, new dist: %s" % (self.map.distance(old_field, (self.map.colNum-1, old_field[1])), self.map.distance(new_field, (self.map.colNum-1, new_field[1])))
				if(self.map.distance(old_field, (self.map.colNum-1, old_field[1]))) >= self.map.distance(new_field, (self.map.colNum-1, new_field[1])):
					response = Message(self, Message.NEGOTIATE_ANSWER, ["yes"] )
				else:
					response = Message(self, Message.NEGOTIATE_ANSWER, ["no"] )
			msg.sender.addNegotiate(response)
			

	def readMessages(self, left=5):
		while (left > 0 and not self.messages.empty()):
			self.readMessage(self.messages.get())
			left -= 1

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
			self.hops = 0
			print self.id, "I'm near ship! Must tell others!"
			self.informOthers(self.neighbours)
		
		if not self.tasks and not self.instructions:
			if self.toShip or self.directToShip:
				pkg = self.getPackageToDeliver()
				if pkg:
					pkg_pos = self.onMyArea[pkg]
					tasks = [(TAKE_OFF, [pkg_pos]), (PUT_SMWHR, [])] * self.getPackageLevel(pkg)
					if self.directToShip:
						tasks.append((TAKE_OFF, [pkg_pos]))
						tasks.append((LOAD_SHIP, []))
						tasks.append((INFORM_SHIP, [pkg]))
					else:
						# add here negotiations #

						##########################
						n = len(self.toShip)
						pos = min(int(abs(gauss(0, 0.7) * n)), n-1)
						nextCrane = self.toShip[pos]

						tasks.append((TAKE_OFF, [pkg_pos]))
						tasks.append((PASS_ON, [nextCrane]))
						tasks.append((MEASURE_TIME, [pkg, nextCrane.id]))
					self.tasks.extend(tasks)
				else:
					self.tasks.append((KEEP_BUSY, []))
			else:
				self.tasks.append((KEEP_BUSY, []))

		if not self.instructions:
			task = self.tasks.popleft()
			inst = self.decomposeTask(task)
			self.instructions.extend(inst)

		self.doAtomicInst(self.instructions.popleft())
	
	def mainLoop(self):
		SLEEP_SEC = 0.02
		
		while self.running:
			while self.running and self.map.pause:
				sleep(0.1)
			
			t = time()

			self.examineSurroundings()
			self.readMessages()
			self.doWork()

			sleep(max(SLEEP_SEC - (time() - t), 0))

	def createThread(self):
		return Thread(target=self.mainLoop, args=[])

	def stop(self):
		self.running = False

