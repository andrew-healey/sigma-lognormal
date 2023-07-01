from time import time

log = False

"""
A timer for profiling performances.
This returns a mini-function--tell the mini-function what step you just completed, and it'll tell you how long it took.
"""
def timer():
	last_time = time()
	def inner(*evt_name):
		nonlocal last_time
		new_time = time()
		duration = new_time - last_time
		last_time = new_time
		if log:
			print(*evt_name,"-",duration)
	return inner