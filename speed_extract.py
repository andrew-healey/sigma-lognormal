import numpy as np

class Point:
	def __init__(self,idx,signal,role):
		self.role=role
		
		self.velocity=signal.velocity[idx]
		self.position=signal.position[idx]
		self.time=signal.time[idx]
		self.angle=signal.angle[idx]
		self.speed=signal.speed[idx]

		self.idx=idx

def sign(num):
	return 1 if num>0 else (0 if num==0 else -1)
import re

from util import diff

def mark_stroke_candidates(signal):

	speed=signal.speed

	ddspeed=diff(diff(speed))

	points=[[0,"low"]]

	for _idx,speed in enumerate(speed[1:-1]):
		idx=_idx+1
		prev_speed=speed[idx-1]
		next_speed=speed[idx+1]
		
		is_local_max= speed>=prev_speed and speed>=next_speed
		if(is_local_max):
			points.append([idx,"high"])
		
		is_local_min = speed<=prev_speed and speed<=next_speed
		if(is_local_min):
			points.append([idx,"low"])
		
		ddspeed=ddspeed[_idx]
		next_ddspeed=0 if _idx==len(ddspeed)-1 else ddspeed[_idx+1]
		
		changes_sign=sign(ddspeed) != sign(next_ddspeed)
			
		if(changes_sign):
			points.append([idx,"flip"])

	points.append([len(speed)-1,"low"])

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
			Point(one,signal,1),
			[Point(two,signal,2) for two in twos],
			Point(three,signal,3),
			[Point(four,signal,4) for four in fours],
			Point(five,signal,5)
		]
		
	# Return type StrokePoints[]
	return [get_points(stroke_idx,points) for stroke_idx in stroke_idxes]

# Input type StrokePoints
# Output type Point[2][]
def get_point_combos(stroke_candidate):
	ret = []

	# Possible combos: p2, p3; p2, p4; p3, p4

	p1=stroke_candidate[0]
	p2s=stroke_candidate[1]
	p3=stroke_candidate[2]
	p4s=stroke_candidate[3]
	p5=stroke_candidate[4]

	for p2 in p2s:
		ret.append([p2,p3])

		for p4 in p4s:
			ret.append([p2,p4])

	for p4 in p4s:
		ret.append([p3,p4])

	return ret

from lognormal import LognormalStroke

def extract_sigma_lognormal(point_combo,points):
	pa,pb = point_combo
	p1,p2,p3,p4,p5 = points

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
	
	def avg(a,b):
		return (a+b)/2
	
	t_0 = avg(est_t_0(pa),est_t_0(pb))

	def delta(pt):
		return pt.time - t_0
	
	def est_D(pt):
		exponent = (( np.log(delta(pt)) - mu )**2) / (2*sigma_sq)
		return pt.vel * sigma*np.sqrt(2*pi)*delta(pt) * np.exp( exponent )
	
	D=avg(est_D(pa),est_D(pb))

	# Now, extract angle parameters.

	speed_lognormal = LognormalStroke(D,t_0,mu,sigma,None,None) # No angle information *yet*.

	def fraction_done(pt):
		return speed_lognormal.fraction_done(pt.time)
	
	# Get theta-speed from p2 and p4.
	delta_theta = (p2.angle-p4.angle)/(fraction_done(p2)-fraction_done(p4))

	# Extrapolate theta out to p1 and p5.
	theta_s = p3.angle + delta_theta * (fraction_done(p1)-fraction_done(p3))
	theta_e = p3.angle + delta_theta * (fraction_done(p5)-fraction_done(p3))

	speed_lognormal.theta_s = theta_s
	speed_lognormal.theta_e = theta_e

	lognormal = speed_lognormal

	return lognormal

def get_stroke_combos(stroke_candidate):
	p1=stroke_candidate[0]
	p2s=stroke_candidate[1]
	p3=stroke_candidate[2]
	p4s=stroke_candidate[3]
	p5=stroke_candidate[4]

	ret = []
	for p2 in p2s:
		for p4 in p4s:
			ret.append([p1,p2,p3,p4,p5])
	
	return ret

# Input type Signal
# Output type LognormalStroke[]
def extract_all_lognormals(signal):
	stroke_candidates = mark_stroke_candidates(signal) # StrokePoints[n]
	point_combos = [get_point_combos(candidate) for candidate in stroke_candidates] # Point[2][n]
	stroke_combos = [get_stroke_combos(candidate) for candidate in stroke_candidates] # Point[5][n]

	lognormals = []

	for candidate_idx in range(len(stroke_candidates)):
		pairs = point_combos[candidate_idx] # Point[2][n]
		strokes = stroke_combos[candidate_idx] # Point[5][n]

		for pair in pairs:
			for stroke in strokes:
				lognormal = extract_sigma_lognormal(pair,stroke)
				lognormals.append(lognormal)
	
	return lognormals