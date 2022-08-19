import matplotlib.pyplot as plt
import numpy as np

def plot_signals(signals):
	for signal in signals:
		plt.scatter(signal.position[:,0],-signal.position[:,1])
	plt.show()

def plot_velocities(signals):
	for signal in signals:
		plt.scatter(signal.velocity[:,0],-signal.velocity[:,1])
	plt.show()

def plot_speeds(signals):
	for signal in signals:
		plt.scatter(signal.time[1:],signal.speed)
	plt.show()