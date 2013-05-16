from crane import *
from map import *

if __name__ == '__main__':

	display = Display(800, 800, 100, 25)

	map = Map(7, 7, display)
	
	crane1 = map.field(2, 3).getCrane()
	crane2 = map.field(3, 5).getCrane()
	
	while True:
		map.drawMap()
		#crane1.angle = (crane1.angle + 1) % 360
		#crane2.angle = (crane2.angle - 1) % 360
