import numpy as np
from sigma_lognormal.signals import Signal
from sigma_lognormal.lognormal import LognormalStroke

"""
An action plan is a sequence of handstrokes.
It can be evaluated by using .signal(timesteps).
"""
class ActionPlan:
	def __init__(self,strokes,start_point):
		self.strokes=strokes
		self.start_point=start_point
	def signal(self,time):
		lognormal_signals=[stroke.signal(time) for stroke in self.strokes]

		start_position = self.start_point[np.newaxis,:].repeat(len(time),axis=0)
		full_signal=Signal(start_position,np.zeros((len(time)-1,2)),None,None,time)

		for lognormal_signal in lognormal_signals:
			full_signal += lognormal_signal
		return full_signal
	def sub_plan(self,num_strokes):
		return ActionPlan(self.strokes[:num_strokes],self.start_point)
	def to_json(self):
		return {
			"strokes":[stroke.to_json() for stroke in self.strokes],
			"start_point":self.start_point.tolist()
		}
	@staticmethod
	def from_json(json):
		return ActionPlan(
			[LognormalStroke.from_json(stroke_json) for stroke_json in json["strokes"]],
			np.array(json["start_point"])
		)