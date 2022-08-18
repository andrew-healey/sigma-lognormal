from time import time
def timer():
	last_time = time()
	def inner(*evt_name):
		nonlocal last_time
		new_time = time()
		duration = new_time - last_time
		last_time = new_time
		print(*evt_name,"-",duration)
	return inner