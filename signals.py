from preprocess import get_angle,hz
from util import l2
from low_pass import low_pass
import numpy as np

class Signal:
	position = np.array([])
	velocity = np.array([])
	time = np.array([])
	angle=np.array([])
	speed=np.array([])
	name=None

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
			self.speed = low_pass(l2(self.velocity),hz)
	
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
		if(isinstance(other,Signal)):
			position = self.position+other.position
			velocity = self.velocity+other.velocity
			time = self.time

			return Signal(position,velocity,None,None,time)
		elif(isinstance(other,int) or isinstance(other,float) or isinstance(other,np.ndarray) and other.shape==()):
			# Add constant position offset to signal.
			position = self.position+other
			return Signal(position,self.velocity,self.angle,self.speed,self.time)
		else:
			raise TypeError("Cannot add Signal and "+str(type(other)))
	
	def __sub__(self,other):
		return self + other*(-1)

	def __getitem__(self,val):
		assert isinstance(val,slice)
		position = self.position[val]
		time = self.time[val]

		val_short = slice(val.start,val.stop-1,val.step)
		velocity = self.velocity[val_short]
		angle = self.angle[val_short]
		speed = self.speed[val_short]

		return Signal(position,velocity,angle,speed,time)
	