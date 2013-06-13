class Message:
	(SEARCH_PACKAGE, PACKAGE_DELIVERED, PACKAGE_LOADED, HAVE_SHIP_PATH, NEGOTIATE_FIELD, NEGOTIATE_ANSWER, NEGOTIATE_OWNERSHIP) = range(0, 7)
	def __init__(self, sender, type, data):
		self.sender = sender
		self.type   = type
		self.data   = data
