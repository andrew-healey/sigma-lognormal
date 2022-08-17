import numpy as np
from signals import Signal

class ActionPlan:
	def __init__(self,strokes,start_point):
		self.strokes=strokes
		self.start_point=start_point
	def signal(self,time):
		lognormal_signals=[stroke.signal(time) for stroke in self.strokes]

		combined_signal = sum(lognormal_signals)
		combined_signal.position += self.start_point[np.newaxis,:].repeat(len(time),axis=0)

		return combined_signal