"""
Autism Detection: Domain Adaptation for Multi-Site Neuroimaging Data Analysis

Reference:
[1] Cameron Craddock, Yassine Benhajali, Carlton Chu, Francois Chouinard, Alan Evans, András Jakab, Budhachandra Singh Khundrakpam, John David Lewis, Qingyang Li, Michael Milham, Chaogan Yan, Pierre Bellec (2013). The Neuro Bureau Preprocessing Initiative: open sharing of preprocessed neuroimaging data and derivatives. In Neuroinformatics 2013, Stockholm, Sweden.

[2] Abraham, A., Pedregosa, F., Eickenberg, M., Gervais, P., Mueller, A., Kossaifi, J., ... & Varoquaux, G. (2014). Machine learning for neuroimaging with scikit-learn. Frontiers in neuroinformatics, 14.

[3] Zhou, S., Li, W., Cox, C.R., & Lu, H. (2020). Side Information Dependence as a Regularizer for Analyzing Human Brain Conditions across Cognitive Experiments. in AAAI 2020, New York, USA. https://ojs.aaai.org//index.php/AAAI/article/view/6179

[4] Zhou, S. (2022). Interpretable Domain-Aware Learning for Neuroimage Classification (Doctoral dissertation, University of Sheffield). https://etheses.whiterose.ac.uk/31044/1/PhD_thesis_ShuoZhou_170272834.pdf
"""
import argparse
import os

import numpy as np
import pandas as pd
from config import get_cfg_defaults
from nilearn.connectome import ConnectivityMeasure
from nilearn.datasets import fetch_abide_pcp
from sklearn.linear_model import RidgeClassifier

import kale.utils.seed as seed
from kale.evaluate import cross_validation
from kale.pipeline.multi_domain_adapter import CoIRLS


def arg_parse():
    parser = argparse.ArgumentParser(
        description="Autism Detection: Domain Adaptation for Multi-Site Neuroimaging Data Analysis"
    )
    parser.add_argument("--cfg", required=True, help="path to config file", type=str)
    args = parser.parse_args()
    return args


def main():
    args = arg_parse()

    # ---- Set up configs ----
    cfg = get_cfg_defaults()
    cfg.merge_from_file(args.cfg)
    cfg.freeze()
    seed.set_seed(cfg.SOLVER.SEED)

    # ---- Fetch ABIDE fMRI timeseries ----
    fetch_abide_pcp(
        data_dir=cfg.DATASET.ROOT,
        pipeline=cfg.DATASET.PIPELINE,
        band_pass_filtering=True,
        global_signal_regression=False,
        derivatives=cfg.DATASET.ATLAS,
        quality_checked=False,
        SITE_ID=cfg.DATASET.SITE_IDS,
        verbose=1,
    )

    # ---- Read Phenotypic data ----
    pheno_file = os.path.join(cfg.DATASET.ROOT, "ABIDE_pcp/Phenotypic_V1_0b_preprocessed1.csv")
    pheno_info = pd.read_csv(pheno_file, index_col=0)

    # ---- Read timeseries from files ----
    data_dir = os.path.join(cfg.DATASET.ROOT, "ABIDE_pcp/%s/filt_noglobal" % cfg.DATASET.PIPELINE)
    use_idx = []
    time_series = []
    for i in pheno_info.index:
        data_file_name = "%s_%s.1D" % (pheno_info.loc[i, "FILE_ID"], cfg.DATASET.ATLAS)
        data_path = os.path.join(data_dir, data_file_name)
        if os.path.exists(data_path):
            time_series.append(np.loadtxt(data_path, skiprows=0))
            use_idx.append(i)

    # ---- Use "DX_GROUP" (autism vs control) as labels, and "SITE_ID" as covariates ----
    pheno = pheno_info.loc[use_idx, ["SITE_ID", "DX_GROUP"]].reset_index(drop=True)

    # ---- Extracting Brain Networks Features ----
    correlation_measure = ConnectivityMeasure(kind="correlation", vectorize=True)
    brain_networks = correlation_measure.fit_transform(time_series)

    # ---- Machine Learning for Multi-site Data ----
    print("Baseline Model")
    estimator = RidgeClassifier()
    results = cross_validation.leave_one_group_out(
        brain_networks, pheno["DX_GROUP"].values, pheno["SITE_ID"].values, estimator
    )
    print(pd.DataFrame.from_dict(results))

    print("Domain Adaptation")
    estimator = CoIRLS(kernel=cfg.MODEL.KERNEL, lambda_=cfg.MODEL.LAMBDA_, alpha=cfg.MODEL.ALPHA)
    results = cross_validation.leave_one_group_out(
        brain_networks, pheno["DX_GROUP"].values, pheno["SITE_ID"].values, estimator, domain_adaptation=True
    )
    print(pd.DataFrame.from_dict(results))


if __name__ == "__main__":
    main()
