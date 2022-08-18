import numpy as np
from signals import Signal
from action_plan import ActionPlan

from speed_extract import extract_all_lognormals

from timer import timer

class BeamSearch:
	def __init__(self,signal,beam_width,snr_threshold,max_strokes):
		self.signal=signal
		self.beam_width=beam_width
		self.snr_threshold=snr_threshold
		self.max_strokes=max_strokes
		self.subtract_cache = {}
		self.snr_cache={}
	
	
	# Input type ActionPlan
	# Output type Signal
	def subtract_from_signal(self,action_plan):

		# If possible, evaluate only the *final* stroke. Use a cached version of the n-1 strokes.
		if len(action_plan.strokes)>1:
			curr_stroke = action_plan.strokes[-1]
			if curr_stroke in self.subtract_cache:
				return self.subtract_cache[curr_stroke]
			prev_stroke = action_plan.strokes[-2]
			if prev_stroke in self.subtract_cache:

				cached_value = self.subtract_cache[prev_stroke]
				stroke_signal = curr_stroke.signal(self.signal.time)
				ret= cached_value - stroke_signal

				self.subtract_cache[curr_stroke] = ret
				return ret

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

		if action_plan in self.snr_cache:
			return self.snr_cache[action_plan]
		
		subtracted = self.subtract_from_signal(action_plan)

		square_speed = np.square(self.signal.speed)
		square_speed_subtracted = np.square(subtracted.speed)

		ms_speed = np.mean(square_speed)
		ms_speed_subtracted = np.mean(square_speed_subtracted)

		ret = 10*np.log10(ms_speed/ms_speed_subtracted)
		self.snr_cache[action_plan] = ret

		return ret
	
	# Output type ActionPlan[]
	def get_next_action_plans(self,action_plans):
		next_action_plans = []

		plan_making_timer = timer()

		for action_plan in action_plans:
			next_action_plans += self.get_children(action_plan)
		plan_making_timer("Plan making",len(next_action_plans),"plans")
		sorted_plans = sorted(next_action_plans,key=lambda x: self.snr(x),reverse=True)
		plan_making_timer("Sorting")
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

		perf_timer = timer()
		num_strokes = 0

		while True:
			perf_timer("Start iter")
			new_plans = self.get_next_action_plans(plans)
			num_strokes+=1
			perf_timer("Got children plans")
			print("Max. SNR:",self.snr(new_plans[0]))
			print("Num. strokes:",num_strokes)
			if self.should_stop(plans,new_plans):
				return new_plans[0]
			perf_timer("Stop check")
			plans = new_plans

			# Clear all old SNR cache entries.
			keys = list(self.snr_cache.keys())
			for cached_snr in keys:
				if len(cached_snr.strokes) < num_strokes - 1:
					del self.snr_cache[cached_snr] 
			

			# Clear old subtract cache entries.
			for cached_subtract in self.subtract_cache:
				cached_strokes = len(cached_subtract.strokes)
				if cached_strokes < num_strokes - 1:
					del self.subtract_cache[cached_subtract]