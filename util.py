import numpy as np

def delta(arr):
	return arr[1:]-arr[:-1]

def diff(arr,time):
	da = delta(arr)
	dt = delta(time)
	return da/dt