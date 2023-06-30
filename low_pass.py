import numpy as np
from scipy.signal import butter, lfilter, freqz, filtfilt,savgol_filter
import matplotlib.pyplot as plt


def butter_lowpass(cutoff, fs, order=5):
    return butter(order, cutoff, fs=fs, btype='low', analog=False)

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    
    y = filtfilt(b, a, data)
    return y

use_butter = True

cutoff_freq=20
order=3

N_window = 3
window = 2*N_window+1

from math import pi

def low_pass_pre(sequence,hz):
    vals=sequence[:,0]
    filtered=low_pass(vals,hz)
    
    length=sequence.shape[0]
    return np.concatenate((filtered.reshape((length,1)),sequence[:,1].reshape((length,1))),axis=1)

def butter_filt(sequence,hz):
  try:
    return butter_lowpass_filter(sequence,cutoff=cutoff_freq,fs=hz,order=order)
  except ValueError:
    return sequence

# TODO - remove delay on this by using filtfilt
def savgol_filt(sequence,hz):
	temp_out = savgol_filter(sequence,window_length=window,polyorder=3,deriv=0)
	delay = N_window


low_pass = butter_filt if use_butter else savgol_filt