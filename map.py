import sys
from math import *
from field import *
from display import *
from crane import *
from ship import *

class Map:

	def __init__(self, rowNum, colNum, display):
		self.rowNum = rowNum
		self.colNum = colNum
		self.display = display
		self.pause = True
		self.map = [[Field(Field.STORAGE_TYPE, []) for col in xrange(colNum)] for row in xrange(rowNum)]
		
		self.map[0][0] = Field(Field.STORAGE_TYPE, [Crate(1, 3), Crate(5, 2), Crate(22, 3)])
		self.map[2][6] = Field(Field.STORAGE_TYPE, [Crate(11, 3), Crate(12, 2), Crate(13, 3), Crate(10,1)])
		self.map[4][6] = Field(Field.STORAGE_TYPE, [Crate(14, 3), Crate(15, 2), Crate(16, 3), Crate(17,2)])
		self.map[4][4] = Field(Field.STORAGE_TYPE, [Crate(8, 3), Crate(772, 2)])
		self.map[3][2] = Field(Field.STORAGE_TYPE, [Crate(7, 3), Crate(432,3), Crate(433,1)])
		self.map[6][2] = Field(Field.STORAGE_TYPE, [Crate(2, 3), Crate(32,3), Crate(33,1)])
		c1 = Crane(1, (1, 1), 3, 1, 10, self)
		c2 = Crane(2, (2, 3), 3, 1, 10, self)
		c3 = Crane(3, (3, 5), 3, 2, 10, self)
		c4 = Crane(4, (5, 3), 3, 1, 10, self)
		c5 = Crane(5, (4, 1), 3, 1, 10, self)
		c1.addNeighbours([c2])
		c2.addNeighbours([c1, c3, c5])
		c3.addNeighbours([c2, c4])
		c4.addNeighbours([c3, c5])
		c5.addNeighbours([c2, c4])
		self.map[1][1] = Field(Field.CRANE_TYPE, [c1])
		self.map[2][3] = Field(Field.CRANE_TYPE, [c2])
		self.map[3][5] = Field(Field.CRANE_TYPE, [c3])
		self.map[5][3] = Field(Field.CRANE_TYPE, [c4])
		self.map[4][1] = Field(Field.CRANE_TYPE, [c5])
		self.ship = Ship(self, [c1, c2, c3, c4, c5], [7, 772, 8, 5, 2, 32], 0, self.rowNum - 1, 2.0)
		for i in xrange(self.ship.topRow, self.ship.bottomRow + 1):
			self.map[i][self.colNum - 1] = Field(Field.SHIP_TYPE, [])

		# start
		self.pause = False
		
	
	def stopThreads(self):
		for i in xrange(self.rowNum):
			for j in xrange(self.colNum):
				if self.fieldType(i, j) == Field.CRANE_TYPE:
					self.field(i, j).getCrane().stop()
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
		
		
