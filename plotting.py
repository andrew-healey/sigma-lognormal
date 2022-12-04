import matplotlib.pyplot as plt
import numpy as np

plotters = {
	"xs": lambda signal: (signal.time, signal.position[:,0]),
	"ys": lambda signal: (signal.time, signal.position[:,1]),
	"signals": lambda signal: (signal.position[:,0], -signal.position[:,1]),
	"velocities": lambda signal: (signal.velocity[:,0], -signal.velocity[:,1]),
	"speeds": lambda signal: (signal.time[1:], signal.speed),
	"angles": lambda signal: (signal.time[1:], signal.angle)
}

def show_plot(plot_type,signals,should_scatter=True):
	for signal in signals:
		x,y = plotters[plot_type](signal)
		if should_scatter:
			plt.scatter(x,y)
		else:
			plt.plot(x,y)
	plt.show()

import matplotlib.animation
from IPython.display import HTML

def animate_plot(plot_type,signals):
	sequences = [plotters[plot_type](signal) for signal in signals] # list of (x,y) tuples
	all_xs,all_ys = zip(*sequences) # list of x lists, list of y lists

	x_bounds = (min([min(xs) for xs in all_xs]),max([max(xs) for xs in all_xs]))
	y_bounds = (min([min(ys) for ys in all_ys]),max([max(ys) for ys in all_ys]))
	max_length = max([len(xs) for xs in all_xs])

	fig, ax = plt.subplots()
	ax.axis([*x_bounds,*y_bounds])
	lines = [ax.plot([],[])[0] for _ in signals]
	plt.close(fig) # I'll manually render this with HTML. Hide the default output.

	def animate(i):
		for line,(x,y) in zip(lines,sequences):
			line.set_data(x[:i], y[:i])
		return lines

	ani = matplotlib.animation.FuncAnimation(fig, animate, frames=max_length,blit=True)

	writergif = matplotlib.animation.PillowWriter(fps=30) 
	ani.save("plot.gif", writer=writergif)

	return HTML(ani.to_jshtml())