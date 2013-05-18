from crane import *
from ship import *
from map import *

if __name__ == '__main__':
	display = Display(940, 750, 100, 25)
	map = Map(11, 7, display)

	while True:
		map.drawMap()
