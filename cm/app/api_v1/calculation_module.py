import os
import sys
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)
from ..helper import generate_output_file_tif
from ..helper import generate_output_file_shp
from ..helper import generate_output_file_csv
from ..helper import create_zip_shapefiles
import my_calculation_module_directory.CM.CM_TUW23.run_cm as CM23
from my_calculation_module_directory.CM.CM_TUW0.rem_mk_dir import rm_file
from ..constant import CM_NAME


def calculation(output_directory, inputs_raster_selection, inputs_parameter_selection):
    '''
    def calculation()
    inputs:
        investment_start_year: year the investment starts e.g. 2018.
        investment_last_year: year the investment starts e.g. 2030.
        depreciation_time: depreciation time in years e.g. 25.
        accumulated_energy_saving: accumulated energy saving at the end of investment period [0:1].
        dh_connection_rate_first_year: share of demand covered by DH to the total demand in DH areas in the first year of investment [0:1].
        dh_connection_rate_last_year: share of demand covered by DH to the total demand in DH areas in the last year of investment [0:1].
        interest_rate: interest rate [0:100] in percent.
        grid_cost_ceiling: The cost in EUR/MWh that should not be exceeded.
        c1: the construction cost constant (EUR/m); default values for inner city area, outer city area and park areas are are 292.38, 218.78, 154.37 EUR/m, respectively.
        c2: the construction cost coefficient (EUR/m2); default values for inner city area, outer city area and park areas are are 2067.13, 1763.5, 1408.76 EUR/m2, respectively.
        full_load_hours: full load hours require for calculating the right pipe dimension, by default it is set to 3000.
        in_raster_gfa: gross floor area map for the selected zone.
        in_raster_hdm: heat density map for the selected zone.

    Outputs:
        out_raster_maxDHdem: max demand should be covered by DH during the investment period [MWh],
        out_raster_invest_Euro: distribution grid investment [EUR/MWh],
        out_raster_hdm_last_year: heat density map at the end of investment period,
        out_raster_dist_pipe_length: distribution grid pipeline length [m/m2],
        out_raster_coh_area_bool: shows both economic and non-economic coherent areas,
        out_raster_hdm_in_dh_reg_last_year: heat densities in the last year of investment within the coherent areas,
        out_raster_labels,
        out_shp_prelabel,
        out_shp_label,
        out_csv_solution.
    '''
    # input parameters
    investment_start_year = int(inputs_parameter_selection["investment_start_year"])
    investment_last_year = int(inputs_parameter_selection["investment_last_year"])
    depreciation_time = int(inputs_parameter_selection["depreciation_time"])
    accumulated_energy_saving = float(inputs_parameter_selection["accumulated_energy_saving"])
    dh_connection_rate_first_year = float(inputs_parameter_selection["dh_connection_rate_first_year"])
    dh_connection_rate_last_year = float(inputs_parameter_selection["dh_connection_rate_last_year"])
    interest_rate = float(inputs_parameter_selection["interest_rate"])/100.0
    grid_cost_ceiling = float(inputs_parameter_selection["grid_cost_ceiling"])
    c1 = float(inputs_parameter_selection["c1"])
    c2 = float(inputs_parameter_selection["c2"])
    full_load_hours = int(inputs_parameter_selection["full_load_hours"])
    mip_gap = 0.01*float(inputs_parameter_selection["mip_gap"])

    
    # input raster layers: (gfa:= gross floor area; hdm:= heat density map)
    in_raster_gfa = inputs_raster_selection["gross_floor_area"]
    in_raster_hdm = inputs_raster_selection["heat"]
    
    # output raster layers
    out_raster_maxDHdem = generate_output_file_tif(output_directory)
    out_raster_economic_maxDHdem = generate_output_file_tif(output_directory)
    out_raster_invest_Euro = generate_output_file_tif(output_directory)
    out_raster_hdm_last_year = generate_output_file_tif(output_directory)
    out_raster_dist_pipe_length = generate_output_file_tif(output_directory)
    out_raster_coh_area_bool = generate_output_file_tif(output_directory)
    out_raster_labels = generate_output_file_tif(output_directory)
    
    # output shapefiles
    out_shp_prelabel = generate_output_file_shp(output_directory)
    out_shp_label = generate_output_file_shp(output_directory)
    out_shp_edges = generate_output_file_shp(output_directory)
    out_shp_nodes = generate_output_file_shp(output_directory)

    # output csv files
    out_csv_solution = generate_output_file_csv(output_directory)

    output_summary, opt_term_cond, edge_list = CM23.main(
            investment_start_year,
            investment_last_year,
            depreciation_time,
            accumulated_energy_saving,
            dh_connection_rate_first_year,
            dh_connection_rate_last_year,
            interest_rate,
            grid_cost_ceiling,
            c1,
            c2,
            full_load_hours,
            mip_gap,
            in_raster_gfa,
            in_raster_hdm,
            out_raster_maxDHdem,
            out_raster_economic_maxDHdem,
            out_raster_invest_Euro,
            out_raster_hdm_last_year,
            out_raster_dist_pipe_length,
            out_raster_coh_area_bool,
            out_raster_labels,
            out_shp_prelabel,
            out_shp_label,
            out_shp_edges,
            out_shp_nodes,
            out_csv_solution,
            output_directory
            )
    
    rm_file(out_raster_maxDHdem, out_raster_maxDHdem[:-4] + ".tfw",
            out_raster_invest_Euro, out_raster_invest_Euro[:-4] + ".tfw",
            out_raster_dist_pipe_length, out_raster_dist_pipe_length[:-4] + ".tfw",
            out_raster_coh_area_bool, out_raster_coh_area_bool[:-4] + ".tfw",
            out_raster_labels, out_raster_labels[:-4] + ".tfw")
    result = dict()

    if opt_term_cond==True:
        out_shp_label = create_zip_shapefiles(output_directory, out_shp_label)
        result['name'] = CM_NAME
        result["raster_layers"]=[
              {"name": "heat demand density in the last year of the investment","path": out_raster_hdm_last_year, "type": "heat"},
              {"name": "heat demand covered by DH in the last year of the investment","path": out_raster_economic_maxDHdem, "type": "heat"}
              ]
        if len(edge_list) > 0:
            out_shp_edges = create_zip_shapefiles(output_directory, out_shp_edges)
            result["vector_layers"]=[
                 {"name": "Coherent areas (economic and non-economic) shapefile", "path": out_shp_label, "type": "custom",
                      "symbology": [
                              {"red":222, "green":45, "blue":38, "opacity":0.7, "value":" No", "label":"Not Economic"},
                              {"red": 44, "green":162, "blue": 95, "opacity":0.7, "value":" Yes", "label":"Economic"}
                              ]},
                              
                 {"name": "Transmission lines shapefile","path": out_shp_edges},
                  ]
        else:
            result["vector_layers"]=[
                 {"name": "Coherent areas (economic and non-economic) shapefile", "path": out_shp_label, "type": "custom",
                      "symbology": [
                              {"red":222, "green":45, "blue":38, "opacity":0.7, "value":" No", "label":"Not Economic"},
                              {"red": 44, "green":162, "blue": 95, "opacity":0.7, "value":" Yes", "label":"Economic"}
                              ]}]
        result["tabular"]=[{"name": "Summary of results","path": out_csv_solution}]

    horizon = investment_last_year - investment_start_year + 1
    if horizon > depreciation_time:
        output_summary = output_summary + [{"unit": "-", "name": "Warning: Study horizon is longer than depreciation time. The calculation was done only till the end of depreciation time!", "value": 0.0}]
    result['indicator'] = output_summary
    return result
