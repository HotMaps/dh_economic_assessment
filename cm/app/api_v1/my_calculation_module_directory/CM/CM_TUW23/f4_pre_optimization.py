import os
import sys
import numpy as np
import pandas as pd
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.
                                                       abspath(__file__))))
if path not in sys.path:
    sys.path.append(path)
from CM.CM_TUW1.read_raster import raster_array
from CM.CM_TUW23.f5_distance_calculation import feature_dist
from CM.CM_TUW23.f6_optimization import optimize_dist
from CM.CM_TUW23.f7_polygonize import polygonize as poly
from CM.CM_TUW23.f8_show_in_graph import edge_representation


def pre_opt(depreciation_time, interest_rate, grid_cost_ceiling,
            trans_line_cap_cost, full_load_hours, in_raster_hdm,
            out_raster_coh_area_bool, out_raster_hdm_last_year,
            out_raster_dist_pipe_length, out_raster_maxDHdem,
            out_raster_labels, out_raster_invest_Euro, out_shp_prelabel,
            out_shp_label, out_shp_edges, out_shp_nodes, out_csv_solution,
            output_directory, polygonize_region=False):
    hdm_arr, geoTrans = raster_array(out_raster_hdm_last_year, return_gt=True)
    labels = raster_array(out_raster_labels, 'int16')
    nr_coherent = np.max(labels)
    labels_copy = np.copy(labels)
    distance_matrix, row_from_label, col_from_label, \
        row_to_label, col_to_label = feature_dist(labels)

    total_pipe_length_arr = raster_array(out_raster_dist_pipe_length)
    hdm_1st_arr = raster_array(in_raster_hdm)
    dist_invest_arr = raster_array(out_raster_invest_Euro)
    maxDHdem_arr = raster_array(out_raster_maxDHdem)
    # prepare dataframe for final answers
    heat_dem_coh_1st = np.zeros((nr_coherent))
    heat_dem_coh_last = np.zeros((nr_coherent))
    heat_dem_spec_area = np.zeros((nr_coherent))
    dist_pipe_len = np.zeros((nr_coherent))
    q = np.zeros((nr_coherent))
    q_inv = np.zeros((nr_coherent))
    q_spec_cost = np.zeros((nr_coherent))
    area_coh_area = np.zeros((nr_coherent))
    for i in range(1, nr_coherent+1):
        j = i-1
        temp = labels_copy == i
        # in hectare
        area_coh_area[j] = np.sum(temp)
        heat_dem_coh_1st[j] = np.sum(hdm_1st_arr[temp])
        heat_dem_coh_last[j] = np.sum(hdm_arr[temp])
        # pipe length raster is in m/m2 and for each pixel needs a factor 10000
        # for meter and factor 1e-3 for km. Overal factor 10 to get it in km
        dist_pipe_len[j] = np.sum(total_pipe_length_arr[temp])*10
        q[j] = np.sum(maxDHdem_arr[temp])
        q_inv[j] = np.sum(dist_invest_arr[temp])
        q_spec_cost[j] = q_inv[j] / q[j]
        # MWh/km2
        heat_dem_spec_area[j] = heat_dem_coh_last[j] / area_coh_area[j]
    df = pd.DataFrame({
                       'heat demand total 1st year [MWh]': heat_dem_coh_1st,
                       'heat demand total last year [MWh]': heat_dem_coh_last,
                       'max potential district heating through investment period [MWh]': q,
                       'specific heat demand total 1st year [MWh/ha]': heat_dem_spec_area,
                       'distribution line length [km]': dist_pipe_len,
                       'distribution costs - annualized [EUR]': q_inv,
                       'distribution costs [EUR/MWh]': q_spec_cost,
                       'area [ha]': area_coh_area
                       })
    '''
    Dimension DN Water flow m/s Capacity MW Cost EUR/m
    Reference: GIS based analysis of future district heating in Denmark
    Author: Steffan Nielsen, Bernd Moeller
    '''
    annuity_factor = (interest_rate*(1+interest_rate)**depreciation_time)/((1+interest_rate)**depreciation_time-1)
    tl_cost_copy = np.copy(trans_line_cap_cost)
    temp_q = np.copy(q)
    power_to_add = temp_q[temp_q/full_load_hours > 190]/full_load_hours
    for item in power_to_add:
        for i in range(1, 5):
            temp_price = i * item / 190 * 976
            tl_cost_copy = np.concatenate((tl_cost_copy, [[i * item, temp_price]]))
    tl_cost_copy = tl_cost_copy[tl_cost_copy[:, 0].argsort()]
    trans_line_cap_cost = np.copy(tl_cost_copy)

    # consideration of annuity factor
    trans_line_cap_cost[:, 1] = trans_line_cap_cost[:, 1] * annuity_factor
    cost_matrix = trans_line_cap_cost[:, 1]
    pow_range_matrix = trans_line_cap_cost[:, 0]
    term_cond, dh, edge_list = optimize_dist(grid_cost_ceiling, cost_matrix,
                                             pow_range_matrix, distance_matrix,
                                             q, q_spec_cost)

    grid_cost_header = 'Connected at %0.2f EUR/MWh' % grid_cost_ceiling
    df[grid_cost_header] = dh[:-6]
    df['label'] = df.index + 1
    headers = ['label', 'heat demand total 1st year [MWh]',
               'heat demand total last year [MWh]',
               'distribution costs [EUR/MWh]',
               'specific heat demand total 1st year [MWh/ha]',
               'distribution costs - annualized [EUR]', 'area [ha]',
               'distribution line length [km]', grid_cost_header]
    df = df[headers]

    df.to_csv(out_csv_solution)
    if polygonize_region and term_cond:
        economic_bool = dh[:-6]
        poly(heat_dem_coh_last, heat_dem_spec_area, q, q_spec_cost,
             economic_bool, area_coh_area, out_raster_coh_area_bool,
             out_raster_labels, out_shp_prelabel, out_shp_label)
    node_label_list = np.arange(1, nr_coherent+1) * dh[0: -6]
    if term_cond:
        if len(edge_list) > 0:
            edge_representation(row_from_label, col_from_label, row_to_label,
                                col_to_label, distance_matrix, node_label_list,
                                edge_list, geoTrans, out_shp_edges,
                                out_shp_nodes, output_directory)
    sum_dist_pipeline = np.sum(dist_pipe_len * dh[:-6])
    return dh[-6:], sum_dist_pipeline, np.sum(hdm_1st_arr), np.sum(hdm_arr), nr_coherent, np.sum(dh[:-6]), term_cond
