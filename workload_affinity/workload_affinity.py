import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

FILE = r"\\shwdewajod1018\skx-2s\Summary\cores_2015_stream_911\Specjbb2015_Stream_SKX6.xlsx"
INDEX = ["hp_instance", "lp_instance", "hp_llc", "lp_llc", "hp_workload", "lp_workload", "hp_mba", "lp_mba"]

def excel2df(file, i):
    df = pd.read_excel(file, header=0, index_col=0, sheetname="raw").transpose().set_index(i).astype('float64')
    return df

def get_corr(A, B):
    corr = np.corrcoef(A, B)[0][1]
    return corr

def df_corrs(df, keys, result_key):
    output = {}
    for i in keys:
        if i in df.columns:
            c = get_corr(df[i], df[result_key])
            output[i] = c
        else:
            continue
    return output

def get_pca(df, components = 1):
    clean_df = df.replace([np.inf, -np.inf, np.nan], 0)
    m = clean_df.as_matrix().astype(np.float64)
    pca = PCA(n_components=components)
    pca.fit(m)
    data = pca.components_[0]
    return data

def get_cos(A, B):
    num = float(np.dot(A.T, B))
    denom = np.linalg.norm(A) * np.linalg.norm(B)
    cos = num / denom
    sim = 0.5 + 0.5 * cos
    return sim

def collaborative_filt(input, types):
    output = {}
    for key in types.keys():
        sim = get_cos(input ,types[key])
        output[key] = sim
    sorted_output = sorted(output.iteritems(), key=lambda d: abs(d[1]), reverse=True)
    return sorted_output

if __name__ == "__main__":
    types = {}
    # read data
    data = excel2df(FILE, INDEX)
    # training data
    training_data = data.query("hp_instance==24")
    # test data
    test_data = data.query("hp_instance==8")

    # get training data workload type from corr of performance score and LLC/MB
    corr_dic = df_corrs(training_data, ["_LP_MB_MEAN", "_LP_LLC_MEAN"], "score")
    dic_sort = sorted(corr_dic.iteritems(), key=lambda d: abs(d[1]), reverse=True)
    # get training data PCA result of metrics
    train_pca = get_pca(training_data)
    types[dic_sort[0][0]] = train_pca

    #get test_data pca
    test_pca = get_pca(test_data)

    # use collaborative filter to get resource affinity of test data
    print collaborative_filt(test_pca, types)

