"""
Table of Contents:
    -print_pickle
    -debug
    -column_append
    -to_float
    -random_df
    -df_identifier
    -first_col
    -column_apply
    -combine_dfs
    -hash_numpy_int
    -hash_numpy
    -hash_df
    -quick_save
    -quick_load
    -try_mkdir
    -binarize
    -current_time
    -print_current_time
    -is_categorical
    -quick_cache
    -interaction_terms
    -add_index_to_columns

"""
from __future__ import print_function
import numpy as np
import pandas as pd
import cPickle as pickle
import gc

from pdb import set_trace
from os import makedirs, path
from datetime import datetime
from sklearn.preprocessing import LabelBinarizer

from decorators import default_catcher
import SETTINGS

debug = set_trace


def print_pickle(filename):
    """
    Prints the content of a pickle file.
    """
    with open(filename) as infile:
        x = pickle.load(infile)
        print(x)
    return x


def column_append(s, df):
    """
    Appends a value to the name of a dataframe.
    """
    assert isinstance(df, pd.DataFrame)
    return df.rename(columns=lambda c: "{}_{}".format(c, s))


@default_catcher(np.nan)
def to_float(s):
    return float(s)


def random_df(rows, cols):
    """
    Returns a normally distributed random dataframe with input dimensions.
    """
    return pd.DataFrame(np.random.randn(rows, cols))


def df_identifier(df):
    """
    Gets a (hopefully) unique identifier for a dataframe.
    """
    assert isinstance(df, pd.DataFrame)
    return "".join(map(str, df.columns))


def first_col(df):
    """
    Returns the first column of a DataFrame
    """
    assert isinstance(df, pd.DataFrame)
    return df[df.columns[0]]


def column_apply(df, func, *args, **kwargs):
    """
    Returns the resulting dataframe from applying a function to each column of an input dataframe.
    """
    assert isinstance(df, pd.DataFrame)
    if df.shape[1] == 1:
        return func(df)
    elif df.shape[1] == 0:
        return pd.DataFrame()
    applied = [func(df[[col]], *args, **kwargs) for col in df]
    return combine_dfs(applied)


def combine_dfs(dfs):
    """
    Takes in a list of dataframes with the same number of rows and appends them together.
    """
    if len(dfs) == 0:
        return pd.DataFrame()
    return pd.concat(dfs, axis=1)


def hash_numpy_int(x):
    """Returns int of hashed value of numpy array.
    """
    assert isinstance(x, np.ndarray)
    return hash(tuple(map(to_float, x.flatten())))


def hash_numpy(x):
    """Returns string of hashed value of numpy array.
    """
    assert isinstance(x, np.ndarray)
    return "{}_{}".format(x.shape, hash_numpy_int(x))


def hash_df(df):
    """Returns hashed value of pandas data frame.
    """
    return hash_numpy(df.as_matrix())


def quick_save(directory, filename, obj):
    """Quickly pickle an object in a file.
    """
    try_mkdir(directory)
    gc.disable()
    new_filename = path.join(directory, filename + ".pickle")
    with open(new_filename, 'w') as outfile:
        pickle.dump(obj, outfile, pickle.HIGHEST_PROTOCOL)
    gc.enable()


def quick_load(directory, filename):
    """Quickly unpickle an object from a file.
    """
    new_filename = path.join(directory, filename + ".pickle")
    gc.disable()
    with open(new_filename) as infile:
        obj = pickle.load(infile)
    gc.enable()
    return obj


def try_mkdir(directory):
    """ try to make directory
    """
    try:
        makedirs(directory)
    except OSError:
        pass


def binarize(data):
    """ convert categorical data into a matrix of 0's and 1's
    """
    lb = LabelBinarizer()
    return lb.fit_transform(data)


def current_time():
    """ Returns current time as a string.
    """
    return str(datetime.now())


def print_current_time():
    """ prints current time
    """
    print(current_time())


def is_categorical(X):
    """ utility method to determine whether a feature is categorical
    """
    assert isinstance(X, np.ndarray)
    size, = X.shape
    try:  # non-numerical
        X = X.astype(np.float)
    except ValueError:
        return True
    if not np.allclose(X, X.astype(np.int)):  # floating point numbers
        return False
    num_unique, = np.unique(X).shape
    if num_unique > SETTINGS.IS_CATEGORICAL.THRESHOLD * size:
        return False
    else:
        return True


def quick_cache(unique_name, func, *args, **kwargs):
    """ an easy to use fast cache
    """
    try:
        return quick_load(SETTINGS.QUICK_CACHE.DIRECTORY, unique_name)
    except:
        print("Quick Cache Miss: {}".format(unique_name))
        result = func(*args, **kwargs)
        quick_save(SETTINGS.QUICK_CACHE.DIRECTORY, unique_name, result)
        return result


def interaction_terms(df, feat1, feat2):
    """Creates a new df with (len(feat1) + 1) * (len(feat2) + 1) - 1 features, with each new feature as a product of a feature in feat1 and a feature in feat2.
    """
    assert isinstance(df, pd.DataFrame)
    assert isinstance(feat1, set)
    assert isinstance(feat2, set)
    assert feat1.intersection(feat2) == set()
    cols = set(df.columns)
    assert feat1.issubset(cols)
    assert feat2.issubset(cols)

    terms = []
    feat1_df = df[list(feat1)]
    terms.append(feat1_df)
    terms.append(df[list(feat2)])

    for f in feat2:
        col = np.array(df[f]).reshape(-1, 1)
        prod = col * feat1_df
        renamed = prod.rename(columns=lambda x: "{}_*_{}".format(x, f))
        terms.append(renamed)

    return combine_dfs(terms)


def add_index_to_columns(df):
    return pd.DataFrame(df.as_matrix(), columns=["{}_{}".format(i, j) for i, j in enumerate(df.columns)])


""" ~~~~~~~~~~~~~~TODO~~~~~~~~~~~~~~~~~~~~~~ """

from param import Param


def split_and_classify(data, target, split_col):
    identifier = "data_{}_".format(split_col)
    column = data[:, split_col]

    uniques = Param.f(identifier + "uniques", np.unique, column)
    groups = [(v, np.where(column == v)) for v in uniques]

    prediction = np.zeros(data.shape[0])
    for v, group in groups:
        tmp_identifier = identifier + str(v)
        tmp_target = None if target is None else target[group]
        tmp_pred = classify(data[group], tmp_target, tmp_identifier)
        prediction[group] = tmp_pred

    return prediction


def classify(data, target, data_identifier):

    def sgd_classify_and_score(loss, penalty):
        def get_classifier():
            clf = SGDClassifier(loss=loss, penalty=penalty, n_iter=20, random_state=8675309, shuffle=True, class_weight="auto")
            clf.fit(data, target)
            clf_score = score(target, clf.predict(data))
            return clf, clf_score

        identifier = '_'.join((data_identifier, loss, penalty, "classifier"))
        clf, clf_score = Param.f(identifier, get_classifier)
        return clf.predict(data), clf_score

    """ in case target has only one value """
    target_unique = Param.f(
        data_identifier + "_target_unique", np.unique, target)
    if len(target_unique) == 1:
        return target_unique[0] * np.ones(data.shape[0])

    # losses = ['hinge', 'log', 'modified_huber', 'perceptron', 'huber',
    # 'epsilon_insensitive']
    losses = ['hinge', 'log', 'huber']
    penalties = ['l1', 'l2']
    # penalties = ['l1']

    predictions = []
    for loss in losses:
        for penalty in penalties:
            predictions.append(sgd_classify_and_score(loss, penalty))

    prediction = combine_predictions(predictions)
    return prediction


def feature_selection(data, target, keep_cols=[], short_circuit=False):
    def get_keep_features():
        if short_circuit:
            return np.repeat([True], data.shape[1])
        clf = SGDClassifier(loss='hinge', penalty='l1', n_iter=10, n_jobs=2, random_state=8675309, shuffle=True, class_weight="auto")
        clf.fit(data, target)
        return clf.coef_[0, :] != 0

    keep_features = Param.f("keep_features", get_keep_features)
    keep_features[keep_cols] = True
    """ get the new indices of keep_cols """
    kept_cols = keep_features.cumsum()[keep_cols] - 1
    return data[:, keep_features], kept_cols


def tempfile(delete=False):
    """Creates temporary file.

    Parameters
    ----------
    delete : boolean, optional, default: False
             Whether or not the temporary file is deleted immediately when closed.

    Returns
    -------
    temporary_file : A named temporary file with name attribute.
    """
    from tempfile import NamedTemporaryFile
    return NamedTemporaryFile(delete=delete)
