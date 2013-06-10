class Message:
	(SEARCH_PACKAGE, PACKAGE_DELIVERED, HAVE_SHIP_PATH, NEGOTIATE_FIELD, NEGOTIATE_ANSWER) = range(0, 5)
	def __init__(self, sender, type, data):
		self.sender = sender
		self.type   = type
		self.data   = data
