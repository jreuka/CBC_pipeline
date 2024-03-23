import pandas as pd
import numpy as np
from keras.models import Sequential
from keras.layers import LSTM
from keras.layers import Dense
from keras.layers import Bidirectional
from keras.layers import Masking
from keras.optimizers import SGD
from keras.callbacks import ReduceLROnPlateau
from sklearn.preprocessing import LabelEncoder
from keras.utils import to_categorical
from sklearn.preprocessing import MinMaxScaler
from tqdm import tqdm
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt


def equalise_num_samples(dd):
    """
    Function to equalise samples (animal with more trajectories - subsampled to number of other animal)
    """
    return dd.groupby('animal_id').sample(n=min(Counter(dd.animal_id).values()))

def sep_norm_labels(dd):
    """
    Function to normalise input data
    """
    f = dd.copy()
    y = f.pop('animal_id') - 1
    f = np.array(f.drop(columns=['time']))

    scaler = MinMaxScaler(feature_range=(0, 1))

    f = scaler.fit_transform(f)
    print(f.shape)
    #Numpy data array x of shape(samples, timesteps, features)
    f = f.reshape(len(f), 240, 2)
    f[np.isnan(f)] = -99
    y = y.astype(int)
    return f, y


def encode(lab):
    """
    Function to convert animal identity to labels
    """
    encoder = LabelEncoder()
    encoder.fit(lab)
    encoded_Y = encoder.transform(lab)
    # convert integers to dummy variables (i.e. one hot encoded)
    dummy_y = to_categorical(encoded_Y).reshape(len(encoded_Y), 2)
    return dummy_y


def create_datasets(dd):
    """
    Funtion to split and nomralise dataset
    """
    train, validate, test = np.split(dd.sample(frac=1),
                                     [int(.8 * len(dd)), int(.9 * len(dd))])

    tr_f, tr_y = sep_norm_labels(train)
    ts_f, ts_y = sep_norm_labels(test)
    vl_f, vl_y = sep_norm_labels(validate)

    tr_d_y = encode(tr_y)
    vl_d_y = encode(vl_y)

    return tr_f, tr_d_y, vl_f, vl_d_y, ts_f, ts_y

def create_test_data(dd):
    """
    Function to create test data
    """
    ts_f, ts_y = sep_norm_labels(dd)
    return ts_f, ts_y


def train_test_model(tr_f, tr_d_y, vl_f, vl_d_y, ts_f, ts_y, x):
    """
    Function creating LSTM, training and testing
    """
    # define LSTM
    model = Sequential()
    model.add(Masking(mask_value=-99, input_shape=(240, 2)))
    #model.add(Bidirectional(LSTM(128, return_sequences=True), input_shape=(240, 4)))
    model.add(Bidirectional(LSTM(128)))
    model.add(Dense(128, activation='tanh'))
    model.add(Dense(2, activation="softmax"))
    model.compile(loss='binary_crossentropy', optimizer=SGD(learning_rate=1.0, clipnorm=1.0), metrics=['accuracy'])

    if x == 0:
        model.summary()

    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.1, patience=1, min_lr=0.001)

    # fit model for one epoch on this sequence
    history = model.fit(tr_f, tr_d_y, validation_data=[vl_f, vl_d_y], epochs=30, callbacks=[reduce_lr], verbose=0)

    # evaluate LSTM
    yhat = model.predict(ts_f, verbose=0)

    racc = sum(np.argmax(yhat, axis=1) == ts_y) / len(ts_y)
    rrec1 = len([i for i in range(len(np.argmax(yhat, axis=1))) if list(np.argmax(yhat, axis=1))[i] == list(ts_y)[i] and list(np.argmax(yhat, axis=1))[i] == 0])/Counter(ts_y)[0]
    rrec2 = len([i for i in range(len(np.argmax(yhat, axis=1))) if list(np.argmax(yhat, axis=1))[i] == list(ts_y)[i] and list(np.argmax(yhat, axis=1))[i] == 1])/Counter(ts_y)[1]
    return racc, rrec1, rrec2, model

def test_date_data(dd1, dd2, model):
    """
    Function to train and test on dates seperately
    """
    d1t, d1ty = create_test_data(dd1)
    d2t, d2ty = create_test_data(dd2)

    d1yhat = model.predict(d1t, verbose=0)
    d2yhat = model.predict(d2t, verbose=0)

    raccd1 = sum(np.argmax(d1yhat, axis=1) == d1ty) / len(d1ty)
    raccd2 = sum(np.argmax(d2yhat, axis=1) == d2ty) / len(d2ty)

    rrec1_d1 = len([i for i in range(len(np.argmax(d1yhat, axis=1))) if list(np.argmax(d1yhat, axis=1))[i] == list(d1ty)[i] and list(np.argmax(d1yhat, axis=1))[i] == 0])/Counter(d1ty)[0]
    rrec2_d1 = len([i for i in range(len(np.argmax(d1yhat, axis=1))) if list(np.argmax(d1yhat, axis=1))[i] == list(d1ty)[i] and list(np.argmax(d1yhat, axis=1))[i] == 1])/Counter(d1ty)[1]

    rrec1_d2 = len([i for i in range(len(np.argmax(d2yhat, axis=1))) if list(np.argmax(d2yhat, axis=1))[i] == list(d2ty)[i] and list(np.argmax(d2yhat, axis=1))[i] == 0])/Counter(d2ty)[0]
    rrec2_d2 = len([i for i in range(len(np.argmax(d2yhat, axis=1))) if list(np.argmax(d2yhat, axis=1))[i] == list(d2ty)[i] and list(np.argmax(d2yhat, axis=1))[i] == 1])/Counter(d2ty)[1]

    return raccd1, raccd2, rrec1_d1, rrec2_d1, rrec1_d2, rrec2_d2


##### Main

##
# Run over complete data set
ls_files = ['./nnBrBr_long_2min_200.csv', './nnBrBr_long_2min_120.csv', './nnBrBr_long_2min_240.csv']

# uncomment for dataset including mask area - change dimension Line 86, 38 to input_shape=(240, 3)
#ls_files = ['./nBrBr_long_2min_200.csv', './nBrBr_long_2min_120.csv', './nBrBr_long_2min_240.csv']

for f in ls_files:
    dd = pd.read_csv(f)

    accs = []
    rec_an1 = []
    rec_an2 = []

    dd['time'] = dd.apply(lambda x: datetime.strptime(x['time'], '%Y-%m-%d %H:%M:%S'), axis=1)

    ddd = equalise_num_samples(dd)


    for x in tqdm(range(30)):
        tr_f, tr_d_y, vl_f, vl_d_y, ts_f, ts_y = create_datasets(ddd)

        racc, rrec1, rrec2, model = train_test_model(tr_f, tr_d_y, vl_f, vl_d_y, ts_f, ts_y, x)

        accs.append(racc)
        rec_an1.append(rrec1)
        rec_an2.append(rrec2)


    print(accs)
    print(np.mean(accs))

    print(Counter(ddd['animal_id']))

    plt.hist(accs)
    acdic = {'accs': accs, 'rec1': rec_an1, 'rec2': rec_an2}
    acpd = pd.DataFrame(acdic)
    acpd.to_csv('accurcies_' + f[2:])


ls_files = ['./nnBrBr_long_2min_200.csv', './nnBrBr_long_2min_120.csv', './nnBrBr_long_2min_240.csv']

##
# Run over datasets divided by dates
for f in ls_files:
    dd = pd.read_csv(f)

    accs = []
    rec_an1 = []
    rec_an2 = []

    accs_d2 = []
    accs_d3 = []
    rec_d2_an1 = []
    rec_d2_an2 = []
    rec_d3_an1 = []
    rec_d3_an2 = []

    dd['time'] = dd.apply(lambda x: datetime.strptime(x['time'], '%Y-%m-%d %H:%M:%S'), axis=1)

    d1 = datetime(2022, 8, 31)
    d2 = datetime(2022, 9, 30)

    ddd1 = dd.loc[(dd['time'] <= d1)]
    ddd2 = dd.loc[(dd['time'] > d1) & (dd['time'] <= d2)]
    ddd3 = dd.loc[(dd['time'] > d2)]

    ddd = equalise_num_samples(ddd1)


    for x in tqdm(range(30)):
        tr_f, tr_d_y, vl_f, vl_d_y, ts_f, ts_y = create_datasets(ddd)

        racc, rrec1, rrec2, model = train_test_model(tr_f, tr_d_y, vl_f, vl_d_y, ts_f, ts_y, x)

        raccd2, raccd3, rrec1_d2, rrec2_d2, rrec1_d3, rrec2_d3 = test_date_data(ddd2, ddd3, model)

        accs.append(racc)
        rec_an1.append(rrec1)
        rec_an2.append(rrec2)

        accs_d2.append(raccd2)
        accs_d3.append(raccd3)
        rec_d2_an1.append(rrec1_d2)
        rec_d2_an2.append(rrec2_d2)
        rec_d3_an1.append(rrec1_d3)
        rec_d3_an2.append(rrec2_d3)


    print(accs)
    print(np.mean(accs))

    print(Counter(ddd['animal_id']))

    plt.hist(accs)
    acdic = {'accs': accs, 'rec1': rec_an1, 'rec2': rec_an2}
    acdic = {'accs': accs, 'rec1': rec_an1, 'rec2': rec_an2,
             'accs_d2': accs_d2, 'rec_an1_d2': rec_d2_an1, 'rec_an2_d2': rec_d2_an2,
             'accs_d3': accs_d3, 'rec_an1_d3': rec_d3_an1,  'rec_an2_d2': rec_d3_an2}
    acpd = pd.DataFrame(acdic)
    acpd.to_csv('dates_accurcies_' + f[2:])