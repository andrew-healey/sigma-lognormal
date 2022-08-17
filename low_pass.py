import numpy as np
from scipy.signal import butter, lfilter, freqz, filtfilt
import matplotlib.pyplot as plt


def butter_lowpass(cutoff, fs, order=5):
    return butter(order, cutoff, fs=fs, btype='low', analog=False)

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    
    y = filtfilt(b, a, data)
    return y

cutoff_freq=15
order=4

from math import pi
delay=1/(2*pi*cutoff_freq)
def low_pass(sequence,hz):
    vals=sequence[:,0]
    filtered=butter_lowpass_filter(vals,cutoff=cutoff_freq,fs=hz,order=order)
    
    length=sequence.shape[0]
    return np.concatenate((filtered.reshape((length,1)),sequence[:,1].reshape((length,1))),axis=1)
