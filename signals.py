from preprocess import get_angle,l2

class Signal:
	position = []
	velocity = []
	time = []
	angle=[]
	speed=[]

	def __init__(self,position,velocity,angle,speed,time):
		self.position = position
		self.velocity = velocity
		self.time = time

		if angle is not None:
			self.angle = angle
		else:
			self.angle=get_angle(self.velocity)
		
		if speed is not None:
			self.speed = speed
		else:
			self.speed = l2(self.velocity) # NOTE: No smoothing here. Paper doesn't say to do it.
	
	def __mul__(self,scalar):
		position = self.position*scalar
		velocity = self.velocity*scalar
		time = self.time
		angle = self.angle
		speed = self.speed*scalar

		return Signal(position,velocity,angle,speed,time)
	
	def __rmul__(self,scalar):
		return self*scalar
	
	def __add__(self,other):
		position = self.position+other.position
		velocity = self.velocity+other.velocity
		time = self.time

		return Signal(position,velocity,None,None,time)
	
	def __sub__(self,other):
		return self + other*(-1)
	