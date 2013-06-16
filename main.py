import sys
from crane import *
from ship import *
from map import *


if __name__ == '__main__':
	if len(sys.argv) == 2:
		map = Map(sys.argv[1])
	else:
		map = Map("maps/map1")

	while True:
		map.drawMap()
