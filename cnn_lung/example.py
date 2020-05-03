import os
import numpy as np
import scipy.io.wavfile as wav
from numpy.lib import stride_tricks
import pickle
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-audio_path")
args = parser.parse_args()
audio_path = args.audio_path
import warnings
warnings.filterwarnings('ignore')
import soundfile as sf
from python_speech_features import mfcc

CUR_PATH = os.path.dirname(os.path.abspath(__file__))

def get_feat(sig, rate):
    mfcc_feat = mfcc(sig,rate,nfft=2048, lowfreq=50, highfreq=2000)
    # print(100*len(sig)/rate)
    # print(len(mfcc_feat))
    if (abs((100*len(sig)/rate) / len(mfcc_feat) - 1) > 0.2):
        winstep = np.round(0.01*(len(mfcc_feat)/(100*len(sig)/rate)), 2)
        mfcc_feat = mfcc(sig,rate,nfft=2048, lowfreq=50, highfreq=2000, winstep=winstep)
    # print(len(mfcc_feat))
    return mfcc_feat

def pad(x, l = 250):
    if (x.shape[0] == l):
        return x
    if (x.shape[0] < l):
        pad = (l - len(x)) // 2
        x = np.concatenate((np.zeros([pad,x.shape[1]]),x,np.zeros([pad,x.shape[1]])))
    else:
        pad = (len(x) - l) // 2
        if (pad == 0):
            x = x[1:, :]
        else:
            x = x[pad:-pad,:]
    if (x.shape[0] == l-1):
        x = np.concatenate((x, np.zeros([1,x.shape[1]])))
    return x[:l]

def load_model(path):
    model = pickle.load(open(path, 'rb'))
    return model

def predict(wav_path, model_path):
    (rate, sig) = wav.read(wav_path)
    data = pad(get_feat(sig, rate)).flatten()
    if (len(data) == 0):
        return 0
    nn = load_model(model_path)
    pred = nn.predict([data])
    return pred[0]

model_path = os.path.join(CUR_PATH, "vclf.pkl")
if ('.ogg' in audio_path):
    data, samplerate = sf.read(audio_path)
    audio_path = ".".join(audio_path.split('.')[:-1]) + "_converted.wav"
    sf.write(audio_path, data, samplerate)
pred = predict(audio_path, model_path)
print(np.round(pred,3))
