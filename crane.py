from Queue import Queue
from threading import Thread
from collections import deque, namedtuple
from math import sqrt, atan2, cos, sin, pi
from time import sleep, time
from message import Message
from field import Field
from random import randrange, choice

(MOVE_ARM, HOOK_UP, HOOK_DOWN, GRAB, DROP, SEND_MSG) = range(10, 16)
(TAKE_OFF, PASS_ON, LOAD_SHIP, KEEP_BUSY) = range(20,24)

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
                pos = self.getHookPosition()
                self.crate = self.map[pos].removeCrateFromTop()
                print self.id, "grab from", pos, ", hook height:", self.hookHeight, "id: ", self.crate.id
        
        def dropInst(self):
                pos = self.getHookPosition()
                self.map[pos].putCrateOnTop(self.crate)
                print self.id, "drop on", pos, ", hook height:", self.hookHeight
                self.crate = None

        def sendMessageInst(self, receiver, message):
                receiver.addMessage(message)

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
                        
        # this function decompose "move crate from pos1 to pos2" action
        # to atomic instructions
        def moveContainerDecompose(self, pos1, pos2):
                def calcAngleAndShift(pos, armAngle, hookDist):
                        (dy, dx) = (pos[0] - self.position[0], pos[1] - self.position[1])
                        rotate = ((atan2(dy,dx) - armAngle + pi) % (2*pi)) - pi
                        hookShift = sqrt(dy*dy + dx*dx) - hookDist
                        return (rotate, hookShift)

                (rotate1, shift1) = calcAngleAndShift(pos1, self.angle, self.hookDistance)
                (rotate2, shift2) = calcAngleAndShift(pos2, self.angle+rotate1, self.hookDistance+shift1)
                stack1Size = self.map[pos1].countCrates()
                stack2Size = self.map[pos2].countCrates()

                return (
                        self.hookUpDecompose(self.height - self.hookHeight) +
                        self.moveArmDecompose(rotate1, shift1) +
                        self.hookDownDecompose(self.height - stack1Size) +
                        self.grabDecompose() + 
                        self.hookUpDecompose(self.height - stack1Size) +
                        self.moveArmDecompose(rotate2, shift2) +
                        self.hookDownDecompose(self.height - stack2Size - 1) +
                        self.dropDecompose()
                )

        # functions of tasks that crane has to do
        def takeOff(self, pos):
                free = None
                while True:
                        freeY = randrange(-self.reach, self.reach+1) + self.position[0]
                        freeX = randrange(-self.reach, self.reach+1) + self.position[1]
                        free = (freeY, freeX)
                        f = self.map[free]
                        if free != pos and f and f.type == Field.STORAGE_TYPE and f.countCrates() < f.STACK_MAX_SIZE:
                                break
                return self.moveContainerDecompose(pos, free)

        def passOn(self, pos, crane):
                print "testLine common fields for %s and %s" % (self.id, crane.id)
                aList = self.map.commonStorageFields(self,crane)
                for x in xrange(len(aList)):
                        print str(aList[x]) + '\n'
                rect = self.map.commonArea(self, crane)
                (topLeft, h, w) = rect
                common = None
                while True:
                        commonY = topLeft[0] + randrange(0, h)
                        commonX = topLeft[1] + randrange(0, w)
                        common = (commonY,commonX)
                        f = self.map[common]
                        if common != self.position and common != crane.position and f and f.type == Field.STORAGE_TYPE and f.countCrates() < Field.STACK_MAX_SIZE:
                                break
                return self.moveContainerDecompose(pos, common)
        
        def loadShip(self, pos):
                randY = randrange(-self.reach, self.reach)
                shipPos = None
                while True:
                        shipY = randrange(-self.reach, self.reach+1) + self.position[0]
                        shipX = self.map.colNum-1
                        shipPos = (shipY, shipX)
                        f = self.map[shipPos]
                        if shipPos != self.position and f and f.type == Field.SHIP_TYPE and f.isStackable():
                                break
                        #msg = Message(self, Message.PACKAGE_DELIVERED, [!!!Add here Id of the package which is delivered!!!])
                        #self.map.ship.messages.put(msg)
                msg = Message(self, Message.PACKAGE_DELIVERED, self.map[pos].getTopCrateId())
                return (
                        self.moveContainerDecompose(pos, shipPos) +
                        self.sendMessageDecompose(self.map.ship, msg)
                )

        
        def keepBusy(self):
                rotate = ((pi/2 - self.angle + pi) % (2*pi)) - pi
                return (
                        self.hookUpDecompose(self.height - self.hookHeight) +
                        self.moveArmDecompose(rotate, 0)
                )
        
        def doAtomicInst(self, inst):
                cmd = {
                        MOVE_ARM:  self.moveArmInst,
                        HOOK_UP:   self.hookUpInst,
                        HOOK_DOWN: self.hookDownInst,
                        GRAB:      self.grabInst,
                        DROP:      self.dropInst,
                        SEND_MSG:  self.sendMessageInst
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

        def informOthers(self, recipients):
                for c in recipients:
                        if c not in self.toShip:
                                res = c.addMessage(Message(self, Message.HAVE_SHIP_PATH, []))
                                print self.id, "I have informed", c.id, "with res", res

        def startMeasureTime(self, containerId, craneId):
                self.inWay[containerId] = (craneId, time())

        def stopMeasureTime(self, containerId, stop):
                (craneId, start) = self.inWay[containerId]
                measure = start - stop
                del (self.inWay[containerId])
                return (craneId, measure)

        def addMessage(self, msg):
                self.messages.put(msg)

        def addNeighbours(self, l):
                self.neighbours.extend(l)
                if self.directToShip or self.toShip:
                        self.informOthers(l)

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
                        if msg.data.containerId in self.inWay:
                                self.stopMeasureTime(msg.data.stop)
                        self.wanted.discard(msg.data.containerId)

                elif msg.type == Message.HAVE_SHIP_PATH:
                        self.toShip.append(msg.sender)
                        print self.id, "To ship through", msg.sender.id
                        self.informOthers(self.neighbours)

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
                        print self.id, "I'm near ship! Must tell others!"
                        self.informOthers(self.neighbours)
                
                if not self.tasks and not self.instructions:
                        if self.toShip or self.directToShip:
                                pkg = self.getPackageToDeliver()
                                if pkg:
                                        pkg_pos = self.onMyArea[pkg]
                                        tasks = [(TAKE_OFF, [pkg_pos])] * self.getPackageLevel(pkg)
                                        if self.directToShip:
                                                tasks.append((LOAD_SHIP, [pkg_pos]))
                                        else:
                                                nextCrane = choice(self.toShip)
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

