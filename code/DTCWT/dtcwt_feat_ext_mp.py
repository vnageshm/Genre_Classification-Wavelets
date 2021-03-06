import wave, tarfile, os, librosa
import numpy as np
import pywt
from collections import Counter
import scipy
from time import time
from multiprocessing import Pool
import dtcwt

tf = tarfile.open('dataset/genres.tar.gz')
trans = dtcwt.Transform1d(biort='antonini', qshift='qshift_d')

def calculate_entropy(list_values):
	counter_values = Counter(list_values).most_common()
	probabilities = [elem[1]/len(list_values) for elem in counter_values]
	entropy=scipy.stats.entropy(probabilities)
	return entropy

def calculate_statistics(list_values):
	n5 = np.nanpercentile(list_values, 5)
	n25 = np.nanpercentile(list_values, 25)
	n75 = np.nanpercentile(list_values, 75)
	n95 = np.nanpercentile(list_values, 95)
	median = np.nanpercentile(list_values, 50)
	mean = np.nanmean(list_values)
	std = np.nanstd(list_values)
	var = np.nanvar(list_values)
	rms = np.nanmean(np.sqrt(list_values**2))
	return [n5, n25, n75, n95, median, mean, std, var, rms]

def calculate_crossings(list_values):
	zero_crossing_indices = np.nonzero(np.diff(np.array(list_values) > 0))[0]
	no_zero_crossings = len(zero_crossing_indices)
	mean_crossing_indices = np.nonzero(np.diff(np.array(list_values) > np.nanmean(list_values)))[0]
	no_mean_crossings = len(mean_crossing_indices)
	return [no_zero_crossings, no_mean_crossings]

def get_features(list_values):
	entropy = calculate_entropy(list_values)
	crossings = calculate_crossings(list_values)
	statistics = calculate_statistics(list_values)
	return [entropy] + crossings + statistics

def dwt_feat_ext(wav_name):
	X_data = []
	# trans = dtcwt.Transform1d()
	# for i in tqdm(range(len(wav_names))):
	f = tf.extractfile(wav_name)
	d, fs = librosa.load(f)
	forw = trans.forward(d, nlevels=17)
	# list_coeff = pywt.wavedec(d, wavelet_name)
	features = []
	for coeff in forw.highpasses:
		temp = (np.abs(coeff.squeeze()))
		features += get_features(temp)
	features += get_features(forw.lowpass.squeeze())
	X_data.append(features)
	return X_data

if __name__ == '__main__':
	wav_names = [fname for fname in tf.getnames() if '.wav' in fname.split(os.sep)[-1]]
	# wav_names1 = wav_names[:100]
	start = time()
	# result = []
	with Pool(processes = 12) as pool:
		result = pool.map(dwt_feat_ext, wav_names)
		# result = result.get()
	pool.close()
	end = time()
	out = np.array(result)
	np.save('feat_data/dtcwt_15_lvl17', out)
	# print('Shape of array: ' + str(out.shape))
	print('Time taken: ' + str((end - start)/60) + ' mins')
	# print(out)
