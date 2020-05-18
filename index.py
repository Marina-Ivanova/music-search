import librosa
import os
import numpy as np
from scipy.ndimage.filters import maximum_filter
import scipy.ndimage as ndimage
from sklearn.externals import joblib


def main():
    directory = 'music/Rock'
    path_f = []
    for d, dirs, files in os.walk(directory):
        audio = filter(lambda x: x.endswith('.mp3'), files)
        print(audio)
        for f in audio:
            path = os.path.join(d,f) # формирование адреса
            path_f.append(path) # добавление адреса в список

    print(path_f)

    def read_and_resample(path, sample_rate):
        # read and resample to 22KHz
        y, sr = librosa.load(path, sr=sample_rate)
        print(f"{path}")
        return y

    dataset = {}
    sample_rate = 22050
    # reading all audios
    for path in path_f:
        dataset[path] = read_and_resample(path, sample_rate)

    print(dataset)

    y = dataset["music/Rock/Black Elk - Toggle.mp3"]

    # Let's make and display a mel-scaled power (energy-squared) spectrogram
    S = librosa.feature.melspectrogram(y, sr=sample_rate, n_mels=128)
    neighborhood_size = 10

    # sec/sample - constant for all files
    wav = dataset["music/Rock/Black Elk - Toggle.mp3"]
    time_resolution = (wav.shape[0] / sample_rate) / S.shape[1]
    print("Time resolution:", time_resolution)

    def form_constellation(wav, sample_rate):
        S = librosa.feature.melspectrogram(wav, sr=sample_rate, n_mels=256, fmax=4000)
        S = librosa.power_to_db(S, ref=np.max)
        # get local maxima
        Sb = maximum_filter(S, neighborhood_size) == S

        Sbd, num_objects = ndimage.label(Sb)
        objs = ndimage.find_objects(Sbd)
        points = []
        for dy, dx in objs:
            x_center = (dx.start + dx.stop - 1) // 2
            y_center = (dy.start + dy.stop - 1) // 2
            if (dx.stop - dx.start) * (dy.stop - dy.start) == 1:
                points.append((x_center, y_center))

        print(len(points))
        return sorted(points)

    constellations = {}
    for name, wav in dataset.items():
        constellations[name] = form_constellation(wav, sample_rate)

    target = (int(1 / time_resolution), int(3 / time_resolution), -30, 30)    # start, end, Hz low, Hz high

    def build_constellation_index(constellation_collection, target):
        result_index = {}
        for name, points in constellation_collection.items():
            print(name)
            for point in points:
                f1 = point[1]
                tg = [p for p in points if
                            point[0] + target[0] <= p[0] < point[0] + target[1]
                            and
                            point[1] + target[2] <= p[1] < point[1] + target[3]
                     ]
                for p in tg:
                    f2 = p[1]
                    dt = p[0] - point[0]
                    t = p[0]

                    if (f1, f2, dt) in result_index:
                        result_index[(f1, f2, dt)].append((t, name))
                    else:
                        result_index[(f1, f2, dt)] = [(t, name)]
        return result_index

    index = build_constellation_index(constellations, target)
    joblib.dump(index, 'index_rock.pkl')


if __name__ == "__main__":
  main()