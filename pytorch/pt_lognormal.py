from sigma_lognormal.signals import Signal
import torch
from torch import nn
import math
from sigma_lognormal.lognormal import LognormalStroke

class LognormalDiffStroke(nn.Module):
	def __init__(self,stroke):
		super().__init__()
		self.D = nn.Parameter(torch.tensor(stroke.D))
		self.t_0 = nn.Parameter(torch.tensor(stroke.t_0))
		self.mu = nn.Parameter(torch.tensor(stroke.mu))
		self.sigma = nn.Parameter(torch.tensor(stroke.sigma))
		self.theta_s = nn.Parameter(torch.tensor(stroke.theta_s))
		self.theta_f = nn.Parameter(torch.tensor(stroke.theta_f))

	def speed(self,time):
		delta=time-self.t_0
		multiplier=self.D / (self.sigma*torch.sqrt(torch.tensor(2*math.pi))*delta)
		erf_input=self.time_param(time)
		exp_input= -(erf_input**2)
		return multiplier * torch.exp(exp_input)
	
	def time_param(self,time):
		delta=time-self.t_0
		fixed_delta = torch.maximum(torch.tensor(0.01),delta)
		ret=(torch.log(fixed_delta)-self.mu)/(torch.sqrt(torch.tensor(2))*self.sigma)
		return ret
	def fraction_done(self,time):
		time_param=self.time_param(time)
		erf = torch.erf(time_param)
		return (1+erf)/2
	def length(self,time):
		fraction_done=self.fraction_done(time)
		return self.D*fraction_done
	def angle(self,time):
		fraction_done=self.fraction_done(time)
		return self.theta_s + (self.theta_f-self.theta_s)*fraction_done
	def velocity(self,time):
		speed=self.speed(time)
		angle=self.angle(time)
		
		x=speed*torch.cos(angle)
		y=speed*torch.sin(angle)

		return torch.cat((x[...,None],y[...,None]),dim=-1)
	def position(self,time):
		multiplier = self.D / (self.theta_f - self.theta_s)
		angle=self.angle(time)

		x=torch.sin(angle) - torch.sin(self.theta_s)
		y=-torch.cos(angle)+torch.cos(self.theta_s)

		combined=torch.cat((x[...,None],y[...,None]),dim=-1)

		return multiplier*combined
	
	# This sets angle and speed to zero.
	# It means Signal.__add__ doesn't try to recompute them (read: using NP operations).
	def forward(self,time):
		return Signal(self.position(time),self.velocity(time[:-1]),torch.tensor(0),torch.tensor(0),time)
	def to_lognormal_stroke(self):
		return LognormalStroke(self.D.item(),self.t_0.item(),self.mu.item(),self.sigma.item(),self.theta_s.item(),self.theta_f.item())