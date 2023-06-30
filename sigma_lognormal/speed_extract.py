import numpy as np
np.seterr(all="ignore")

from sigma_lognormal.util import l2

# Should p_3 have speed of speed(t_3), or match the max. speed of the stroke?
use_real_max = False
real_max_range = 5 # frames. Equal to 30 ms, aka less than any valid p2/p4 delta t.

class Point:
	def __init__(self,idx,signal,role):
		self.role=role
		
		self.velocity=signal.velocity[idx]
		self.position=signal.position[idx]
		self.time=signal.time[idx]
		self.angle=signal.angle[idx]

		if role == 3 and use_real_max:
			rough_speed = l2(signal.velocity)
			speed_window = rough_speed[idx-real_max_range:idx+real_max_range]
			self.speed = np.max(speed_window)
		else:
			self.speed=signal.speed[idx]

		self.idx=idx
	def __str__(self) -> str:
		# Display role, index, time, speed, angle.
		return "Point(role={},idx={},time={},speed={},angle={})".format(self.role,self.idx,self.time,self.speed,self.angle)

def sign(num):
	return 1 if num>0 else (0 if num==0 else -1)
import re

from sigma_lognormal.util import diff

def mark_stroke_candidates(signal):

	speed_seq=signal.speed

	ddspeed_seq=diff(diff(speed_seq,signal.time[1:]),signal.time[2:])

	points=[[0,"low"]]

	for _idx,speed in enumerate(speed_seq[1:-1]):
		idx=_idx+1
		prev_speed=speed_seq[idx-1]
		next_speed=speed_seq[idx+1]
		
		is_local_max= speed>=prev_speed and speed>=next_speed
		if(is_local_max):
			points.append([idx,"high"])
		
		is_local_min = speed<=prev_speed and speed<=next_speed
		if(is_local_min):
			points.append([idx,"low"])
		
		ddspeed=ddspeed_seq[_idx]
		next_ddspeed=0 if _idx==len(ddspeed_seq)-1 else ddspeed_seq[_idx+1]
		
		changes_sign=sign(ddspeed) != sign(next_ddspeed)
			
		if(changes_sign):
			points.append([idx,"flip"])

	points.append([len(speed_seq)-1,"low"])

	lookup_str="".join([point[1][0] for point in points])

	# Indexes in the high-flip-low string.
	stroke_idxes=[m.start() for m in re.finditer('lf+hf+(?=l)', lookup_str)]

	def get_points(stroke_idx,points):

		one=points[stroke_idx]
		three_idx=stroke_idx+lookup_str[stroke_idx:].find("h")
		twos=points[stroke_idx+1:three_idx]
		three=points[three_idx]
		five_idx=three_idx+lookup_str[three_idx:].find("l")
		fours=points[three_idx+1:five_idx]
		five=points[five_idx]
		

		# type StrokePoints = [Point, Point[], Point, Point[], Point]
		points=[
			Point(one[0],signal,1),
			[Point(two[0],signal,2) for two in twos],
			Point(three[0],signal,3),
			[Point(four[0],signal,4) for four in fours],
			Point(five[0],signal,5)
		]
		return points
		
	# Return type StrokePoints[]
	return [get_points(stroke_idx,points) for stroke_idx in stroke_idxes]

# Input type StrokePoints
# Output type Point[2][]
def get_point_combos(stroke_candidate):
	ret = []

	# Possible combos: p2, p3; p2, p4; p3, p4

	p2s=stroke_candidate[1]
	p3=stroke_candidate[2]
	p4s=stroke_candidate[3]

	for p2 in p2s:
		ret.append([p2,p3])

		for p4 in p4s:
			ret.append([p2,p4])

	for p4 in p4s:
		ret.append([p3,p4])

	return ret

from sigma_lognormal.lognormal import LognormalStroke

def extract_sigma_lognormal(point_combo,points):
	pa,pb = point_combo
	p1,p2,p3,p4,p5 = points

	if pa.speed <= 0 or pb.speed <= 0:
		return None

	ratio = pa.speed/pb.speed
	l_ratio = np.log(ratio)

	if pa.role==2 and pb.role==3:
		sigma_sq=-2 - 2*l_ratio - 1/(2*l_ratio)
	elif pa.role==2 and pb.role==4:
		sigma_sq=-2 + 2*np.sqrt( l_ratio**2 + 1 )
	elif pa.role==3 and pb.role==4:
		sigma_sq=-2 + 2*l_ratio + 1/(2*l_ratio)
	else:
		raise ValueError("Invalid Numbers "+str(pa.role)+", "+str(pb.role))
	
	sigma=np.sqrt(sigma_sq)

	# Calculate mu.

	def calc_a(pt):
		if pt.role==3:
			exponent= -sigma_sq
		elif pt.role==2:
			exponent=sigma/2 * (-np.sqrt(sigma_sq+4) - 3*sigma)
		elif pt.role==4:
			exponent=sigma/2 * (np.sqrt(sigma_sq+4) - 3*sigma)
		else:
			raise ValueError("Invalid Number "+str(pt.role))
		return np.exp(exponent)
	
	time_diff = pa.time - pb.time
	a_diff = calc_a(pa) - calc_a(pb)

	exp_mu = time_diff / a_diff
	mu = np.log(exp_mu)

	# Now, calculate t_0.
	def est_t_0(pt):
		return pt.time - exp_mu * calc_a(pt)
	
	how_to_combine = "prefer_p3"

	# Given a computation and two points, decide how to combine the computation between them.
	def decide(func,a=pa,b=pb):
		if how_to_combine=="prefer_p3":
			if a.role==3:
				return func(a)
			elif b.role==3:
				return func(b)

		if how_to_combine=="first":
			return func(a)
		# Default is to average.
		return (func(a)+func(b))/2
	
	t_0 = decide(est_t_0)

	def delta(pt):
		return pt.time - t_0
	
	def est_D(pt):
		exponent = (( np.log(delta(pt)) - mu )**2) / (2*sigma_sq)
		return pt.speed * sigma*np.sqrt(2*np.pi)*delta(pt) * np.exp( exponent )
	
	D=decide(est_D)

	# Now, extract angle parameters.

	speed_lognormal = LognormalStroke(D,t_0,mu,sigma,None,None) # No angle information *yet*.

	should_hardcode = True

	def fraction_done(pt):
		if should_hardcode:
			if pt.role==1:
				return 0
			elif pt.role==5:
				return 1
		return speed_lognormal.fraction_done(pt.time)
	
	# Get theta-speed from p2 and p4.
	delta_theta = (p2.angle-p4.angle)/(fraction_done(p2)-fraction_done(p4))

	# Extrapolate theta out to p1 and p5.
	theta_s = p3.angle + delta_theta * (fraction_done(p1)-fraction_done(p3))
	theta_f = p3.angle + delta_theta * (fraction_done(p5)-fraction_done(p3))

	speed_lognormal.theta_s = theta_s
	speed_lognormal.theta_f = theta_f

	lognormal = speed_lognormal

	return lognormal

# Should I use trapezoids to regulate p2 and p4 point candidates?
run_limits = True

def get_stroke_combos(stroke_candidate):
	p1=stroke_candidate[0]
	p2s=stroke_candidate[1]
	p3=stroke_candidate[2]
	p4s=stroke_candidate[3]
	p5=stroke_candidate[4]

	# If a subset of p2s and p4s is *more valid*, use that subset.
	# Otherwise, use the whole set.
	def select_valid(pts):
		valid_pts = [pt for pt in pts if inflection_point_is_valid(p3,pt)]
		if len(valid_pts)>0:
			return valid_pts
		return pts
	
	if run_limits:
		p2s = select_valid(p2s)
		p4s = select_valid(p4s)

	ret = []
	for p2 in p2s:
		for p4 in p4s:
			ret.append([p1,p2,p3,p4,p5])
	
	return ret

class TrapezoidZone:
	def __init__(self,y_min,y_max,xt1,xt2,xb1,xb2):
		left_slope = (y_max-y_min)/(xt1-xb1)
		right_slope = (y_max-y_min)/(xt2-xb2)

		self.left_slope = left_slope
		self.left_pt = [xb1,y_min]

		self.right_slope = right_slope
		self.right_pt = [xb2,y_min]

		self.y_min = y_min
		self.y_max = y_max
	def contains(self,x,y):
		if y<self.y_min or y>self.y_max:
			#print("Out of bounds:",y,self.y_min,self.y_max)
			return False

		left_bound = self.left_slope * (x-self.left_pt[0]) + self.left_pt[1]
		right_bound = self.right_slope * (x-self.right_pt[0]) + self.right_pt[1]

		#print("Left:",left_bound,"Right:",right_bound,"Y:",y,"X:",x)

		return left_bound >= y and right_bound <= y

# Delta t is in milliseconds.
valid_traps = [
	TrapezoidZone(.44,.54,-75,-30,-140,-50),
	TrapezoidZone(.66,.74,50,130,25,60)
]

# Little tests.

assert valid_traps[1].contains(70,.73)

# Determines if a p2 or p4 point falls within expected human muscle ranges.
# Input type Point, Point
# Output type boolean
def inflection_point_is_valid(p3,pb):
	# pb is p2 or p4.
	delta_t = pb.time - p3.time
	speed_ratio = pb.speed/p3.speed

	ret = any([trap.contains(delta_t,speed_ratio) for trap in valid_traps])
	#print("valid:",ret,"delta_t: "+str(delta_t), "speed_ratio: "+str(speed_ratio))

	return ret

def is_valid(lognormal):
	if lognormal is None:
		return False
	if any([not np.isfinite(param) for param in [
		lognormal.D,
		lognormal.t_0,
		lognormal.mu,
		lognormal.sigma,
		lognormal.theta_s,
		lognormal.theta_f
	]]):
		return False
	return True

# Should I try all possible angle comos *with* all possible {p2,p3,p4} speed combos?
# Or, should I get the best speed-matching speed combo, then try all possible angle combos?
angle_duo_combinations = False

# When I've picked a *best* speed {p2,p3,p4} combo, should I pick the best {p2,p4} speed combo for angles? Or just try all combos for angles?
pick_best_inflections = False

# If I see a stroke with a small max. speed, should I discard it?
use_speed_threshold = True

# Input type Signal
# Output type LognormalStroke[]
def extract_all_lognormals(signal,peak_height_threshold=0):
	stroke_candidates = mark_stroke_candidates(signal) # StrokePoints[n]

	if use_speed_threshold:
		stroke_candidates = [candidate for candidate in stroke_candidates if candidate[2].speed>=peak_height_threshold]

	point_combos = [get_point_combos(candidate) for candidate in stroke_candidates] # Point[2][n]
	stroke_combos = [get_stroke_combos(candidate) for candidate in stroke_candidates] # Point[5][n]

	lognormals = []

	for candidate_idx in range(len(stroke_candidates)):
		pairs = point_combos[candidate_idx] # Point[2][n]
		strokes = stroke_combos[candidate_idx] # Point[5][n]

		if angle_duo_combinations:
			for pair in pairs:
				for stroke in strokes:
					lognormal = extract_sigma_lognormal(pair,stroke)
					if is_valid(lognormal):
						lognormals.append(lognormal)
		else:
			demo_stroke = strokes[0]
			p1=demo_stroke[0]
			p5=demo_stroke[4]

			speed_candidates = [(pair,extract_sigma_lognormal(pair,demo_stroke)) for pair in pairs]
			speed_candidates = [(pair,lognormal) for pair,lognormal in speed_candidates if is_valid(lognormal)]
			speed_candidates = [(pair,lognormal,get_speed_mse(lognormal,signal,p1,p5)) for pair,lognormal in speed_candidates]
			speed_candidates.sort(key=lambda x:x[2])
			best_pair = speed_candidates[0][0]

			if pick_best_inflections:
				p2_p4_combos = [point_combo for point_combo in pairs if point_combo[0].role==2 and point_combo[1].role==4]
				best_p2_p4 = p2_p4_combos[0]

				stroke = [
					demo_stroke[0],
					best_p2_p4[0],
					demo_stroke[2],
					best_p2_p4[1],
					demo_stroke[4]
				]

				lognormal = extract_sigma_lognormal(best_pair,stroke)
				if is_valid(lognormal):
					lognormals.append(lognormal)

			else:
				for stroke in strokes:
					lognormal = extract_sigma_lognormal(best_pair,stroke)
					if is_valid(lognormal):
						lognormals.append(lognormal)
	
	return lognormals

# Should competing {p2,p3,p4} speed combos be tested *locally* or *globally*?
compare_speed_globally = False

def get_speed_mse(lognormal,signal,p1,p5):
	stroke_speed = lognormal.signal(signal.time).speed
	target_speed = signal.speed
	squared_err = (stroke_speed-target_speed)**2
	if not compare_speed_globally:
		squared_err = squared_err[p1.idx:p5.idx]
	return np.mean(squared_err)