import numpy as np
from signals import Signal
from action_plan import ActionPlan

from speed_extract import extract_all_lognormals

class BeamSearch:
	def __init__(self,signal,beam_width,snr_threshold,max_strokes):
		self.signal=signal
		self.beam_width=beam_width
		self.snr_threshold=snr_threshold
		self.max_strokes=max_strokes
	
	# Input type ActionPlan
	# Output type Signal
	def subtract_from_signal(self,action_plan):
		action_signal = action_plan.signal(self.signal.time)

		return self.signal - action_signal
	
	# Input type ActionPlan
	# Output type ActionPlan[]
	def get_children(self,action_plan):
		leftover_signal = self.subtract_from_signal(action_plan)

		# Get stroke candidates.
		all_lognormals = extract_all_lognormals(leftover_signal)

		child_plans = [
			ActionPlan([*action_plan.strokes,stroke],action_plan.start_point) for stroke in all_lognormals
		]

		return child_plans
	
	def snr(self,action_plan):
		subtracted = self.subtract_from_signal(action_plan)

		square_speed = np.square(self.signal.speed)
		square_speed_subtracted = np.square(subtracted.speed)

		ms_speed = np.mean(square_speed)
		ms_speed_subtracted = np.mean(square_speed_subtracted)

		return 10*np.log10(ms_speed/ms_speed_subtracted)
	
	# Output type ActionPlan[]
	def get_next_action_plans(self,action_plans):
		next_action_plans = []
		for action_plan in action_plans:
			next_action_plans += self.get_children(action_plan)
		sorted_plans = sorted(next_action_plans,key=lambda x: self.snr(x),reverse=True)
		return sorted_plans[:self.beam_width]

	def should_stop(self,old_plans,new_plans):
		has_good_snr = any([self.snr(action_plan)>self.snr_threshold for action_plan in new_plans])
		num_strokes = len(new_plans[0].strokes)
		too_many_strokes = num_strokes>=self.max_strokes

		best_old_snr = self.snr(old_plans[0])
		best_new_snr = self.snr(new_plans[0])
		snr_decreased = best_new_snr<=best_old_snr

		return has_good_snr or too_many_strokes or snr_decreased
	
	def search(self):
		plans = [
			ActionPlan([],self.signal.position[0])
		]

		while True:
			new_plans = self.get_next_action_plans(plans)
			print("Max. SNR:",self.snr(new_plans[0]))
			print("Num. strokes:",len(new_plans[0].strokes))
			if self.should_stop(plans,new_plans):
				return new_plans[0]
			plans = new_plans
		
		raise Exception("Should never get here.")