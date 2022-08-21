from time import time

log = False

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