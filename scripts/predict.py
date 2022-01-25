import torch
from torch.utils.data import TensorDataset, DataLoader

import numpy  as np
import pandas as pd

import math
from .Discriminator import ensembleNet, evsNet


def predict(args):
    feature_path= args.input
    cancervar   = args.cancervar_path
    method      = args.method
    device      = args.device
    output_path = args.output
    model_path  = args.config

    feature_dat = pd.read_csv(feature_path, header=None, index_col=0,sep="\t")
    features    = feature_dat.values


    if method == "ensemble":
        disNet = ensembleNet().to(device)
        disNet.load_state_dict( torch.load( model_path, map_location=torch.device(device)  )  )

    else:
        disNet = evsNet().to(device)
        disNet.load_state_dict( torch.load( model_path, map_location=torch.device(device)  )  )

    validDataset = TensorDataset(torch.Tensor(features[:, np.newaxis, :]))
    validLoader  = DataLoader(dataset=validDataset, batch_size = 1000, shuffle=False)
    
    output_lst = []

    disNet.eval()
    with torch.no_grad():
        for testdata in validLoader:
            data = testdata[0]
            data = data.to(device)
            _, output = disNet(data)
            softmax2_score = [ math.exp(i[1]) / ( math.exp(i[0]) + math.exp(i[1]) ) for i in output.cpu().numpy() ]
            softmax2_score2 = ["%.4f" % elem for elem in softmax2_score]
            output_lst += softmax2_score2

    feature_dat["%s_score" % method] = output_lst

    cancervar_dat = pd.read_csv(cancervar, sep = "\t")
    cancervar_dat['new_index'] = cancervar_dat.apply(lambda x: 'row_{%s}_chr{%s}_start{%s}_end{%s}_ref{%s}_alt{%s}' \
        % (x.name, x['#Chr'], x['Start'], x["End"], x['Ref'], x['Alt']), axis = 1)
    cancervar_dat.set_index('new_index', inplace=True)
    
    output = pd.concat([ cancervar_dat, feature_dat[["%s_score" % method]].rename_axis('new_index') ], axis=1)
    output.to_csv(output_path, index=None, na_rep = ".",sep="\t")

    return 1
