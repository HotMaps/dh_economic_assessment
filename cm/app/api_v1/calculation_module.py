import os
import logging
import numpy as np
import pandas as pd
from my_calculation_module_directory.CM.CM_TUW0.rem_mk_dir import rm_mk_dir
from my_calculation_module_directory.CM.CM_TUW40.f1_main_call import main
from my_calculation_module_directory.CM.CM_TUW40.f4_results_summary import summary
from initialize import Param, Out_File_Path


def logfile(P, OFP):
    logging_text = "\n\n"
    P_attr_dict = vars(P)
    col_width = 5 + max(len(key) for key in P_attr_dict.keys())
    for key in P_attr_dict.keys():
        logging_text = logging_text + "".join(key.ljust(col_width) + str(P_attr_dict[key]).ljust(col_width) + '\n')
    with open(OFP.logfile, 'w') as f:
        f.write(logging_text)


def unify_excels(output_directory):
    init_df = True
    for root, dirs, files in os.walk(output_directory):
        for file in files:
            if "summary.csv" == file:
                f = os.path.join(root, "summary.csv")
                tmp_df = pd.read_csv(f)
                if init_df:
                    df = tmp_df.copy()
                    init_df = False
                else:
                    df = df.append(tmp_df, ignore_index=True)
    out_xlsx = os.path.join(output_directory, 'summary_all.xlsx')
    df.to_excel(out_xlsx, index=False)


def calculation(output_directory, inputs_raster_selection, inputs_parameter_selection):
    '''
        def calculation()
        inputs:


        Outputs:

    '''
    in_raster_hdm = inputs_raster_selection["heat"]
    in_raster_gfa = inputs_raster_selection["gross_floor_area"]
    p = Param(inputs_parameter_selection)
    if not os.path.isdir(output_directory) or not os.path.exists(output_directory):
        raise NotADirectoryError(f"Directory not created : {output_directory}")
    else:
        logging.info(msg=f"Dir created : {output_directory}")
    OFP = Out_File_Path(output_directory, in_raster_hdm, in_raster_gfa, inputs_parameter_selection)
    rm_mk_dir(OFP.dstDir)
    logfile(p, OFP)
    main(p, OFP)
    result_dict = summary(p, OFP)


if __name__ == "__main__":
    output_directory = r"C:\Users\Mostafa\git\dh_economic_assessment\cm\tests\data\tmp"
    inputs_raster_selection = {
        'heat': r"C:\Users\Mostafa\git\dh_economic_assessment\cm\tests\data\hdm_Wien.tif",
        'gross_floor_area': r"C:\Users\Mostafa\git\dh_economic_assessment\cm\tests\data\gfa_Wien.tif"
                               }
    inputs_parameter_selection = {
        'country': 'AT',
        'pipe_length_per_year': np.inf,
        'scenario': 'test',
        'cost_ceiling': 22,
        # pixel threshold may not be changed. 20 is the correct value.
        'pix_threshold': 20,
        'DH_threshold': 5,
        'total_investment_annuity': np.inf,
        'investment_increasing_factor': 1,
        'start_year': 2020,
        'last_year': 2050,
        'ms_2020': 35,
        'ms_2050': 50,
        'depreciation_period': 30,
        'interest': 0.03,
        "use_default_cost_factors": True,
        'max_total_allowed_pipe_length': 20000,
    }
    calculation(output_directory, inputs_raster_selection, inputs_parameter_selection)