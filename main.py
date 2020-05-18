from flask import Flask, render_template, request, redirect, url_for, flash
import librosa
import joblib
import numpy as np
from werkzeug.utils import secure_filename
import os
from flask_wtf import FlaskForm
from wtforms import FileField, SelectField
from flask_wtf.file import FileRequired
from scipy.ndimage.filters import maximum_filter
import scipy.ndimage as ndimage

app = Flask(__name__)


app.config.update(dict(
    SECRET_KEY="rejirh234",
    WTF_CSRF_SECRET_KEY="l2njW"
))


class MyForm(FlaskForm):
    dropdown = SelectField('Choose genre:', choices=[('All', 'All genres'), ('Pop', 'Pop'), ('Hiphop', 'Hip-Hop'), ('Folk', 'Folk'), ('Rock', 'Rock')])
    file = FileField('Choose file:', validators=[FileRequired()])

ALLOWED_EXTENSIONS = ['mp3']

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=('GET', 'POST'))
def submit():
    form = MyForm()

    if form.validate_on_submit():
        genre = form.dropdown.data
        file = form.file.data
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(filename))
        else:
            flash('mp3 file format is required')
            return redirect('/')

        if genre == 'Pop':
            directory = 'music/Pop'
            index = joblib.load('index_pop.pkl')
        elif genre == 'Hiphop':
            directory = 'music/Hiphop'
            index = joblib.load('index_hiphop.pkl')
        elif genre == 'Folk':
            directory = 'music/Folk'
            index = joblib.load('index_folk.pkl')
        elif genre == 'Rock':
            directory = 'music/Rock'
            index = joblib.load('index_rock.pkl')
        else:
            directory = 'music'
            index = joblib.load('index_all.pkl')

        path_f = []
        for d, dirs, files in os.walk(directory):
            audio = filter(lambda x: x.endswith('.mp3'), files)
            for f in audio:
                path = os.path.join(d, f)  # формирование адреса
                path_f.append(path)  # добавление адреса в список

        # print(path_f)

        def read_and_resample(path, sample_rate):
            # read and resample to 22KHz
            y, sr = librosa.load(path, sr=sample_rate)
            # print(f"{path}")
            return y

        sample_rate = 22050
        # reading request audio
        request_data = read_and_resample(filename, sample_rate)
        # Let's make and display a mel-scaled power (energy-squared) spectrogram
        S = librosa.feature.melspectrogram(request_data, sr=sample_rate, n_mels=128)
        neighborhood_size = 10
        # sec/sample - constant for all files
        wav = request_data
        time_resolution = (wav.shape[0] / sample_rate) / S.shape[1]
        # print("Time resolution:", time_resolution)

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

            # print(len(points))
            return sorted(points)

        request_constellation = form_constellation(request_data, sample_rate)
        target = (int(1 / time_resolution), int(3 / time_resolution), -30, 30)  # start, end, Hz low, Hz high

        def build_constellation_index(constellation_collection, target):
            result_index = {}
            for name, points in constellation_collection.items():
                # print(name)
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

        request = build_constellation_index({filename: request_constellation}, target)
        # print(path_f)
        times = dict((name, []) for name in path_f)
        for key, v in request.items():
            if key in index:
                for t_r, name_r in v:
                    for pair in index[key]:
                        t_i, name_i = pair
                        times[name_i].append(t_i - t_r)
        # print(times)
        result = []
        for name, matches in times.items():
            if matches:
                result.append((name, max(matches)))
        # print(result)

        result_sorted = sorted(result, key=lambda x: x[1], reverse=True)
        output = result_sorted[0][0]
        output1 = output.split('/')
        output2 = output1[2].split('.mp3')
        final_result = output2[0]
        # print(final_result)
        return redirect(url_for('result', result=final_result))
    return render_template('submit.html', form=form)


@app.route('/result')
def result():
    return render_template("result.html", song_name=request.args.get('result'))


@app.route('/add', methods=('GET', 'POST'))
def add():
    form = MyForm()

    if form.validate_on_submit():
        genre = form.dropdown.data
        file = form.file.data
        if genre == 'Pop':
            directory = 'music/Pop'
        elif genre == 'Hiphop':
            directory = 'music/Hiphop'
        elif genre == 'Folk':
            directory = 'music/Folk'
        elif genre == 'Rock':
            directory = 'music/Rock'
        else:
            directory = 'music'

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(directory + '/' + filename))
        else:
            flash('mp3 file format is required')
            return redirect('/add')


        path_f = []
        for d, dirs, files in os.walk(directory):
            audio = filter(lambda x: x.endswith('.mp3'), files)
            for f in audio:
                path = os.path.join(d, f)  # формирование адреса
                path_f.append(path)  # добавление адреса в список

        # print(path_f)

        def read_and_resample(path, sample_rate):
            # read and resample to 22KHz
            y, sr = librosa.load(path, sr=sample_rate)
            # print(f"{path}")
            return y

        dataset = {}
        sample_rate = 22050
        # reading all audios
        for path in path_f:
            dataset[path] = read_and_resample(path, sample_rate)

        y = dataset[directory + '/' + filename]
        # # Let's make and display a mel-scaled power (energy-squared) spectrogram
        S = librosa.feature.melspectrogram(y, sr=sample_rate, n_mels=128)
        neighborhood_size = 10
        # sec/sample - constant for all files
        wav = dataset[directory + '/' + filename]
        time_resolution = (wav.shape[0] / sample_rate) / S.shape[1]
        # print("Time resolution:", time_resolution)

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

            # print(len(points))
            return sorted(points)

        constellations = {}
        for name, wav in dataset.items():
            constellations[name] = form_constellation(wav, sample_rate)

        target = (int(1 / time_resolution), int(3 / time_resolution), -30, 30)  # start, end, Hz low, Hz high

        def build_constellation_index(constellation_collection, target):
            result_index = {}
            for name, points in constellation_collection.items():
                # print(name)
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
        if genre == 'Pop':
            joblib.dump(index, 'index_pop.pkl')
        elif genre == 'Hiphop':
            joblib.dump(index, 'index_hiphop.pkl')
        elif genre == 'Folk':
            joblib.dump(index, 'index_folk.pkl')
        elif genre == 'Rock':
            joblib.dump(index, 'index_rock.pkl')
        else:
            joblib.dump(index, 'index_all.pkl')

        # rebuilding index for all songs
        directory_all = 'music'
        path_all = []
        for d, dirs, files in os.walk(directory_all):
            audio = filter(lambda x: x.endswith('.mp3'), files)
            for f in audio:
                path = os.path.join(d, f)  # формирование адреса
                path_f.append(path)  # добавление адреса в список

        # print(path_all)

        dataset_all = {}
        # reading all audios
        for path in path_all:
            dataset_all[path] = read_and_resample(path, sample_rate)

        constellations_all = {}
        for name, wav in dataset_all.items():
            constellations_all[name] = form_constellation(wav, sample_rate)

        index_all = build_constellation_index(constellations_all, target)
        joblib.dump(index_all, 'index_all.pkl')
        flash('File was successfully added to the database')
        return redirect('/')
    return render_template('add.html', form=form)

