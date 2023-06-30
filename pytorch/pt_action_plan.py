import torch
from torch import nn
from pytorch.pt_lognormal import LognormalDiffStroke
from sigma_lognormal.signals import Signal
from sigma_lognormal.action_plan import ActionPlan

class DiffActionPlan(nn.Module):
	def __init__(self,action_plan):
		super().__init__()
		self.strokes = nn.ModuleList([LognormalDiffStroke(stroke) for stroke in action_plan.strokes])
		self.start_point = torch.from_numpy(action_plan.start_point)
	def forward(self,time):

		# This is the non-vectorized version.
		# TODO vectorize.
		lognormal_signals=[stroke(time) for stroke in self.strokes]

		default_position = self.start_point.repeat(time.shape[0],1)
		default_velocity = torch.zeros_like(default_position)[:-1]

		full_signal=Signal(default_position,default_velocity,torch.tensor(0),torch.tensor(0),time)
		for lognormal_signal in lognormal_signals:
			full_signal += lognormal_signal
		return full_signal
	def to_action_plan(self):
		return ActionPlan([stroke.to_lognormal_stroke() for stroke in self.strokes],self.start_point.numpy())