import sys
from crate import *

class Field:

	(STORAGE_TYPE, ROAD_TYPE, CRANE_TYPE) = range(0, 3)
	STACK_MAX_SIZE = 4
	
	def __init__(self, type, objectsList = []):
		self.type = type
		self.objectsList = objectsList
		
		
	def	countCrates(self):
		if self.type == Field.CRANE_TYPE:
			raise Exception("Invalid Request")
		return len(self.objectsList)
	
			
	def getAllCratesIds(self):
		if self.type == Field.CRANE_TYPE:
			raise Exception("Invalid Request")
		ids = []
		for crate in self.objectsList:
			ids.append(crate.id)
		return ids
		

	def isCratePresent(self, crateId):
		if self.type == Field.CRANE_TYPE:
			raise Exception("Invalid Request")
		for crate in self.objectsList:
			if crate.id == crateId:
				return True
		return False

		
	def getCratePosition(self, crateId):
		if self.type == Field.CRANE_TYPE:
			raise Exception("Invalid Request")
		for i in xrange(len(self.objectsList)):
			if self.objectsList[i] == crateId:
				return (len(self.objectsList) - i - 1)  # 0 = top of the stack, i.e. no crates are on the crate
		return -1
		
		
	def removeCrateFromTop(self):
		if self.type == Field.CRANE_TYPE or len(self.objectsList) < 1:
			raise Exception("Invalid Request")
		return self.objectsList.pop()
			
			
	def putCrateOnTop(self, crate):
		if self.type == Field.CRANE_TYPE or len(self.objectsList) == Field.STACK_MAX_SIZE:
			raise Exception("Invalid Request")
		self.objectsList.append(crate)
		
	def getCrane(self):
		if self.type != Field.CRANE_TYPE:
			raise Exception("Invalid Request")
		return self.objectsList[0]
