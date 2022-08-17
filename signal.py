class Signal:
	position = []
	velocity = []
	time = []
	angle=[]
	speed=[]

	def __init__(self,position,velocity,angle,speed,time):
		self.position = position
		self.velocity = velocity
		self.angle = angle
		self.speed = speed
		self.time = time
