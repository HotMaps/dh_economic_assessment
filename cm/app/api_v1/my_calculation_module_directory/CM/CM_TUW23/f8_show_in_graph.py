import os
import sys
from osgeo import osr
import networkx as nx
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.
                                                       abspath(__file__))))
if path not in sys.path:
    sys.path.append(path)


def edge_representation(row_from_label, col_from_label, row_to_label,
                        col_to_label, distance_matrix, node_label_list,
                        edge_list, gt, out_shp_edges, out_shp_nodes, outDir,
                        epsg=3035):
    G = nx.Graph()
    x0, y0 , w , h = gt[0], gt[3], gt[1], gt[5]
    X0 = x0 + w/2
    Y0 = y0 + h/2
    for k in range(edge_list.shape[0]):
        s, t, edge_weight = edge_list[k, :]
        s, t = int(s), int(t)
        py0_ind, px0_ind = row_from_label[s, t], col_from_label[s, t]
        py1_ind, px1_ind = row_to_label[s, t], col_to_label[s, t]
        px0, py0 = X0 + 100 * px0_ind, Y0 - 100 * py0_ind
        px1, py1 = X0 + 100 * px1_ind, Y0 - 100 * py1_ind
        # G.add_edge((px0, py0), (px1, py1), weight=distance_matrix[s, t])
        G.add_edge((px0, py0), (px1, py1), weight=edge_weight)
    nx.write_shp(G, outDir)
    spatialRef = osr.SpatialReference()
    spatialRef.ImportFromEPSG(epsg)
    spatialRef.MorphToESRI()
    for item in ['nodes', 'edges']:
        prj_file = outDir + os.sep + item + '.prj'
        with open(prj_file, 'w') as file:
            file.write(spatialRef.ExportToWkt())
    G = None
    for filename in os.listdir(outDir):
        if filename.startswith("edges"):
            os.rename(outDir + os.sep + filename, outDir + os.sep + os.path.splitext(os.path.basename(out_shp_edges))[0] + os.path.splitext(filename)[1])
        if filename.startswith("nodes"):
            os.rename(outDir + os.sep + filename, outDir + os.sep + os.path.splitext(os.path.basename(out_shp_nodes))[0] + os.path.splitext(filename)[1])
