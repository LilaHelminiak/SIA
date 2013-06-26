import sys
from math import radians, sin, cos, sqrt, floor, pi
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
	CRANE_BODY_COLOUR = (100, 100, 100)
	FORKLIFT_BODY_COLOUR = (70, 170, 170)
	ROAD_COLOUR = (210, 210, 210)

	
	def __init__(self, width, height, fieldSize, fontSize):
		self.width = width  # in pixels
		self.height = height  # in pixels
		self.fieldSize = fieldSize  # in pixels
		self.normalizeSize()
		self.colsPerScreen = int(self.width / self.fieldSize)
		self.rowsPerScreen = int(self.height / self.fieldSize)
		self.upperLeftFieldCoors = (0, 0)
		self.showingInfoForObject = None  # reference to an object (Field / Crane / Ship)
		self.displayHUD = True		

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
		craneRect = pygame.draw.circle(self.windowSurface, Display.CRANE_BODY_COLOUR, (rect.centerx, rect.centery), self.fieldSize / 2, 0)
					
		craneIdText = self.basicFont.render(str(crane.id), True, Display.WHITE)
		craneIdTextRect = craneIdText.get_rect()
		craneIdTextRect.centerx = craneRect.centerx - self.fieldSize / 4
		craneIdTextRect.centery = craneRect.centery - self.fieldSize / 4
		self.windowSurface.blit(craneIdText, craneIdTextRect)
					
		if crane.crate == None:
			heldCrateId = "---"
		else:
			heldCrateId = self.crateIdToString(crane.crate.id)
		craneHeldCrateId = self.basicFont.render(heldCrateId, True, Display.WHITE)
		craneHeldCrateIdRect = craneHeldCrateId.get_rect()
		craneHeldCrateIdRect.centerx = craneRect.centerx
		craneHeldCrateIdRect.centery = craneRect.centery + self.fieldSize / 4
		self.windowSurface.blit(craneHeldCrateId, craneHeldCrateIdRect)
		return craneRect


	def drawCranesArms(self, map):
		for crane in map.cranesList:
			(row, col) = crane.position
			(up, down) = (self.upperLeftFieldCoors[0], self.upperLeftFieldCoors[0] + self.rowsPerScreen - 1)
			(left, right) = (self.upperLeftFieldCoors[1], self.upperLeftFieldCoors[1] + self.colsPerScreen - 1)
			(row, col) = (row - up, col - left)
			armLen = sqrt(2) * crane.reach * self.fieldSize
			y1 = int(row * self.fieldSize + self.fieldSize / 2)
			x1 = int(col * self.fieldSize + self.fieldSize / 2)
			y2 = int(y1 + sin(crane.angle) * armLen)
			x2 = int(x1 + cos(crane.angle) * armLen)

			if (y1 < 0 and y2 < 0) or (x1 < 0 and x2 < 0) or (y1 > self.height  and y2 > self.height) or (x1 > self.width and x2 > self.width):
				continue

			pygame.draw.line(self.windowSurface, Display.BLACK, (x1, y1), (x2, y2), 3)
			hookDist = crane.hookDistance * self.fieldSize
			pygame.draw.circle(self.windowSurface, Display.BLACK, (int(x1 + cos(crane.angle) * hookDist), int(y1 + sin(crane.angle) * hookDist)), int(max(5, (crane.hookHeight / crane.height) * 10)), 0)


	def drawForklifts(self, map):
		for forklift in map.forkliftsList:
			(row, col) = forklift.position
			(up, down) = (self.upperLeftFieldCoors[0], self.upperLeftFieldCoors[0] + self.rowsPerScreen - 1)
			(left, right) = (self.upperLeftFieldCoors[1], self.upperLeftFieldCoors[1] + self.colsPerScreen - 1)
			if row >= up - 1 and row <= down + 1 and col >= left - 1 and col <= right + 1:
				(row, col) = (row - up, col - left)
				y = int(int(row) * self.fieldSize + self.fieldSize / 2 + (row - int(row)) * self.fieldSize)
				x = int(int(col) * self.fieldSize + self.fieldSize / 2 + (col - int(col)) * self.fieldSize)
				armLen = 3 * self.fieldSize / 8
				pygame.draw.line(self.windowSurface, Display.BLACK, (x, y), (x + cos(forklift.angle) * armLen, y + sin(forklift.angle) * armLen), 4)
				forkliftRect = pygame.draw.circle(self.windowSurface, Display.FORKLIFT_BODY_COLOUR, (x, y), self.fieldSize / 4, 0)

				forkliftIdText = self.basicFont.render(str(forklift.id), True, Display.WHITE)
				forkliftIdTextRect = forkliftIdText.get_rect()
				forkliftIdTextRect.centerx = x
				forkliftIdTextRect.centery = y - self.fieldSize / 8
				self.windowSurface.blit(forkliftIdText, forkliftIdTextRect)

				if forklift.crate == None:
					heldCrateId = "---"
				else:
					heldCrateId = self.crateIdToString(forklift.crate.id)
				forkliftHeldCrateId = self.basicFont.render(heldCrateId, True, Display.WHITE)
				forkliftHeldCrateIdRect = forkliftHeldCrateId.get_rect()
				forkliftHeldCrateIdRect.centerx = x
				forkliftHeldCrateIdRect.centery = y + self.fieldSize / 8
				self.windowSurface.blit(forkliftHeldCrateId, forkliftHeldCrateIdRect)


	def drawCratesOnField(self, ids, rect):
		for i in xrange(len(ids)):
			pygame.draw.rect(self.windowSurface, Display.WHITE, (rect.centerx - ((self.fontSize / 2) * 3 + 8) / 2, rect.bottom - (self.fontSize + 1) - (self.fieldSize / 4) * i, (self.fontSize / 2) * 3 + 10, self.fontSize + 2))
			pygame.draw.rect(self.windowSurface, Display.BLACK, (rect.centerx - ((self.fontSize / 2) * 3 + 8) / 2, rect.bottom - (self.fontSize + 1) - (self.fieldSize / 4) * i, (self.fontSize / 2) * 3 + 10, self.fontSize + 2), 1)
			crateId = self.basicFont.render(self.crateIdToString(ids[i]), True, Display.BLACK, Display.WHITE)
			crateIdRect = crateId.get_rect()
			crateIdRect.centerx = rect.centerx
			crateIdRect.centery = rect.bottom - (self.fieldSize / 4) * i - self.fontSize / 2
			self.windowSurface.blit(crateId, crateIdRect)


	def drawHUD(self, map):
		if self.displayHUD == False:
			return
		hudFontSize = self.fontSize + int(self.fontSize / 2)
		hudFont = pygame.font.SysFont(None, hudFontSize)
		neededCratesText = hudFont.render("The ship needs:", True, Display.BLACK)
		neededCratesTextRect = neededCratesText.get_rect()
		neededCratesTextRect.left = self.width - 200
		neededCratesTextRect.top = 20
		self.windowSurface.blit(neededCratesText, neededCratesTextRect)

		crateList = map.ship.neededCrates
		for i in xrange(len(crateList)):
			if i >= len(crateList):
				break
			crateText = hudFont.render(str(self.crateIdToString(crateList[i])), True, Display.BLACK)
			crateTextRect = crateText.get_rect()
			crateTextRect.left = self.width - 50
			crateTextRect.top = 20 + (hudFontSize + 2) * (i + 1)
			self.windowSurface.blit(crateText, crateTextRect)


	def drawInformationWindow(self, map):
		if self.showingInfoForObject == None:
			return
		infoRect = pygame.draw.rect(self.windowSurface, Display.WHITE, (self.width / 8, self.height / 8, 6 * self.width / 8, 6 * self.height / 8))
		info = "FIELD"
		if self.showingInfoForObject == map.ship:
			info = "SHIP"
			labels = ["CRATE ID", "REQUESTED", "DELIVERED", "WAITED", "CRANE ID"]
			for i in xrange(5):
				text = self.basicFont.render(labels[i], True, Display.BLACK, Display.WHITE)
				textRect = text.get_rect()
				textRect.left = infoRect.left + 10 + i * 140
				textRect.top = infoRect.top + 30
				self.windowSurface.blit(text, textRect)

			for i in xrange(len(map.ship.infoData)):
				values = [self.crateIdToString(map.ship.infoData[i][0]), "-", "-", "-", "-"]
				for j in xrange(1, 4):
					if map.ship.infoData[i][j] != None:
						values[j] = "%.2f" % map.ship.infoData[i][j]
				if map.ship.infoData[i][4] != None:
						values[4] = str(map.ship.infoData[i][4])
				for j in xrange(5):
					text = self.basicFont.render(values[j], True, Display.BLACK, Display.WHITE)
					textRect = text.get_rect()
					textRect.left = infoRect.left + 10 + j * 140
					textRect.top = infoRect.top + 30 + (i + 1) * 30
					self.windowSurface.blit(text, textRect)
		elif self.showingInfoForObject.type == Field.CRANE_TYPE:
			info = "CRANE"
			labels = ["ID", "HELD CRATE", "AVERAGE TIME", "# OF CRATES PASSED", "ARM MOVEMENT TOTAL", "HORIZONTAL HOOK MOV. TOTAL", "VERTICAL HOOK MOV. TOTAL"]
			for i in xrange(len(labels)):
				text = self.basicFont.render(labels[i], True, Display.BLACK, Display.WHITE)
				textRect = text.get_rect()
				textRect.left = infoRect.left + 10
				textRect.top = infoRect.top + 30 + i * 50
				self.windowSurface.blit(text, textRect)
			crane = self.showingInfoForObject.getCrane()
			values = [str(crane.id), "-", "-", str(crane.passedPackages), str(crane.armMoveTotal * 180 / pi), str(crane.hookMoveHorTotal), str(crane.hookMoveVerTotal)]
			if crane.crate != None:
				values[1] = self.crateIdToString(crane.crate.id)
			if crane.averageTime != 0:
				values[2] = "%.2f" % crane.averageTime
			for j in xrange(len(values)):
				text = self.basicFont.render(values[j], True, Display.BLACK, Display.WHITE)
				textRect = text.get_rect()
				textRect.left = infoRect.left + 10 + 300
				textRect.top = infoRect.top + 30 + j * 50
				self.windowSurface.blit(text, textRect)
		text = self.basicFont.render(info, True, Display.BLACK, Display.WHITE)
		textRect = text.get_rect()
		textRect.centerx = infoRect.centerx
		textRect.centery = infoRect.top + 10
		self.windowSurface.blit(text, textRect)


	def drawStuff(self, map):
		(upperLeftRow, upperLeftCol) = self.upperLeftFieldCoors
		rowDisplay = 0
		for row in xrange(upperLeftRow, min(map.rowNum, upperLeftRow + self.rowsPerScreen)):
			colDisplay = 0
			for col in xrange(upperLeftCol, min(map.colNum, upperLeftCol + self.colsPerScreen)):

				if map.fieldType(row, col) == Field.ROAD_TYPE:
					pygame.draw.rect(self.windowSurface, Display.ROAD_COLOUR, (colDisplay * self.fieldSize, rowDisplay * self.fieldSize, self.fieldSize, self.fieldSize)) # Road field has a different colour

				if map.fieldType(row, col) == Field.SHIP_TYPE:
					pygame.draw.rect(self.windowSurface, Display.BROWN, (colDisplay * self.fieldSize, rowDisplay * self.fieldSize, self.fieldSize, self.fieldSize)) # draw the ship's front column

				rect = pygame.draw.rect(self.windowSurface, Display.BLACK, (colDisplay * self.fieldSize, rowDisplay * self.fieldSize, self.fieldSize, self.fieldSize), 1)
				colDisplay += 1

				if map.fieldType(row, col) == Field.CRANE_TYPE:
					self.drawCraneBody(map[(row, col)].getCrane(), rect)
					continue
				
				if map.field(row, col).isForkliftPresent() or map.field(row, col).countCrates() == 0:
					continue
				self.drawCratesOnField(map.field(row, col).getAllCratesIds(), rect)

			if upperLeftCol + self.colsPerScreen >= map.colNum + 1 and map.fieldType(row, map.colNum - 1) == Field.SHIP_TYPE: # draw the ship's back column
				pygame.draw.rect(self.windowSurface, Display.BROWN, (colDisplay * self.fieldSize, rowDisplay * self.fieldSize, self.fieldSize, self.fieldSize))

			rowDisplay += 1

		self.drawForklifts(map)
		self.drawCranesArms(map)
		self.drawHUD(map)
		self.drawInformationWindow(map)


	def moveDisplay(self, map, position):
		if position[0] >= 0 and position[0] < map.rowNum:
			if position[1] >= 0 and position[1] < map.colNum + 1:
				self.upperLeftFieldCoors = position


	def startShowingInformationWindow(self, map, position):
		(row, col) = position
		if col in (map.colNum - 1, map.colNum) and row < map.rowNum:
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
				if event.key == K_h:
					self.displayHUD ^= True
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
		
