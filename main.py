import sys
from objects import Map


if __name__ == '__main__':
	if len(sys.argv) == 2:
		fileName = sys.argv[1]
	else:
		fileName = "maps/map1"
	try:
		f = open(fileName, "r")
	except:
		raise Exception("Error when reading the file.")
	map = Map(f)
	f.close()

	while True:
		map.drawMap()
