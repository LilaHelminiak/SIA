import sys
from math import *
from field import *
from display import *
from crane import *
from ship import *

class Map:

	def __init__(self, fileName):
		try:
			f = open(fileName, "r")
		except:
			raise Exception("Error when reading the file.")

		self.pause = True
		self.display = Display(940, 750, 100, 25)

		t = [int(x) for x in f.readline().split()] # mapHeight mapWidth
		f.readline() # empty line 
		self.rowNum = t[0]
		self.colNum = t[1]
		self.map = [[Field(Field.ROAD_TYPE, []) for col in xrange(self.colNum)] for row in xrange(self.rowNum)]
		for y in xrange(self.rowNum):
			for x in xrange(self.colNum-1, self.colNum):
				self.map[y][x] = Field(Field.SHIP_TYPE, [])

		
		cranesNum = int(f.readline()) # cranesNumber
		cranesList = []
		for _ in xrange(cranesNum):
			t = [int(x) for x in f.readline().split()] # crane_id crane_row crane_column crane_range crane_reach crane_height
			crane = Crane(t[0], (t[1], t[2]), t[3], t[4], t[5], self)
			cranesList.append(crane)
			self.map[t[1]][t[2]] = Field(Field.CRANE_TYPE, [crane])
			for y in xrange(t[1]-t[4], t[1]+t[4]+1):
				for x in xrange(t[2]-t[4], t[2]+t[4]+1):
					if self.inMapBounds((y, x)) and self.map[y][x].type == Field.ROAD_TYPE:
						self.map[y][x] = Field(Field.STORAGE_TYPE, [])
		f.readline() # empty line
		
		self.edge = {}
		for y in xrange(self.rowNum):
			for x in xrange(self.colNum):
				roadList = []
				if self.map[y][x].type == Field.ROAD_TYPE:
					print 'ROAD TYPE' + str((y,x))
					if self.inMapBounds((y-1,x)) and self.map[y-1][x].type == Field.ROAD_TYPE:
						roadList.append((y-1,x))
					if self.inMapBounds((y+1,x)) and self.map[y+1][x].type == Field.ROAD_TYPE:
						roadList.append((y+1,x))
					if self.inMapBounds((y,x-1)) and self.map[y][x-1].type == Field.ROAD_TYPE:
						roadList.append((y,x-1))
					if self.inMapBounds((y,x+1)) and self.map[y][x+1].type == Field.ROAD_TYPE:
						roadList.append((y,x+1))
					self.edge[(y,x)] = roadList
		
		self.island = []
		for i in self.edge:
			notIn = True
			for a in self.island:
				if i in a:
					notIn = False
					break
			if notIn:
				l = []
				q = Queue()
				q.put(i)
				while not q.empty():
					el = q.get()
					if el not in l:
						l.append(el)
						for j in self.edge[el]:
							q.put(j)
				self.island.append(l)
					
		cratesNum = int(f.readline()) # cratesNumber
		for _ in xrange(cratesNum):
			t = [int(x) for x in f.readline().split()] # crate_id crate_weight crate_row crate_column
			self.map[t[2]][t[3]].putCrateOnTop(Crate(t[0], t[1]))
		f.readline() # empty line		

		for crane1 in cranesList:
			for crane2 in cranesList:
				if crane1 == crane2:
					continue
				if self.commonArea(crane1, crane2) != None:
					crane1.addNeighbours([crane2])

		forkliftsNum = len(self.island) - 1 #int(f.readline()) # forkliftsNumber
		forkliftList = []
		print '@@@' + str(forkliftsNum)
		for i in xrange(forkliftsNum):
			#t = [int(x) for x in f.readline().split()] # forklift_id forklift_row forklift_column
			forklift = Forklift(i+1, (self.island[i][0][0], self.island[i][0][1]), self) #Forklift(t[0], (t[1], t[2]), self)
			forkliftList.append(forklift)
			#self.map[t[1]][t[2]] = Field(Field.STORAGE_TYPE, [forklift])
		#f.readline() # empty line

		t = [int(x) for x in f.readline().split()] # shipFrontCoor shipBackCoor cratesPerMessage messageDelayTime
		neededCrates = [int(x) for x in f.readline().split()] # needed_crate_1_id ... needed_crate_n_id
		self.ship = Ship(self, cranesList, forkliftList, neededCrates, t[0], t[1], t[2], t[3])
		for i in xrange(self.ship.topRow, self.ship.bottomRow + 1):
			self.map[i][self.colNum - 1] = Field(Field.SHIP_TYPE, [])
		f.close()
		
		print 'edges!' + str(self.edge)
		print '!!!!!!!!!!!!!!!!!!ISLANDS:'
		print self.island

		self.pause = False

	
	def stopThreads(self):
		for i in xrange(self.rowNum):
			for j in xrange(self.colNum):
				if self.fieldType(i, j) == Field.CRANE_TYPE:
					self.field(i, j).getCrane().stop()
				elif self.map[i][j].isForkliftPresent() != None:
					self.map[i][j].isForkliftPresent().stop()
		self.ship.stop()


	def __call__(self, pos):
		if(self.inMapBounds(pos) == False):
			return None
		return self.map[pos[0]][pos[1]]


	def __getitem__(self, pos):
		return self(pos)

	
	def fieldType(self, row, col):
		return self.map[row][col].type

		
	def field(self, row, col):
		return self.map[row][col]

		
	def inMapBounds(self, pos):
		(y, x) = pos
		return y >= 0 and x >= 0 and y < self.rowNum and x < self.colNum
		
	#Returns distance between (y1,x1) and (y2,x2) of the given fields
	def distance(self, coordinates1, coordinates2):
		y = fabs(coordinates1[0] - coordinates2[0])
		x = fabs(coordinates1[1] - coordinates2[1])	   
		return sqrt(x*x + y*y)
		
	# Returns ((leftUpperCornerRow, leftUpperCornerCol), height, width) or None
	def commonArea(self, crane1, crane2):
		up = max(crane1.position[0] - crane1.reach, crane2.position[0] - crane2.reach)
		down = min(crane1.position[0] + crane1.reach, crane2.position[0] + crane2.reach)
		left = max(crane1.position[1] - crane1.reach, crane2.position[1] - crane2.reach)
		right = min(crane1.position[1] + crane1.reach, crane2.position[1] + crane2.reach)
		if up > down or left > right:
			return None
		return ((up, left), down - up + 1, right - left + 1)
		
	# Returns list of (y,x) coordinates of storage fields sorted by distance form crane1
	def commonStorageFields(self, crane1, crane2):
		commonFields = []
		rect = self.commonArea(crane1, crane2)
		(topLeft, h, w) = rect
		for i in xrange(h):
			for j in xrange(w):
				commonY = topLeft[0] + i
				commonX = topLeft[1] + j
				common = (commonY,commonX)
				f = self[common]
				if common != crane1.position and common != crane2.position and f and f.type == Field.STORAGE_TYPE and f.countCrates() < Field.STACK_MAX_SIZE:
				    self.distance(crane1.position, common)
				    commonFields.append(((commonY,commonX), self.distance(crane1.position, common)))
		commonFields = sorted(commonFields, key=lambda commonFields: commonFields[1])
		commonF = []
		for x in xrange(len(commonFields)):
		    commonF.append(commonFields[x][0])
		return commonF

	
	def drawMap(self):
		self.display.drawMap(self)
		
		
