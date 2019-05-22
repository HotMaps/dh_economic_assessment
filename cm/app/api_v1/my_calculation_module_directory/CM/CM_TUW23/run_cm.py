import os
import sys
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.
                                                       abspath(__file__))))
if path not in sys.path:
    sys.path.append(path)
import CM.CM_TUW23.f0_main_call as f0


def main(investment_start_year, investment_last_year, depreciation_time,
         accumulated_energy_saving, dh_connection_rate_first_year,
         dh_connection_rate_last_year, interest_rate, grid_cost_ceiling,
         c1, c2, full_load_hours, in_raster_gfa, in_raster_hdm,
         out_raster_maxDHdem, out_raster_invest_Euro,
         out_raster_hdm_last_year, out_raster_dist_pipe_length,
         out_raster_coh_area_bool, out_raster_labels, out_shp_prelabel,
         out_shp_label,out_shp_edges, out_shp_nodes, out_csv_solution,
         output_directory):
    output_summary = f0.main(investment_start_year, investment_last_year,
                             depreciation_time, accumulated_energy_saving,
                             dh_connection_rate_first_year,
                             dh_connection_rate_last_year, interest_rate,
                             grid_cost_ceiling, c1, c2, full_load_hours,
                             in_raster_gfa, in_raster_hdm,
                             out_raster_maxDHdem, out_raster_invest_Euro,
                             out_raster_hdm_last_year,
                             out_raster_dist_pipe_length,
                             out_raster_coh_area_bool,
                             out_raster_labels, out_shp_prelabel,
                             out_shp_label, out_shp_edges, out_shp_nodes,
                             out_csv_solution, output_directory)
    return output_summary
