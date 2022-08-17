from signal import Signal
import numpy as np
from scipy import special

class LognormalStroke:
	def __init__(self,D,t_0,mu,sigma,theta_s,theta_f):
		self.D = D
		self.t_0=t_0
		self.mu=mu
		self.sigma=sigma
		self.theta_s=theta_s
		self.theta_f=theta_f
	def speed(self,time):
		delta=time-self.t_0
		multiplier=self.D / (self.sigma*np.sqrt(2*np.pi)*delta)
		erf_input=self.time_param(time)
		exp_input=-(erf_input**2)
		return multiplier * np.exp(exp_input)

	def time_param(self,time):
		delta=time-self.t_0
		ret=(np.log(delta)-self.mu)/(np.sqrt(2)*self.sigma)
		nans_fixed=np.nan_to_num(ret,num=np.NINF)
		return nans_fixed
	def fraction_done(self,time):
		time_param=self.time_param(time)
		erf = special.erf(time_param)
		return (1+erf)/2
	def length(self,time):
		fraction_done=self.fraction_done(time)
		return self.D*fraction_done # D represents total stroke length.
	def angle(self,time):
		fraction_done=self.fraction_done(time)
		return self.theta_s + (self.theta_f-self.theta_s)*fraction_done
	def velocity(self,time):
		speed=self.speed(time)
		angle=self.angle(time)
		
		x=speed*np.cos(angle)
		y=speed*np.sin(angle)

		return np.concatenate((x.reshape((x.shape[0],1)),y.reshape((y.shape[0],1))),axis=1)

	def position(self,time):
		multiplier = self.D / (self.theta_f - self.theta_s)
		angle=self.angle(time)

		x=np.sin(angle) - np.sin(self.theta_s)
		y=-np.cos(angle)+np.cos(self.theta_s)

		combined=np.concatenate((x.reshape((x.shape[0],1)),y.reshape((y.shape[0],1))),axis=1)

		return multiplier*combined

	def signal(self,time):
		position=self.position(time)
		velocity=self.velocity(time)
		angle=self.angle(time)
		speed=self.speed(time)

		return Signal(position,velocity,angle,speed,time)

