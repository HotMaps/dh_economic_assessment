import os
import sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.
                                                       abspath(__file__))))
if path not in sys.path:
    sys.path.append(path)


def summary(covered_demand, dist_inv, dist_spec_cost, trans_inv,
            trans_spec_cost, trans_line_length, dist_pipe_length, heat_dem_1st,
            heat_dem_last, n_coh_areas, n_coh_areas_selected, term_cond, numLabels):
    if numLabels < 1:
        summary = [{"unit": "-", "name": "No coherent area for given input parameters found!", "value": 0.0}]
    elif numLabels > 70:
        summary = [{"unit": "-", "name": "Too many coherent areas. consider to change input parameters!", "value": 0.0}]
    else:
        if term_cond=="aborted":
            summary = [{"unit": "-", "name": "For given input parameters, the optimization time limit was reached with no result. Modify your inputs or your selection and run again.", "value": 0.0}]
        else:
            summary = [{"unit": "MWh", "name": "Total demand in selected region in the first year of investment", "value": float(round(heat_dem_1st, 2))},
                       {"unit": "MWh", "name": "Total demand in selected region in the last year of investment", "value": float(round(heat_dem_last, 2))},
                       {"unit": "MWh", "name": "Maximum potential of DH system through the investment period", "value": float(round(covered_demand, 2))},
                       {"unit": "EUR/MWh", "name": "Energetic specific DH grid costs", "value": float(round(dist_spec_cost + trans_spec_cost, 2))},
                       {"unit": "EUR/MWh", "name": "Energetic specific DH distribution grid costs", "value": float(round(dist_spec_cost, 2))},
                       {"unit": "EUR/MWh", "name": "Energetic specific DH transmission grid costs", "value": float(round(trans_spec_cost, 2))},
                       {"unit": "EUR/m", "name": "Specific DH distribution grid costs per meter", "value": float(round(dist_inv/(dist_pipe_length*1000 + 1), 2))},
                       {"unit": "EUR/m", "name": "Specific DH transmission grid costs per meter", "value": float(round(trans_inv/(trans_line_length*1000 + 1), 2))},
                       {"unit": "EUR/yr", "name": "Total grid costs - annuity", "value": float(round(dist_inv + trans_inv, 2))},
                       {"unit": "EUR/yr", "name": "Total distribution grid costs - annuity", "value": float(round(dist_inv, 2))},
                       {"unit": "EUR/yr", "name": "Total transmission grid costs - annuity", "value": float(round(trans_inv, 2))},
                       {"unit": "km", "name": "Total distribution grid trench length", "value": float(round(dist_pipe_length, 2))},
                       {"unit": "km", "name": "Total transmission grid trench length", "value": float(round(trans_line_length, 2))},
                       {"unit": "", "name": "Total number of coherent areas", "value": float(round(n_coh_areas, 2))},
                       {"unit": "", "name": "Number of economic coherent areas", "value": float(round(n_coh_areas_selected, 2))}]
    return summary
