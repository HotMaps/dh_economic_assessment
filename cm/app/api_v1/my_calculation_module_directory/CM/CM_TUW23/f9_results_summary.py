import os
import sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.
                                                       abspath(__file__))))
if path not in sys.path:
    sys.path.append(path)


def summary(covered_demand, dist_inv, dist_spec_cost, trans_inv,
            trans_spec_cost, trans_line_length, dist_pipe_length, heat_dem_1st,
            heat_dem_last, n_coh_areas, n_coh_areas_selected):
    
    summary = [{"unit": "MWh", "name": "Total demand in selected region in the first year of investment", "value": float(heat_dem_1st)},
               {"unit": "MWh", "name": "Total demand in selected region in the last year of investment", "value": float(heat_dem_last)},
               {"unit": "MWh", "name": "Maximum potential of DH system through the investment period", "value": float(covered_demand)},
               {"unit": "EUR/MWh", "name": "Energetic specific DH grid costs", "value": float(dist_spec_cost + trans_spec_cost)},
               {"unit": "EUR/MWh", "name": "Energetic specific DH distribution grid costs", "value": float(dist_spec_cost)},
               {"unit": "EUR/MWh", "name": "Energetic specific DH transmission grid costs", "value": float(trans_spec_cost)},
               {"unit": "EUR/m", "name": "Specific DH distribution grid costs per meter", "value": float(dist_inv/(dist_pipe_length*1000 + 1))},
               {"unit": "EUR/m", "name": "Specific DH transmission grid costs per meter", "value": float(trans_inv/(trans_line_length*1000 + 1))},
               {"unit": "EUR", "name": "Total grid costs - annuity", "value": float(dist_inv + trans_inv)},
               {"unit": "EUR", "name": "Total distribution grid costs - annuity", "value": float(dist_inv)},
               {"unit": "EUR", "name": "Total transmission grid costs - annuity", "value": float(trans_inv)},
               {"unit": "km", "name": "Total distribution grid trench length", "value": float(dist_pipe_length)},
               {"unit": "km", "name": "Total transmission grid trench length", "value": float(trans_line_length)},
               {"unit": "", "name": "Total number of coherent areas", "value": float(n_coh_areas)},
               {"unit": "", "name": "Number of economic coherent areas", "value": float(n_coh_areas_selected)}]
    return summary
