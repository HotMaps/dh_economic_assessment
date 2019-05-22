import os
import sys
import numpy as np
from scipy.ndimage import measurements
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.
                                                       abspath(__file__))))
if path not in sys.path:
    sys.path.append(path)
from CM.CM_TUW0.rem_mk_dir import rm_file
from CM.CM_TUW1.read_raster import raster_array
import CM.CM_TUW4.district_heating_potential as DHP
from CM.CM_TUW19 import run_cm as CM19


def distribuition_costs(pixT, DH_threshold, dist_grid_cost,
                        out_raster_hdm_last_year, out_raster_maxDHdem,
                        out_raster_invest_Euro, out_raster_coh_area_bool,
                        out_raster_labels, struct=np.ones((3, 3))):
    rm_file(out_raster_coh_area_bool, out_raster_labels)
    invest_Euro_arr = raster_array(out_raster_invest_Euro)
    maxDHdem_arr = raster_array(out_raster_maxDHdem)
    heat_density_map_last_year, geo_transform = raster_array(out_raster_hdm_last_year, return_gt=True)
    rast_origin = geo_transform[0], geo_transform[3]
    coh_areas = np.zeros_like(maxDHdem_arr, 'int8')
    reg_filter = maxDHdem_arr.astype(bool).astype('int8')
    for pix_threshold in pixT:
        # calculate coherent regions with given thresholds and cut them to
        # LAU2 levels
        # DH_Regions: boolean array showing DH regions
        DH_Regions, gt = DHP.DHReg(heat_density_map_last_year, pix_threshold,
                                   DH_threshold, rast_origin)
        # multiplication with reg_filter required to follow out_raster_maxDHdem
        # pattern and separate connection of regions with pixels that have
        # value of zero in out_raster_maxDHdem
        result = DH_Regions.astype(int) * reg_filter
        labels, nr_coherent = measurements.label(result, structure=struct)
        if nr_coherent == 0:
            break
        for i in range(1, nr_coherent+1):
            temp = labels == i
            q = np.sum(maxDHdem_arr[temp])
            q_inv = np.sum(invest_Euro_arr[temp])
            q_spec_cost = q_inv / q
            if q_spec_cost <= dist_grid_cost and q >= DH_threshold:
                coh_areas[temp] = 1
                heat_density_map_last_year[temp] = 0
        labels = None 
        nr_coherent = None
    labels, numLabels = measurements.label(coh_areas, structure=struct)
    if numLabels == 0:
        raise ValueError('For the provided grid cost ceiling, no district '
                         'heating potential area can be realized!')
    if numLabels > 100:
        raise ValueError('For the given scenario, we found more than 100 '
                         'coherent areas. Please reduce the size of your '
                         'selection and run the scenario again!')
    CM19.main(out_raster_coh_area_bool, geo_transform, 'int8', coh_areas)
    CM19.main(out_raster_labels, geo_transform, "int16", labels)
