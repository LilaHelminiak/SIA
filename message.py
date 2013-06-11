class Message:
	(SEARCH_PACKAGE, PACKAGE_DELIVERED, PACKAGE_LOADED, HAVE_SHIP_PATH, NEGOTIATE_FIELD, NEGOTIATE_ANSWER) = range(0, 6)
	def __init__(self, sender, type, data):
		self.sender = sender
		self.type   = type
		self.data   = data
