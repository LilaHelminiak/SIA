from crane import *
from ship import *
from map import *

if __name__ == '__main__':

	display = Display(740, 750, 100, 25)

	map = Map(11, 7, display)
	
	crane1 = map.field(1, 1).getCrane()
	crane2 = map.field(2, 3).getCrane()
	crane3 = map.field(3, 5).getCrane()
	crane4 = map.field(5, 3).getCrane()
	Ship([crane1, crane2, crane3, crane4], [7, 772, 8, 5, 1, 2])
	
	while True:
		map.drawMap()
