import numpy as np
from signals import Signal

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