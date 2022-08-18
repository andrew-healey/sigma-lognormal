from scipy.interpolate import CubicSpline,UnivariateSpline
from math import floor
import numpy as np

hz=200
period=1000/hz

def round_to_period(ms):
    return period*floor(ms/period)

def resample(locs):
    times=locs[:,-1]
    spline=CubicSpline(times,locs[:,:-1])
    new_times=np.arange(round_to_period(times[0]),round_to_period(times[-1]),period)
    
    resampled_locs=spline(new_times)
    return np.concatenate((resampled_locs,new_times.reshape((new_times.shape[0],1))),1)

from scipy.signal import savgol_filter

def smooth(sequence,window=10):
    loc_data=sequence[:,:-1]
    smooth_data=savgol_filter(loc_data,window,3,axis=0)
    return np.concatenate((smooth_data,sequence[:,-1:]),axis=1)

padding=50 # 50 ms
def pad(locs):
    first=locs[0]
    last=locs[-1]
    
    
    front_times=np.arange(round_to_period(first[-1:]-padding),first[-1:],period)[:,np.newaxis]
    front_vals=np.repeat(first[np.newaxis,:-1],len(front_times),axis=0)
    print(front_times.shape,front_vals.shape)
    front_padding=np.append(front_vals,front_times,axis=1)
    back_times=np.arange(round_to_period(last[np.newaxis,-1:]+padding),last[-1:],period)[:,np.newaxis]
    back_vals=np.repeat(last[np.newaxis,:-1],len(back_times),axis=0)
    back_padding=np.append(back_vals,back_times,axis=1)
    
    return np.concatenate((front_padding,locs,back_padding))

def diff(sequence):
    mult=np.array([1]).repeat(sequence.shape[1])
    mult[-1]=0
    delta=sequence[1:]-sequence[:-1]*mult
    length=sequence.shape[0]-1
    dt=(sequence[1:,-1]-sequence[:-1,-1]).reshape((length,1)).repeat(sequence.shape[1]-1,axis=1)
    dt_multiplier=np.concatenate((dt,np.ones((length,1))),axis=1)
    return delta/dt_multiplier

def l2(sequence):
    length=sequence.shape[0]
    mag=np.sqrt(sequence[:,0]**2+sequence[:,1]**2)
    return np.concatenate((mag.reshape((length,1)),sequence[:,2].reshape((length,1))),axis=1)

from low_pass import low_pass_pre

def get_angle(vels):
	smoother_vels=smooth(vels,window=30)

	raw_angle=np.arctan2(smoother_vels[:,1],smoother_vels[:,0])
	delta_angle=raw_angle[1:]-raw_angle[:-1]
	smooth_delta=(delta_angle+np.pi)%(2*np.pi)-np.pi
	smooth_angle=np.cumsum( np.concatenate((raw_angle[:1],smooth_delta)))
	return smooth_angle

from signals import Signal

def preprocess(locs):
	resampled = resample(locs)
	smoothed=smooth(resampled)
	#padded=pad(smoothed)

	raw_vel=diff(smoothed)

	speed=l2(raw_vel)
	smooth_speed=low_pass_pre(speed,hz)

	smooth_angle=get_angle(raw_vel)

	return Signal(smoothed[:,:2],raw_vel[:,:2],smooth_angle,smooth_speed[:,0],smoothed[:,2])