import os
import sys
import numpy as np
import networkx as nx
import pyomo.environ as en
from pyomo.opt import SolverFactory
from pyomo.opt import TerminationCondition, SolverStatus


path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.
                                                       abspath(__file__))))
if path not in sys.path:
    sys.path.append(path)


def optimize_dist(threshold, cost_matrix, pow_range_matrix, distance_matrix,
                  demand_coherent_area, dist_cost_coherent_area, mip_gap,
                  obj_case=1, full_load_hours=3000, max_pipe_length=3000,
                  logFile_path=None):
    # st = time.time()
    '''
    distance_matrix = np.round(distance_matrix[:7,:7])
    demand_coherent_area = np.round(demand_coherent_area[:7])
    dist_cost_coherent_area = dist_cost_coherent_area[:7]

    Number of coherent areas: n
    demand_coherent_area (n x 1) [MWh]: demand in each coherent area
    dist_cost_coherent_area (n x 1) [EUR]: distribution cost of each coherent
                                           area
    transmision_line_cost (n x n) [EUR/m]: constant value for the cost of
                                   transmission line
    '''
    max_cap = 1000 # range of x variables
    BigM = 10 ** 6
    if len(demand_coherent_area) == 0:
        term_cond = False
        dh = np.zeros(6)
        edge_list = []
        return term_cond, dh, np.array(edge_list)
    if len(demand_coherent_area) == 1:
        term_cond = True
        dh = np.zeros(7)
        dh[0] = 1
        covered_demand = demand_coherent_area
        dist_inv = demand_coherent_area * dist_cost_coherent_area
        dist_spec_cost = dist_inv/covered_demand
        trans_inv = 0
        trans_spec_cost = 0
        trans_line_length = 0
        dh[1: 7] = covered_demand, dist_inv, dist_spec_cost, trans_inv, \
                    trans_spec_cost, trans_line_length
        edge_list = []
        return term_cond, dh, np.array(edge_list)
    G = np.argmax(demand_coherent_area)
    G2 = np.argsort(demand_coherent_area)[-2]
    n = demand_coherent_area.shape[0]
    '''
    
    
    # cut to more distant areas
    # Keep only connections to the x closest Areas
    x = min(7.0, n-1)
    distance_matrix_orig = distance_matrix.copy()
    max_pipe_length2 = np.percentile(distance_matrix, (1 + x) / n
                                        * 100.0, axis=0)
    mask = (np.ones((n, 1), dtype="f4") * max_pipe_length2)
    NotCloseRegions = (distance_matrix > mask)
    # if distance_matrix[a, b] > mask and therefore, should be filtered.
    # accordingly, distance_matrix[b, a] should be filtered as well.
    Filter_NotCloseRegions = np.logical_and(NotCloseRegions, NotCloseRegions.T)

    # Assess which regions belong to Category Large Areas ( x Regions)
    x = min(10.0, n)
    min_energy_large_area = np.percentile(demand_coherent_area, (1 - x / n)
                                                            * 100, axis=0)
    is_large_area_vct = demand_coherent_area >= min_energy_large_area

    #Matrix: mxm Larger areas are true, others are false
    maskLA= (np.ones((n, 1), dtype="f4") * is_large_area_vct)
    # returns nxn matrix showing each coherent area is smaller than which ones
    maskIsSmallerA = ((np.ones((n, 1), dtype="f4") * demand_coherent_area)
                      < (np.ones((n, 1), dtype="f4") * demand_coherent_area).T)
    maskLA[maskIsSmallerA] = False

    # Store the distance of an Area (rows) to all larger Large Areas (in Columns)
    distance_matrix2 = distance_matrix_orig.copy()
    # assign a large distance (BigM) to those coherent areas that are not
    # LA (large area).
    distance_matrix2[maskLA == False] = BigM
    
    # assign a large distance (BigM) to distance from itself with an exception
    # of greatest coherent area (G).
    EYE = np.eye(distance_matrix.shape[0], dtype="f4") * BigM
    EYE[G, G] = 0
    EYE[G2, G2] = 0
    distance_matrix2 += EYE
    
    # Distance of Areas (in rows) to the second closest larger Large Area
    # but only if 
    distance2closest_LargeArea = np.zeros(n, dtype="f4")
    idx = np.argsort(distance_matrix2, axis=1)[:, :2]
    count__ = 0
    for i in range(n):

        dist2closest = distance_matrix_orig[i, idx[i, 0]]
        dist2_2ndclosest = distance_matrix_orig[i, idx[i, 1]]
        dist_1to2nd = distance_matrix_orig[idx[i, 1], idx[i, 0]]
        # if dist2closest=0, it means it is the largest area and the next
        # largest area is the closest large area!
        if dist2closest == 0:
            distance2closest_LargeArea[i] = dist2_2ndclosest
            count__ += 1
            continue
        if dist2_2ndclosest == 0:
            distance2closest_LargeArea[i] = dist2closest
            count__ += 1
            continue

        cos_ = ((dist2closest ** 2 + dist2_2ndclosest ** 2 - dist_1to2nd ** 2)/(2 * dist2closest * dist2_2ndclosest))

        if dist2_2ndclosest > dist_1to2nd:
            # add_2nd_largest = False
            distance2closest_LargeArea[i] = dist2closest
            continue
        elif cos_ <= -1 or cos_ >= 1:
            distance2closest_LargeArea[i] = dist2_2ndclosest
            count__ += 1
            continue
        else:
            arc_between = np.arccos(cos_) * 180 / np.pi

            if (arc_between < 20):
                # add_2nd_largest = False
                distance2closest_LargeArea[i] = dist2closest
            elif arc_between < (20 + 35 * (dist2_2ndclosest / dist2closest / 1.2 - 1)):
                # add_2nd_largest = False
                distance2closest_LargeArea[i] = dist2closest
            else:
                distance2closest_LargeArea[i] = dist2_2ndclosest
                count__ += 1
    # print("Allowed connection to 2nd most distant large area: %s" % count__)
    # Look for closest Large Areas
    m2 = (distance_matrix2 <= (np.ones((n, 1), dtype="f4") * distance2closest_LargeArea).T)
    # Build Filter Matrix: True if connection to close Larger Area
    # Therefore logical_or
    Filter_CloseLargeAreas = np.logical_or(m2, m2.T) 
    FilterNoConnection = np.logical_and(Filter_NotCloseRegions
                                        , Filter_CloseLargeAreas == False)
    distance_matrix[FilterNoConnection] = BigM
    # print(np.sum(np.logical_and(distance_matrix <= BigM, distance_matrix > 0)))
    fix_to_zero_index = np.argwhere(distance_matrix >= max_pipe_length)

    # print("Connections : %i" %(distance_matrix.size - fix_to_zero_index.shape[0] - n))    
    # np.savetxt('fix_to_zero_index.csv', fix_to_zero_index, delimiter=",")
    # distance_matrix3: Distance to a Large Area
    distance_matrix3 = distance_matrix.copy()
    distance_matrix3[maskLA==False] = BigM
    HasConnection2LargerArea_Vctr = np.zeros(n, dtype="int8")
    # HasConnection2LargerArea_Vctr == 1, if a short distance is available
    HasConnection2LargerArea_Vctr[np.min(distance_matrix3, axis=1) < max_pipe_length] = 1

    for i in range(10):
        # Built Matrix: For each Area (in Rows), specify if connected Area is 
        # is Connected to a Larger Large Area 
        # Loop to check if it can handle it forward to such a region
        HasConnection2LargerArea_Vctr_prev = HasConnection2LargerArea_Vctr.copy()

        HasConnection2LargArea_Mtrx = np.ones((n, 1), dtype="int8") * HasConnection2LargerArea_Vctr
        D = distance_matrix.copy()
        D[HasConnection2LargArea_Mtrx==False] = BigM
        HasConnection2LargerArea_Vctr[np.min(D, axis=1) < max_pipe_length] = 1
        if (np.sum(HasConnection2LargerArea_Vctr_prev) == np.sum(HasConnection2LargerArea_Vctr)):
            break
    ###########################################################################
    ###########################################################################
    AddConection = np.zeros((n, n)).astype(bool)
    ###########################################################################
    ###########################################################################
    if min(HasConnection2LargerArea_Vctr) == 0:
        # Some regions have no connection to a larger Large Region
        # print(HasConnection2LargerArea_Vctr)
        HasConnection2LargArea_Mtrx = np.ones((n, 1), dtype="int8") * HasConnection2LargerArea_Vctr
        distance_matrix3 = distance_matrix_orig.copy()
        distance_matrix3[HasConnection2LargArea_Mtrx==0] = BigM
        ClosestDistance2ConnectedArea = np.min(distance_matrix3, axis=1)
        AddConection = (distance_matrix_orig < (np.ones((n, 1), dtype="f4") * ClosestDistance2ConnectedArea * 1.15))
        # Remove Regions which are already connected
        AddConection[HasConnection2LargerArea_Vctr == 1, :] = False
        AddConection = np.maximum(AddConection, AddConection.T)
        AddConection[distance_matrix <= max_pipe_length] = False
        distance_matrix[AddConection] = distance_matrix_orig[AddConection]

    fix_to_zero_index = np.argwhere(np.logical_and(
                                    distance_matrix >= max_pipe_length
                                    , AddConection==False))
    # np.savetxt('AddConection.csv', AddConection, delimiter=",")
    # np.savetxt('distance_matrix_final.csv', distance_matrix, delimiter=",")
    # print("Connections after additional Connections: %i" %(distance_matrix.size - fix_to_zero_index.shape[0] - n))
    
    '''
    m = en.ConcreteModel()
    solver = SolverFactory('gurobi', solver_io='python')
    # the gap between the lower and upper objective bound
    solver.options["MIPGap"] = mip_gap
    # the relative difference between the primal and dual objective value
    solver.options["BarConvTol"] = 1e-1
    # set to 1 if you are interested in feasible solutions
    # set to 2 if no problem with finding good quality solution exist and you want to focus on optimality
    # set to 3 if the best objective bound is moving very slowly (or not at all), to focus on bound
    solver.options["MIPFocus"] = 3
    # memory used. the rest will be written in the hard drive.
    # solver.options["NodefileStart"] = 0.5
    # number of threads used by the solver
    # solver.options["Threads"] = 2
    solver.options["TimeLimit"] = 300

    # ##########################################################################
    # ########## Sets:
    # ##########################################################################
    m.index_row = en.RangeSet(0, n-1)
    m.index_col = en.RangeSet(0, n-1)

    # ##########################################################################
    # ########## Parameters:
    # ##########################################################################
    m.th = en.Param(m.index_row, initialize=threshold)
    m.cap_up = en.Param(initialize=np.sum(demand_coherent_area) -
                        demand_coherent_area[G])

    def demand(m, i):
        return demand_coherent_area[i]
    m.q = en.Param(m.index_row, initialize=demand)

    def distribution_cost(m, i):
        return dist_cost_coherent_area[i]
    m.dist_cost = en.Param(m.index_row, initialize=distribution_cost)

    def l_length(m, i, j):
        return distance_matrix[i, j]
    m.line_length = en.Param(m.index_row, m.index_col, initialize=l_length)

    # ##########################################################################
    # ########## Variables:
    # ##########################################################################
    m.q_bool = en.Var(m.index_row, domain=en.Binary, initialize=1)
    m.l_bool = en.Var(m.index_row, m.index_col, domain=en.Binary, initialize=0)
    m.line_capacity = en.Var(m.index_row, m.index_col,
                             domain=en.NonNegativeReals, bounds=(0, max_cap),
                             initialize=0)
    m.line_cost = en.Var(m.index_row, m.index_col, domain=en.NonNegativeReals,
                         initialize=0)
    # set the largest demand zone to be part of the result
    m.q_bool[G].fix(1)
    for i in m.index_row:
        m.l_bool[i, G].fix(0)
        m.l_bool[i, i].fix(0)
        m.line_capacity[i, G].fix(0)
        m.line_capacity[i, i].fix(0)
        
    for i in m.index_row:
        for j in m.index_col:
            if distance_matrix[i, j] > max_pipe_length:
                m.l_bool[i, j].fix(0)
                m.line_capacity[i, j].fix(0)
    '''
    for i in range(len(demand_coherent_area)):
        # Lowest transmission line capacity is 0.2 Mw. Intercept of the cost function
        # in the piecewise linear expresion is 242.87. It should be set to zero if the
        # capacity is less than 0.2 MW
        if demand_coherent_area[i]/full_load_hours < 0.2:
            for j in range(len(demand_coherent_area)):
                m.l_bool[i, j].fix(0)
                m.line_capacity[i, j].fix(0)
                m.l_bool[j, i].fix(0)
                m.line_capacity[j, i].fix(0)
    '''
    # ##########################################################################
    # ########## Constraints:
    # ##########################################################################

    def overall_cost_rule(m):
        return sum(m.line_cost[i, j] * m.line_length[i, j]
                   for i in m.index_row for j in m.index_col) <= \
                   sum(m.q_bool[i]*m.q[i]*(m.th[i]-m.dist_cost[i])
                       for i in m.index_row)
    m.overall_cost = en.Constraint(rule=overall_cost_rule)

    def max_edge_number_rule(m):
        return sum(m.l_bool[i, j] for i in m.index_row
                   for j in m.index_col) == sum(m.q_bool[i]
                                                for i in m.index_row) - 1
    m.max_edge_number = en.Constraint(rule=max_edge_number_rule)

    def edge_connectivity_rule(m, i):
        if i == G:
            # l_bool[x, G] are already fixed to zero
            return en.Constraint.Skip
        else:
            return m.q_bool[i] <= sum(m.l_bool[j, i] for j in m.index_row)
    m.edge_connectivity = en.Constraint(m.index_row,
                                        rule=edge_connectivity_rule)
#     m.edge_connectivity_0 = en.Constraint(expr=1 <= sum(m.l_bool[G, j]
#                                           for j in m.index_col))

    def edge_connectivity_2_rule(m, i, j):
        if i == G:
            return en.Constraint.Skip
        else:
            return m.l_bool[i, j] <= sum(m.l_bool[h, i]
                                         for h in m.index_row if h != j)
    m.edge_connectivity_2 = en.Constraint(m.index_row, m.index_col,
                                          rule=edge_connectivity_2_rule)

    def edge_connectivity_3_rule(m, i):
        if i == G:
            return en.Constraint.Skip
        else:
            return sum(m.l_bool[h, i] for h in m.index_row) <= 1
    m.edge_connectivity_3 = en.Constraint(m.index_row, rule=edge_connectivity_3_rule)

    def edge_active_rule(m, i, j):
        return 2*(m.l_bool[i, j] + m.l_bool[j, i]) <= m.q_bool[i] + m.q_bool[j]
    m.edge_active = en.Constraint(m.index_row, m.index_col,
                                  rule=edge_active_rule)

    def capacity_lower_bound_rule(m, i, j):
        return m.line_capacity[i, j] >= (m.l_bool[i, j]*m.q[j])/full_load_hours
    m.capacity_lower_bound = en.Constraint(m.index_row, m.index_col,
                                           rule=capacity_lower_bound_rule)

    def capacity_upper_bound_rule(m, i, j):
        return m.line_capacity[i, j] <= \
            (sum(m.q[h] for h in m.index_row if (h != G and h != i)) -
             sum(m.l_bool[h, i] * m.q[h]
                 for h in m.index_row if h != G))/full_load_hours
    m.capacity_upper_bound = en.Constraint(m.index_row, m.index_col,
                                           rule=capacity_upper_bound_rule)

    def force_cap_to_zero_rule(m, i, j):
        return m.line_capacity[i, j] - m.l_bool[i, j]*m.cap_up <= 0
    m.force_cap_to_zero = en.Constraint(m.index_row, m.index_col,
                                        rule=force_cap_to_zero_rule)
    '''
    def force_cap_to_zero_2_rule(m, i, j):
        return m.line_capacity[i, j] + 0.99 >= m.l_bool[i, j]
    m.force_cap_to_zero_2 = en.Constraint(m.index_row, m.index_col,
                                        rule=force_cap_to_zero_2_rule)
    '''
    def capacity_flow_rule(m, i):
        if i == G:
            return sum(m.line_capacity[G, h] for h in m.index_col) == \
                sum(m.q_bool[h]*m.q[h]
                    for h in m.index_row if h != G)/full_load_hours
        else:
            return sum(m.line_capacity[h, i] for h in m.index_row) - \
                sum(m.line_capacity[i, h] for h in m.index_col) == \
                m.q_bool[i]*m.q[i]/full_load_hours
    m.capacity_flow = en.Constraint(m.index_row, rule=capacity_flow_rule)

    def f(m, i, j, x):
        if x >= pow_range_matrix[0] and x < pow_range_matrix[1]:
            return x * (cost_matrix[1] - cost_matrix[0])/(pow_range_matrix[1] - pow_range_matrix[0])
        elif x >= pow_range_matrix[1] and x < pow_range_matrix[2]:
            return (x - pow_range_matrix[1]) * (cost_matrix[2] - cost_matrix[1])/(pow_range_matrix[2] - pow_range_matrix[1]) + cost_matrix[1]
        elif x >= pow_range_matrix[2] and x < pow_range_matrix[3]:
            return (x - pow_range_matrix[2]) * (cost_matrix[3] - cost_matrix[2])/(pow_range_matrix[3] - pow_range_matrix[2]) + cost_matrix[2]
        elif x >= pow_range_matrix[3] and x < pow_range_matrix[4]:
            return (x - pow_range_matrix[3]) * (cost_matrix[4] - cost_matrix[3])/(pow_range_matrix[4] - pow_range_matrix[3]) + cost_matrix[3]
        elif x >= pow_range_matrix[4] and x < pow_range_matrix[5]:
            return (x - pow_range_matrix[4]) * (cost_matrix[5] - cost_matrix[4])/(pow_range_matrix[5] - pow_range_matrix[4]) + cost_matrix[4]
        elif x >= pow_range_matrix[5] and x < pow_range_matrix[6]:
            return (x - pow_range_matrix[5]) * (cost_matrix[6] - cost_matrix[5])/(pow_range_matrix[6] - pow_range_matrix[5]) + cost_matrix[5]
        elif x >= pow_range_matrix[6] and x < pow_range_matrix[7]:
            return (x - pow_range_matrix[6]) * (cost_matrix[7] - cost_matrix[6])/(pow_range_matrix[7] - pow_range_matrix[6]) + cost_matrix[6]
        elif x >= pow_range_matrix[7] and x < pow_range_matrix[8]:
            return (x - pow_range_matrix[7]) * (cost_matrix[8] - cost_matrix[7])/(pow_range_matrix[8] - pow_range_matrix[7]) + cost_matrix[7]
        elif x >= pow_range_matrix[8] and x < pow_range_matrix[9]:
            return (x - pow_range_matrix[8]) * (cost_matrix[9] - cost_matrix[8])/(pow_range_matrix[9] - pow_range_matrix[8]) + cost_matrix[8]
        elif x >= pow_range_matrix[9] and x < pow_range_matrix[10]:
            return (x - pow_range_matrix[9]) * (cost_matrix[10] - cost_matrix[9])/(pow_range_matrix[10] - pow_range_matrix[9]) + cost_matrix[9]
        elif x >= pow_range_matrix[10] and x < pow_range_matrix[11]:
            return (x - pow_range_matrix[10]) * (cost_matrix[11] - cost_matrix[10])/(pow_range_matrix[11] - pow_range_matrix[10]) + cost_matrix[10]
        elif x >= pow_range_matrix[11] and x < pow_range_matrix[12]:
            return (x - pow_range_matrix[11]) * (cost_matrix[12] - cost_matrix[11])/(pow_range_matrix[12] - pow_range_matrix[11]) + cost_matrix[11]
        elif x >= pow_range_matrix[12] and x < pow_range_matrix[13]:
            return (x - pow_range_matrix[12]) * (cost_matrix[13] - cost_matrix[12])/(pow_range_matrix[13] - pow_range_matrix[12]) + cost_matrix[12]
        elif x >= pow_range_matrix[13] and x < pow_range_matrix[14]:
            return (x - pow_range_matrix[13]) * (cost_matrix[14] - cost_matrix[13])/(pow_range_matrix[14] - pow_range_matrix[13]) + cost_matrix[13]
        elif x >= pow_range_matrix[14] and x < pow_range_matrix[15]:
            return (x - pow_range_matrix[14]) * (cost_matrix[15] - cost_matrix[14])/(pow_range_matrix[15] - pow_range_matrix[14]) + cost_matrix[14]
        else: 
            return (x - pow_range_matrix[15]) * (cost_matrix[16] - cost_matrix[15])/(pow_range_matrix[16] - pow_range_matrix[15]) + cost_matrix[15]
    
    m.pw_con = en.Piecewise(m.index_row, m.index_col, m.line_cost, m.line_capacity,
                                pw_pts=list(pow_range_matrix), pw_constr_type='EQ', f_rule=f)
    
    def obj_rule_1(m):
        # OBJ1: Revenue-Oriented Prize Collecting
        return sum(m.th[i]*m.q_bool[i]*m.q[i] for i in m.index_row) - \
            sum(m.line_cost[i, j] * m.line_length[i, j]
                for i in m.index_row for j in m.index_col)

    def obj_rule_2(m):
        # OBJ2: Profit-Oriented Prize Collectiing
        return sum((m.th[i]-m.dist_cost[i])*m.q_bool[i]*m.q[i]
                   for i in m.index_row) - \
                   sum(m.line_cost[i, j] * m.line_length[i, j]
                       for i in m.index_row for j in m.index_col)
    if obj_case == 1:
        m.obj = en.Objective(rule=obj_rule_1, sense=en.maximize)
    elif obj_case == 2:
        m.obj = en.Objective(rule=obj_rule_2, sense=en.maximize)
    else:
        raise ValueError('Objective method is selected wrongly! Please enter '
                         '"1" for Revenue-Oriented Prize Collection or "2" '
                         'for Profit-Oriented Prize Collection')

    results = solver.solve(m, report_timing=False, tee=False, logfile="gurobi.log")
    print("Solver Termination: ", results.solver.termination_condition)
    print("Solver Status: ", results.solver.status)
    term_cond = results.solver.termination_condition == TerminationCondition.optimal
    if results.solver.status == SolverStatus.aborted:
        term_cond = "aborted"

    '''
    ##################
    # save variable values to a csv file
    var_names = [name(v) for v in m.component_objects(Var)]
    list_of_vars = [value(v[index]) for v in m.component_objects(Var) for index in v]
    df = pd.DataFrame()
    result_series = pd.Series(list_of_vars, index=var_names)
    result_series.to_csv(outCSV)
    if done:
        results.write()
        print('obejctive = ', value(m.obj))
    ###################
    '''
    edge_list = []
    dist_inv = 0
    trans_inv = 0
    covered_demand = 0
    trans_line_length = 0
    dh = np.zeros(n+6)
    for i in range(n):
        dh[i] = en.value(m.q_bool[i])
        covered_demand += demand_coherent_area[i] * en.value(m.q_bool[i])
        dist_inv += dh[i]*demand_coherent_area[i] * dist_cost_coherent_area[i]
    for i in range(n):
        for j in range(n):
            if en.value(m.l_bool[i, j]) > 0:
                trans_inv += en.value(m.line_cost[i, j]) * \
                                en.value(m.line_length[i, j])
                trans_line_length += en.value(m.line_length[i, j])
                edge_list.append([i, j, en.value(m.line_capacity[i, j])])
    '''
    for i in range(n):
        for j in range(n):
            if en.value(m.l_bool[i, j]) > 0:
                print(i, " , ", j, "\t capacity: ", en.value(m.line_capacity[i, j]), "\t line: ", en.value(m.l_bool[i, j]))
    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    for i in range(n):
        for j in range(n):
            if en.value(m.line_capacity[i, j]) > 0:
                print(i, " , ", j, "\t capacity: ", en.value(m.line_capacity[i, j]), "\t line: ", en.value(m.l_bool[i, j]))
    '''
    # meter to km
    trans_line_length /= 1000
    dist_spec_cost = dist_inv/covered_demand
    trans_spec_cost = trans_inv/covered_demand
    dh[n: n+6] = covered_demand, dist_inv, dist_spec_cost, trans_inv, \
        trans_spec_cost, trans_line_length
    return term_cond, dh, np.array(edge_list)
