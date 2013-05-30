import sys
from math import radians, sin, cos, sqrt, floor
import pygame
from pygame.locals import *
from field import *


class Display:

	BLACK = (0, 0, 0)
	WHITE = (255, 255, 255)
	RED = (255, 0, 0)
	GREEN = (0, 255, 0)
	BLUE = (0, 0, 255)
	BROWN = (205, 127, 50)

	
	def __init__(self, width, height, fieldSize, fontSize):
		self.width = width  # in pixels
		self.height = height  # in pixels
		self.fieldSize = fieldSize  # in pixels
		self.normalizeSize()
		self.colsPerScreen = int(self.width / self.fieldSize)
		self.rowsPerScreen = int(self.height / self.fieldSize)
		self.upperLeftFieldCoors = (0, 0)
		self.showingInfoForObject = None  # reference to an object (Field / Crane / Ship)		

		pygame.init()
		self.clock = pygame.time.Clock()
		
		self.windowSurface = pygame.display.set_mode((self.width, self.height), 0, 32)
		pygame.display.set_caption("Agents in the Harbour")
		
		self.fontSize = fontSize
		self.basicFont = pygame.font.SysFont(None, self.fontSize)
		
		self.windowSurface.fill(Display.WHITE)
	
	
	def normalizeSize(self):
		self.width = int(floor(self.width / self.fieldSize)) * self.fieldSize
		self.height = int(floor(self.height / self.fieldSize)) * self.fieldSize
	
	
	def crateIdToString(self, x):
		if x < 10:
			return "00" + str(x)
		if x < 100:
			return "0" + str(x)
		else:
			return str(x)


	def drawCraneBody(self, crane, rect):
		craneRect = pygame.draw.circle(self.windowSurface, (100, 100, 100), (rect.centerx, rect.centery), self.fieldSize / 2, 0)
					
		craneIdText = self.basicFont.render(str(crane.id), True, Display.WHITE, (100, 100, 100))
		craneIdTextRect = craneIdText.get_rect()
		craneIdTextRect.centerx = craneRect.centerx - self.fieldSize / 4
		craneIdTextRect.centery = craneRect.centery - self.fieldSize / 4
		self.windowSurface.blit(craneIdText, craneIdTextRect)
					
		if crane.crate == None:
			heldCrateId = "---"
		else:
			heldCrateId = self.crateIdToString(crane.crate.id)
		craneHeldCrateId = self.basicFont.render(heldCrateId, True, Display.WHITE, (100, 100, 100))
		craneHeldCrateIdRect = craneHeldCrateId.get_rect()
		craneHeldCrateIdRect.centerx = craneRect.centerx
		craneHeldCrateIdRect.centery = craneRect.centery + self.fieldSize / 4
		self.windowSurface.blit(craneHeldCrateId, craneHeldCrateIdRect)
		return craneRect


	def drawCranesArms(self, cranesList):
		for i in xrange(len(cranesList)):
			(crane, craneRect) = (cranesList[i][0], cranesList[i][1])
			armLen = sqrt(2) * crane.reach * self.fieldSize
			pygame.draw.line(self.windowSurface, Display.BLACK, (craneRect.centerx, craneRect.centery), (craneRect.centerx + cos(crane.angle) * armLen, craneRect.centery + sin(crane.angle) * armLen), 3)

			hookDist = crane.hookDistance * self.fieldSize
			pygame.draw.circle(self.windowSurface, Display.BLACK, (int(craneRect.centerx + cos(crane.angle) * hookDist), int(craneRect.centery + sin(crane.angle) * hookDist)), int(max(5, (crane.hookHeight / crane.height) * 10)), 0)


	def drawCratesOnField(self, ids, rect):
		for i in xrange(len(ids)):
			pygame.draw.rect(self.windowSurface, Display.BLACK, (rect.centerx - ((self.fontSize / 2) * 3 + 8) / 2, rect.bottom - (self.fontSize + 1) - (self.fieldSize / 4) * i, (self.fontSize / 2) * 3 + 10, self.fontSize + 2), 1)
			crateId = self.basicFont.render(self.crateIdToString(ids[i]), True, Display.BLACK, Display.WHITE)
			crateIdRect = crateId.get_rect()
			crateIdRect.centerx = rect.centerx
			crateIdRect.centery = rect.bottom - (self.fieldSize / 4) * i - self.fontSize / 2
			self.windowSurface.blit(crateId, crateIdRect)


	def drawStuff(self, map):
		(upperLeftRow, upperLeftCol) = self.upperLeftFieldCoors
		cranesList = []
		rowDisplay = 0
		for row in xrange(upperLeftRow, min(map.rowNum, upperLeftRow + self.rowsPerScreen)):
			colDisplay = 0
			for col in xrange(upperLeftCol, min(map.colNum, upperLeftCol + self.colsPerScreen)):

				if map.fieldType(row, col) == Field.SHIP_TYPE:
					pygame.draw.rect(self.windowSurface, Display.BROWN, (colDisplay * self.fieldSize, rowDisplay * self.fieldSize, self.fieldSize, self.fieldSize)) # draw the ship's front column

				rect = pygame.draw.rect(self.windowSurface, Display.BLACK, (colDisplay * self.fieldSize, rowDisplay * self.fieldSize, self.fieldSize, self.fieldSize), 1)
				colDisplay += 1

				if map.fieldType(row, col) == Field.CRANE_TYPE:
					crane = map.field(row, col).getCrane()
					craneRect = self.drawCraneBody(crane, rect)
					cranesList.append((crane, craneRect))
					continue
				
				if map.field(row, col).countCrates() == 0:
					continue
				self.drawCratesOnField(map.field(row, col).getAllCratesIds(), rect)

			if upperLeftCol + self.colsPerScreen >= map.colNum + 1 and map.fieldType(row, map.colNum - 1) == Field.SHIP_TYPE: # draw the ship's back column
				pygame.draw.rect(self.windowSurface, Display.BROWN, (colDisplay * self.fieldSize, rowDisplay * self.fieldSize, self.fieldSize, self.fieldSize))

			rowDisplay += 1

		self.drawCranesArms(cranesList)
		self.drawInformationWindow(map)


	def drawInformationWindow(self, map):
		if self.showingInfoForObject == None:
			return
		infoRect = pygame.draw.rect(self.windowSurface, Display.WHITE, (self.width / 4, self.height / 4, self.width / 2, self.height / 2))
		info = "FIELD"
		if self.showingInfoForObject == map.ship:
			info = "SHIP"
		elif self.showingInfoForObject.type == Field.CRANE_TYPE:
			info = "CRANE"
		text = self.basicFont.render(info, True, Display.BLACK, Display.WHITE)
		textRect = text.get_rect()
		textRect.centerx = infoRect.centerx
		textRect.centery = infoRect.centery
		self.windowSurface.blit(text, textRect)


	def moveDisplay(self, map, position):
		if position[0] >= 0 and position[0] < map.rowNum:
			if position[1] >= 0 and position[1] < map.colNum + 1:
				self.upperLeftFieldCoors = position


	def startShowingInformationWindow(self, map, position):
		(row, col) = position
		if col == map.colNum and row < map.rowNum:
			self.showingInfoForObject = map.ship
		elif map.inMapBounds(position):
			self.showingInfoForObject = map.field(row, col)


	def drawMap(self, map):
		self.clock.tick(30)
		
		for event in pygame.event.get():
			if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
				map.stopThreads()
				pygame.quit()
				sys.exit()
			if event.type == KEYDOWN:
				if event.key == K_SPACE:
					map.pause ^= True
					print "Pause = " + str(map.pause)
				if event.key == K_UP:
					self.moveDisplay(map, (self.upperLeftFieldCoors[0] - 1, self.upperLeftFieldCoors[1]))
				if event.key == K_DOWN:
					self.moveDisplay(map, (self.upperLeftFieldCoors[0] + 1, self.upperLeftFieldCoors[1]))
				if event.key == K_LEFT:
					self.moveDisplay(map, (self.upperLeftFieldCoors[0], self.upperLeftFieldCoors[1] - 1))
				if event.key == K_RIGHT:
					self.moveDisplay(map, (self.upperLeftFieldCoors[0], self.upperLeftFieldCoors[1] + 1))
			if event.type == MOUSEBUTTONDOWN:
				clickRow = self.upperLeftFieldCoors[0] + int(floor(event.pos[1] / self.fieldSize))
				clickCol = self.upperLeftFieldCoors[1] + int(floor(event.pos[0] / self.fieldSize))
				if event.button == 1:
					if self.showingInfoForObject == None:
						self.startShowingInformationWindow(map, (clickRow, clickCol))
					else:
						self.showingInfoForObject = None
					
		self.windowSurface.fill(Display.WHITE)
			
		self.drawStuff(map)
				
		pygame.display.update()
		
