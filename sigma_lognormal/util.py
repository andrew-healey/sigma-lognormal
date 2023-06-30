import numpy as np

def delta(arr):
	return arr[1:]-arr[:-1]

def diff(arr,time):
	da = delta(arr)
	dt = delta(time)
	return da/dt

def l2(arr):
	return np.sqrt(arr[:,0]**2+arr[:,1]**2)