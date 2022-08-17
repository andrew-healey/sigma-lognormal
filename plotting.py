import matplotlib.pyplot as plt
import numpy as np

def plot_signals(signals):
	for signal in signals:
		plt.scatter(signal.position[:,0],-signal.position[:,1])
	plt.show()