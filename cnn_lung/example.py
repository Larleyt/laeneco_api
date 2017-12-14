import os
import numpy as np
import scipy.io.wavfile as wav
from numpy.lib import stride_tricks
import pickle
from keras.models import model_from_json
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-audio_path")
args = parser.parse_args()
audio_path = args.audio_path
from PIL import Image
import warnings
import soundfile as sf
warnings.filterwarnings('ignore')

CUR_PATH = os.path.dirname(os.path.abspath(__file__))


def logscale_spec(spec, sr=44100, factor=20.):
    timebins, freqbins = np.shape(spec)
    scale = np.linspace(0, 1, freqbins) ** factor
    scale *= (freqbins-1)/max(scale)
    scale = np.unique(np.round(scale))
    # create spectrogram with new freq bins
    newspec = np.complex128(np.zeros([timebins, len(scale)]))
    for i in range(0, len(scale)):
        if i == len(scale)-1:
            newspec[:,i] = np.sum(spec[:,scale[i]:], axis=1)
        else:
            newspec[:,i] = np.sum(spec[:,scale[i]:scale[i+1]], axis=1)
    # list center freq of bins
    allfreqs = np.abs(np.fft.fftfreq(freqbins*2, 1./sr)[:freqbins+1])
    freqs = []
    for i in range(0, len(scale)):
        if i == len(scale)-1:
            freqs += [np.mean(allfreqs[scale[i]:])]
        else:
            freqs += [np.mean(allfreqs[scale[i]:scale[i+1]])]
    return newspec, freqs

def stft(sig, frameSize, overlapFac=0.5, window=np.hanning):
    win = window(frameSize)
    hopSize = int(frameSize - np.floor(overlapFac * frameSize))
    # zeros at beginning (thus center of 1st window should be for sample nr. 0)
    samples = np.append(np.zeros(np.floor(frameSize/2.0)), sig)
    # cols for windowing
    cols = np.ceil( (len(samples) - frameSize) / float(hopSize)) + 1
    # zeros at end (thus samples can be fully covered by frames)
    samples = np.append(samples, np.zeros(frameSize))
    frames = stride_tricks.as_strided(samples, shape=(cols, frameSize), strides=(samples.strides[0]*hopSize, samples.strides[0])).copy()
    frames *= win
    return np.fft.rfft(frames)

def stft_eval(samplerate, samples, binsize=2048, plotpath=None, colormap="jet"):
    s = stft(samples, binsize)
    sshow, freq = logscale_spec(s, factor=1.0, sr=samplerate)
    ims = 20.*np.log10(np.abs(sshow)/10e-6) # amplitude to decibel
    timebins, freqbins = np.shape(ims)
    return np.transpose(ims[:, :80])

def extract_zip_spec(path):
    rate, sample = wav.read(path)
    spec = stft_eval(rate, sample)
    if (spec.shape[1] > 500):
        spec = spec[:, spec.shape[1]-500:]
    result = np.array(Image.fromarray(spec).resize((150, int(spec.shape[0])), Image.NEAREST))
    result[np.isnan(result)] = 0
    result[np.isinf(result)] = 0
    return result

def load_nn(path):
    arch, w = pickle.load(open(path, 'rb'))
    model = model_from_json(arch)
    model.set_weights(w)
    return model

def predict(wav_path, model_path):
    data = extract_zip_spec(wav_path)
    mean, std = pickle.load(open(
        os.path.join(CUR_PATH, "mean_and_std.pkl"), 'rb'))
    data = (data - mean) / std
    data = data.reshape((1,1,data.shape[0], data.shape[1]))
    nn = load_nn(model_path)
    pred = nn.predict(data)
    return pred[0][0]

model_path = os.path.join(CUR_PATH, "cnn_1.model")
if ('.ogg' in audio_path):
    data, samplerate = sf.read(audio_path)
    audio_path = ".".join(audio_path.split('.')[:-1]) + "_converted.wav"
    sf.write(audio_path, data, samplerate)
pred = predict(audio_path, model_path)
print(np.round(pred,3))
