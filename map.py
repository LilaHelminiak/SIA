import sys
from math import *
from field import *
from display import *
from crane import *

class Map:

	def __init__(self, rowNum, colNum, display):
		self.rowNum = rowNum
		self.colNum = colNum
		self.display = display
		self.map = [[Field(Field.STORAGE_TYPE, []) for col in xrange(colNum)] for row in xrange(rowNum)]
		
		self.map[0][0] = Field(Field.STORAGE_TYPE, [Crate(1, 3), Crate(5, 2), Crate(22, 3)])
		self.map[4][4] = Field(Field.STORAGE_TYPE, [Crate(8, 3), Crate(772, 2)])
		self.map[3][2] = Field(Field.STORAGE_TYPE, [Crate(7, 3), Crate(432,3), Crate(433,1)])
		c1 = Crane(1, (1, 1), 3, 1, 10, [], self)
		c2 = Crane(2, (2, 3), 3, 1, 10, [], self)
		c3 = Crane(3, (3, 5), 3, 2, 10, [], self)
		c1.addNeighbour(c2)
		c2.addNeighbour(c1); c2.addNeighbour(c3)
		c3.addNeighbour(c2)
		self.map[1][1] = Field(Field.CRANE_TYPE, [c1])
		self.map[2][3] = Field(Field.CRANE_TYPE, [c2])
		self.map[3][5] = Field(Field.CRANE_TYPE, [c3])
	
	
	def fieldType(self, row, col):
		return self.map[row][col].type

		
	def field(self, row, col):
		return self.map[row][col]

	def inRange(self, pos):
		(y, x) = pos
		return y >= 0 and x >= 0 and y < self.rowNum and x < self.colNum

	# Returns ((leftUpperCornerRow, leftUpperCornerCol), height, width) or None
	def commonArea(self, crane1, crane2):
		up = max(crane1.position[0] - crane1.reach, crane2.position[0] - crane2.reach)
		down = min(crane1.position[0] + crane1.reach, crane2.position[0] + crane2.reach)
		left = max(crane1.position[1] - crane1.reach, crane2.position[1] - crane2.reach)
		right = min(crane1.position[1] + crane1.reach, crane2.position[1] + crane2.reach)
		if up > down or left > right:
			return None
		return ((up, left), down - up + 1, right - left + 1)

	
	def drawMap(self):
		self.display.drawMap(self)
		
		
