# -*- coding: utf-8 -*-
"""
Natural Language Generation
"""

# import sys
# sys.path.append("/home/xieyang/secondo/Algebras/SpatialNLQ")
import NLU
import sys


# 组装范围查询语句
def range_query(relation, place, tmp_operator):
    sql = "query " + relation['name'] + " feed filter [.GeoData " + tmp_operator + " " + place + "] consume;"
    return sql


# 组装最近邻查询语句
def nn_query(relation, place, num_neighbors):
    if(relation['GeoData'] == 'point'):
        sql = "query " + relation['name'] + " creatertree[GeoData] " + relation['name']\
            + " distancescan2 [" + place + ", " + num_neighbors + "] consume;"
    else:
        sql = "query " + relation['name'] + " creatertree[GeoData] " + relation['name']\
            + " distancescan3 [" + place + ", " + num_neighbors + "] consume;"
    return sql


# 组装空间join查询
def spatial_join_query(spatial_relations, tmp_operator, index_point, index_region):
    sql = ''
    if tmp_operator == 'ininterior':
        sql = "query " + spatial_relations[index_point]['name'] + " feed {a} " + spatial_relations[index_region]['name']\
            + " feed {b} symmjoin [.GeoData_a ininterior ..GeoData_b] consume;"
    else:
        sql = "query " + spatial_relations[0]['name'] + " feed {a} " + spatial_relations[1]['name']\
            + " feed {b} symmjoin [.GeoData_a intersects1 ..GeoData_b] consume;"
    return sql

# 组装距离join查询
def distance_join_query(spatial_relations, max_distance):
    sql = "query " + spatial_relations[0]['name'] + " feed {a} " + spatial_relations[1]['name']\
        + " feed {b} symmjoin [distance(.GeoData_a, ..GeoData_b) <= " + max_distance + "] consume;"
    return sql


# 一个关系和一个地点时的聚合查询
# 组装聚合-count查询
def place_count_query(relation, place, tmp_operator):
    sql = "query " + relation['name'] + " feed filter [.GeoData " + tmp_operator + " " + place + "] count;"
    return sql
# 组装聚合-sum查询
def place_sum_query(relation, place):
    sql = "query " + relation['name'] + " feed extend [IntersectionArea: area(intersection1(.GeoData, "\
        + place + "))] sum[IntersectionArea];"
    return sql
# 组装聚合-max查询
def place_max_query(relation, place):
    sql = "query " + relation['name'] + " feed extend [IntersectionArea: area(intersection1(.GeoData, "\
        + place + "))] sortby[IntersectionArea desc] head[1] consume;"
    return sql

# 两个关系时的聚合查询
# 组装聚合-count查询
def aggregation_count_query(spatial_relations, tmp_operator, index_point, index_region):
    sql = ''
    if tmp_operator == 'ininterior':
        sql = "query " + spatial_relations[index_region]['name'] + " feed extend [Cnt: fun(t: TUPLE) "\
            + spatial_relations[index_point]['name'] + " feed filter [.GeoData ininterior attr(t, GeoData)] count] consume;"
    else:
        sql = "query " + spatial_relations[0]['name'] + " feed extend [Cnt: fun(t: TUPLE) "\
            + spatial_relations[1]['name'] + " feed filter [.GeoData intersects attr(t, GeoData)] count] consume;"
    return sql
# 组装聚合-max查询
def aggregation_max_query(spatial_relations, tmp_operator, index_point, index_region):
    sql = ''
    if tmp_operator == 'ininterior':
        sql = "query " + spatial_relations[index_region]['name'] + " feed extend [Cnt: fun(t: TUPLE) "\
            + spatial_relations[index_point]['name'] + " feed filter [.GeoData ininterior attr(t, GeoData)] count] sortby[Cnt desc] head[1] consume;"
    else:
        sql = "query " + spatial_relations[0]['name'] + " feed extend [Cnt: fun(t: TUPLE) "\
            + spatial_relations[1]['name'] + " feed filter [.GeoData intersects attr(t, GeoData)] count] sortby[Cnt desc] head[1] consume;"
    return sql


# 判断 spatial_relations 中有几个关系的place属性不为空
def num_placeInRel(spatial_relations):
    if len(spatial_relations) == 0:
        num = 0
    elif len(spatial_relations) == 1:
        if spatial_relations[0]['place'] == '':
            num = 0
        else:
            num = 1
    elif len(spatial_relations) == 2:
        if spatial_relations[0]['place'] == '' and spatial_relations[1]['place'] == '':
            num = 0
        elif spatial_relations[0]['place'] != '' and spatial_relations[1]['place'] != '':
            num = 2
        else:
            num = 1
    else:
        num = 0  
    return num

# 前提是 spatial_relations 中有1个关系的place属性不为空，返回该关系的index
def index_placeInRel(spatial_relations):
    for i in range(len(spatial_relations)):
        if spatial_relations[i]['place'] != '':
            index = i
            break
    return index
# query_type, spatial_relations, place, num_neighbors, max_distance, time, obj_id, sorted_attr, is_less, is_more, is_decreasing, is_increasing = NLU.get_semantic_information(sentence)
#时间段查询
def time_interval_query(id_cond,place_cond,time_cond,spatial_relations,neighbor_query):
    sql_secondo = ""
    commonpart1 = "query "
    commonpart2 = " feed "
    # 火车id
    # idcond1 = "filter [.Id="
    idcond1 = "filter [." + "Id" + "="
    idcond3 = "]"
    # ---------------------------------查询地点或轨迹--------------------------------

    # 查询地点或轨迹语句块
    part3_place = " filter[.Trip present "
    # 轨迹查询语句块
    part5_trajectory = "] extend[Stretch: trajectory(.Trip atperiods "
    # part7_trajectory = ")]project[Id, Line, Stretch] consume;"
    part7_trajectory = ")] " + "project[" + "Stretch] consume;"
    # 地点查询语句块
    part4_oneplace = ") extend[Pos: val(.Trip atinstant "
    part5_oneplace = "] extend[Pos: val(.Trip atinstant "
    # part7_oneplace = ")] project[Id, Line, Pos] consume;"
    part7_oneplace = ")] " + "project[" + "Pos] consume;"
    # 时间段条件
    timescond = ""
    timescond_part1 = "[const periods value ((\"2003-11-20-"
    timescond_part3 = "\" \"2003-11-20-"
    timescond_part5 = "\" TRUE TRUE))]"
    # 时间点条件
    timecond = ""
    timecond_part1 = "[const instant value \"2003-11-20-"
    timecond_part3 = "\"]"
    # -----------------------------查询时间或时间段----------------------------------
    # 查询时间或时间段
    part3_time = " filter[.Trip passes "
    # 时间段语句块
    part5_times = "] extend[Times: deftime(.Trip  at "
    # part7_times = ")] project[Id, Line, Times]  consume;"
    part7_times = ")] " + "project[" + "Times]  consume;"
    # --------------------------------查询火车--------------------------------------
    part3_train = "filter [(deftime(.Trip  at "
    part5_train = ") intersects "
    part7_train = ")]"
    last = "consume;"

    # -------------------------------近邻查询语句块----------------------------------
    sql_secondo1 = sql_secondo2 = ''
    # 第一句指令等于first_sql + （var = 't' + id_cond[0]） + first_sql_part1 + id_cond[0] + first_sql_part3
    first_sql = 'let '
    id_cond_str = ', '.join(id_cond)
    first_sql_part1 = ' = ' + 'Trains' + ' feed filter[.' + spatial_relations[0]['place_name_attr'] + ' = '
    # print("id_cond in NN:", id_cond)
    first_sql_part3 = '] extract[Trip];'

    second_sql_part1 = 'query UTOrdered feed '
    second_sql_part3 = ' knearest[UTrip, '  # 后加定义的移动点var
    second_sql_part5 = ', '  # 后加邻居个数
    second_sql_part7 = '] '
    second_sql_part9 = ' consume;'
    # ------------------------------时间段过滤器语句块---------------------------------
    time_filter = ''
    time_filter_part1 = 'filter [(deftime(.UTrip) intersects '  # 后加时间段
    time_filter_part3 = ')] '
    # -------------------------------根据线路近邻查询语句块-----------------------------
    line_filter = ''
    line_filter_part1 = 'filter[.Line ='  # 后加线路号
    line_filter_part3 = ' ] '
    line_id = []


    subject = "Trains"
    if neighbor_query == '0':
        if id_cond:
            if place_cond:
                if time_cond:
                    if len(time_cond) == 1:
                        idcond = idcond1 + id_cond[0] + idcond3
                        timecond = timecond_part1 + time_cond[0] + timecond_part3
                        sql_secondo = commonpart1 + subject + commonpart2 + idcond + part3_place \
                                      + timecond + part5_oneplace + timecond + ")] "+ part3_time \
                                  + place_cond[0] + part5_times + place_cond[0] +part7_oneplace
                    if len(time_cond) == 2:
                        idcond = idcond1 + id_cond[0] + idcond3
                        timecond = timescond = timescond_part1 + time_cond[0] \
                                               + timescond_part3 + time_cond[1] + timescond_part5
                        sql_secondo = commonpart1 + subject + commonpart2 + idcond + part3_place \
                                      + timecond + part5_trajectory + timecond + ")] "+ part3_time \
                                  + place_cond[0] + part5_times + place_cond[0] +part7_trajectory
                else:  # 火车id, 地点  /查时间
                    idcond = idcond1 + id_cond[0] + idcond3
                    sql_secondo = commonpart1 + subject + commonpart2 + idcond + part3_time \
                                  + place_cond[0] + part5_times + place_cond[0] + part7_times
            else:
                if time_cond:
                    if len(time_cond) == 1:  # 火车id，时间 /查地点
                        idcond = idcond1 + id_cond[0] + idcond3
                        timecond = timecond_part1 + time_cond[0] + timecond_part3
                        sql_secondo = commonpart1 + subject + commonpart2 + idcond + part3_place \
                                      + timecond + part5_oneplace + timecond + part7_oneplace
                    if len(time_cond) == 2:  # 火车id，时间段 /查地点
                        idcond = idcond1 + id_cond[0] + idcond3
                        timecond = timescond = timescond_part1 + time_cond[0] \
                                               + timescond_part3 + time_cond[1] + timescond_part5
                        sql_secondo = commonpart1 + subject + commonpart2 + idcond + part3_place \
                                      + timescond + part5_trajectory + timescond + part7_trajectory
                else:  # 火车id ,地点 /查时间
                    idcond = idcond1 + id_cond[0] + idcond3
                    sql_secondo = commonpart1 + subject + commonpart2 + idcond + part3_time \
                                  + place_cond[0] + part5_times + place_cond[0] + part7_times
        else:
            if place_cond:
                if time_cond:
                    if len(time_cond) == 1:
                        print("Standby")
                    if len(time_cond) == 2:  # 地点，时间段 /查火车
                        timecond = timescond = timescond_part1 + time_cond[0] \
                                               + timescond_part3 + time_cond[1] + timescond_part5
                        sql_secondo = commonpart1 + subject + commonpart2 + part3_train \
                                      + place_cond[0] + part5_train + timecond + part7_train + last
                else:  # 地点 /查时间
                    sql_secondo = commonpart1 + subject + commonpart2 + part3_time + place_cond[0] \
                                  + part5_times + place_cond[0] + part7_times
            else:
                if time_cond:
                    if len(time_cond) == 1:  # 时间 /查地点
                        timecond = timecond_part1 + time_cond[0] + timecond_part3
                        sql_secondo = commonpart1 + subject + commonpart2 + part3_place + timecond \
                                      + part5_oneplace + timecond + part7_oneplace
                    if len(time_cond) == 2:  # 时间段 /查轨迹
                        timecond = timescond = timescond_part1 + time_cond[0] \
                                               + timescond_part3 + time_cond[1] + timescond_part5
                        sql_secondo = commonpart1 + subject + commonpart2 + part3_place + timescond \
                                      + part5_trajectory + timescond + part7_trajectory
    else:#近邻查询
        num_neighbors = neighbor_query
        if time_cond:#根据时间段查
            if len(time_cond) == 1:
                timecond = timescond_part1 + time_cond[0] + timescond_part3+time_cond[0]\
                    + timescond_part5
                time_filter = time_filter_part1 + timecond + time_filter_part3
            if len(time_cond) == 2:
                timecond  = timescond_part1 + time_cond[0] + timescond_part3 + time_cond[1]\
                    + timescond_part5
                time_filter = time_filter_part1 + timecond + time_filter_part3
        if line_id:#根据线路查
            line_filter = line_filter_part1 + line_id + line_filter_part3
        var = 't' + id_cond[0]
        sql_secondo1 = first_sql + var + first_sql_part1 + id_cond[0] + first_sql_part3
        sql_secondo2 = second_sql_part1 + line_filter + time_filter + second_sql_part3 + var + second_sql_part5\
                + num_neighbors +second_sql_part7 + second_sql_part9
    if sql_secondo:
        return sql_secondo
    else:
        sql_secondo = sql_secondo1 + '\n' + sql_secondo2
        return sql_secondo

###########################################################已修改所需的实体
def secondo(sentence, test):
    # 从 NLU.py 文件中获取关键语义信息
    query_type, spatial_relations, place, num_neighbors, max_distance, time, obj_id, sorted_attr, is_less, is_more, is_decreasing, is_increasing = NLU.get_semantic_information(sentence)
    # time_str = ' '.join(map(str, time))
    # obj_str = ' '.join(map(str, obj_id))
    # print(sentence)
    # # query_type = "Basic-area Query"
    # print("query_type: ", end='')
    # print(query_type)
    # print("spatial_relations: ", end='')
    # print(spatial_relations)
    # print("place: ", end='')
    # print(place)
    # print("neighbor_num: " + num_neighbors)
    # print("max distance: " + str(max_distance))
    # print("time: " , time)
    # print("obj_id: " , obj_id)
    # print("spatial_relation",spatial_relations)
    # print()

    sql_secondo = ""

    # 单独处理基础查询（求距离、方向、长度、面积）###########单独一块查询#########
    if query_type in ['Spatial Basic-distance Query', 'Spatial Basic-direction Query', 'Spatial Basic-length Query', 'Spatial Basic-area Query']:
        # 如果是求距离或方向
        if query_type in ['Spatial Basic-distance Query', 'Spatial Basic-direction Query']:
            # 确定运算符
            if query_type == 'Spatial Basic-distance Query':
                operator = 'distance'
            else:
                operator = 'direction'
            if len(place) == 2:
                # 如果俩地点都单独存在
                if num_placeInRel(spatial_relations) == 0:
                    sql_secondo = "query " + operator + "(" + place[0] + ", " + place[1] + ");"
                # 如果一个地点单独存在，另一个存在于关系中
                elif num_placeInRel(spatial_relations) == 1:
                    if len(spatial_relations) == 1:
                        index = 0
                    else:
                        index = index_placeInRel(spatial_relations)
                    # 对地点进行表示
                    tmp_place = '(' + spatial_relations[index]['name'] + ' feed filter [.' + spatial_relations[index]['place_name_attr']\
                        + ' = "' + spatial_relations[index]['place'] + '"] extract[GeoData])'
                    if place[0] == spatial_relations[index]['place']:
                        sql_secondo = "query " + operator + "(" + place[1] + ", " + tmp_place + ");"
                    else:
                        sql_secondo = "query " + operator + "(" + place[0] + ", " + tmp_place + ");"
                # 如果俩地点都存在于关系中
                elif num_placeInRel(spatial_relations) == 2:
                    tmp_place1 = '(' + spatial_relations[0]['name'] + ' feed filter [.' + spatial_relations[0]['place_name_attr']\
                        + ' = "' + spatial_relations[0]['place'] + '"] extract[GeoData])'
                    tmp_place2 = '(' + spatial_relations[1]['name'] + ' feed filter [.' + spatial_relations[1]['place_name_attr']\
                        + ' = "' + spatial_relations[1]['place'] + '"] extract[GeoData])'
                    sql_secondo = "query " + operator + "(" + tmp_place1 + ", " + tmp_place2 + ");"
                else:
                    print("[error]")
            else:
                print("[error]: The number of places should be 2.")
        # 如果是求长度或距离
        else:
            # 确定运算符
            if query_type == 'Spatial Basic-length Query':
                operator = 'size'
            else:
                operator = 'area'
            if len(place) == 1:
                if num_placeInRel(spatial_relations) == 0:
                    sql_secondo = "query " + operator + "(" + place[0] + ");"
                elif num_placeInRel(spatial_relations) == 1:
                    index = index_placeInRel(spatial_relations)
                    # 对地点进行表示
                    tmp_place = '(' + spatial_relations[index]['name'] + ' feed filter [.' + spatial_relations[index]['place_name_attr']\
                        + ' = "' + spatial_relations[index]['place'] + '"] extract[GeoData])'
                    sql_secondo = "query " + operator + tmp_place + ";"
                else:
                    print("[error]")
            else:
                print("[error]: The number of places should be 1.")

        return sql_secondo


    relation_num = len(spatial_relations)
    if relation_num == 2 and query_type != 'Normal Basic Query' and query_type!="Time Interval Query" and query_type != "Time Point Query"  and query_type != "Spatio-Temporal Range Query" and query_type != "Time Range Query" and query_type != "Moving Objects Nearest Neighbor Query" and query_type != "Spatio-temporal Join Query" and query_type != "Similarity Query":
        # 有俩空间关系，且 'place' 属性均为空，则为 join 查询 或 聚合查询，共四种，根据查询类型进行区分
        if spatial_relations[0]['place'] == '' and spatial_relations[1]['place'] == '':
            # 现根据俩关系的GeoData，确定是用哪个运算符：ininterior 或者 intersects，确定哪个的GeoData是point，哪个的GeoData是region
            tmp_operator = ''
            index_point = 0
            index_region = 0
            if spatial_relations[0]['GeoData'] == 'point':
                if spatial_relations[1]['GeoData'] == 'region':
                    tmp_operator = 'ininterior'
                    index_point = 0
                    index_region = 1
                else:
                    print("[error]: To judge the location relationship, spatial objects should be {line, region} x {line, region} || point x region.")
                    return sql_secondo
            elif spatial_relations[1]['GeoData'] == 'point':
                if spatial_relations[0]['GeoData'] == 'region':
                    tmp_operator = 'ininterior'
                    index_point = 1
                    index_region = 0
                else:
                    print("[error]: To judge the location relationship, spatial objects should be {line, region} x {line, region} || point x region.")
                    return sql_secondo
            else:
                tmp_operator = 'intersects'
            # 空间join查询
            if query_type == "Spatial Join Query":
                sql_secondo = spatial_join_query(spatial_relations, tmp_operator, index_point, index_region)
            # 距离join查询
            elif query_type == "Spatial Join Query":
                sql_secondo = distance_join_query(spatial_relations, max_distance)
            # 聚合-count查询
            elif query_type == "Spatial Aggregation-count Query":
                sql_secondo = aggregation_count_query(spatial_relations, tmp_operator, index_point, index_region)
            # 聚合-max查询
            elif query_type == "Spatial Aggregation-max Query":
                sql_secondo = aggregation_max_query(spatial_relations, tmp_operator, index_point, index_region)
            else:
                print("[error]: The query type is incorrect.")
                return sql_secondo
        # 有俩查询地点，则报错
        elif spatial_relations[0]['place'] != '' and spatial_relations[1]['place'] != '':
            print("[error]: The number of spatial relationships should be 1 or 2.")
            return sql_secondo
        # 一个关系和一个存在于关系中的地点，则为范围查询、最近邻查询和聚合查询，共五种，根据查询类型进行区分
        else:
            # 先确定关系和地点
            index_place = 0
            index_relation = 0
            if spatial_relations[0]['place'] != '':
                index_place = 0
                index_relation = 1
            else:
                index_place = 1
                index_relation = 0
            # 对地点进行表示
            tmp_place = '(' + spatial_relations[index_place]['name'] + ' feed filter [.' + spatial_relations[index_place]['place_name_attr']\
                + ' = "' + spatial_relations[index_place]['place'] + '"] extract[GeoData])'
            # 确定是用哪个运算符：ininterior 或者 intersects，范围查询和聚合查询用得到
            tmp_operator = ''
            if spatial_relations[index_relation]['GeoData'] == 'point':
                if spatial_relations[index_place]['GeoData'] == 'region':
                    tmp_operator = 'ininterior'
                else:
                    print("[error]: To judge the location relationship, spatial objects should be {line, region} x {line, region} || point x region.")
                    return sql_secondo
            elif spatial_relations[index_place]['GeoData'] == 'point':
                print("[error]: To judge the location relationship, spatial objects should be {line, region} x {line, region} || point x region.")
                return sql_secondo
            else:
                tmp_operator = 'intersects'
            # 范围查询
            if query_type == "Spatial Range Query":
                sql_secondo = range_query(spatial_relations[index_relation], tmp_place, tmp_operator)
            # 最近邻居查询
            elif query_type == "Spatial Nearest Neighbor Query":
                sql_secondo = nn_query(spatial_relations[index_relation], tmp_place, num_neighbors)
            # 聚合-count查询
            elif query_type == "Spatial Aggregation-count Query":
                sql_secondo = place_count_query(spatial_relations[index_relation], tmp_place, tmp_operator)
            # 聚合-sum查询，此处只考虑region和region相交面积之和
            elif query_type == "Spatial Aggregation-sum Query":
                if spatial_relations[index_relation]['GeoData'] == 'region' and spatial_relations[index_place]['GeoData'] == 'region':
                    sql_secondo = place_sum_query(spatial_relations[index_relation], tmp_place)
                else:
                    print("[error]: The Aggregation-sum query only considers the sum of areas where regions intersect.")
                    return sql_secondo
            # 聚合-max查询，此处只考虑region和region相交面积的最大值
            elif query_type == "Spatial Aggregation-max Query":
                if spatial_relations[index_relation]['GeoData'] == 'region' and spatial_relations[index_place]['GeoData'] == 'region':
                    sql_secondo = place_max_query(spatial_relations[index_relation], tmp_place)
                else:
                    print("[error]: You can query the maximum area of intersecting regions.")
                    return sql_secondo
            else:
                print("[error]: The query type is incorrect.")
                return sql_secondo

    elif relation_num == 1 and query_type!="Normal Basic Query" and query_type!="Time Interval Query" and query_type != "Time Point Query" and query_type != "Spatio-Temporal Range Query" and query_type != "Time Range Query" and query_type != "Moving Objects Nearest Neighbor Query" and query_type != "Spatio-temporal Join Query" and query_type != "Similarity Query":
        # 如果只有一个空间关系，则该 place 必为空，也应当有一个已知的地点
        if(spatial_relations[0]['place'] == ''):
            # 一个关系和一个单独的地点，则为范围查询、最近邻查询和聚合查询，共五种，根据查询类型进行区分
            if(len(place) > 0):
                # 确定是用哪个运算符：ininterior 或者 intersects，范围查询和聚合查询用得到
                tmp_operator = ''
                if spatial_relations[0]['GeoData'] == 'point':
                    tmp_operator = 'ininterior'
                else:
                    tmp_operator = 'intersects'
                # 范围查询
                if query_type == "Spatial Range Query":
                    sql_secondo = range_query(spatial_relations[0], place[0], tmp_operator)
                # 最近邻居查询
                elif query_type == "Spatial Nearest Neighbor Query":
                    sql_secondo = nn_query(spatial_relations[0], place[0], num_neighbors)
                # 聚合-count查询
                elif query_type == "Spatial Aggregation-count Query":
                    sql_secondo = place_count_query(spatial_relations[0], place[0], tmp_operator)
                # 聚合-sum查询，此处只考虑region和region相交面积之和
                elif query_type == "Spatial Aggregation-sum Query":
                    sql_secondo = place_sum_query(spatial_relations[0], place[0])
                # 聚合-max查询，此处只考虑region和region相交面积的最大值
                elif query_type == "Spatial Aggregation-max Query":
                    sql_secondo = place_max_query(spatial_relations[0], place[0])
                else:
                    print("[error]: The query type is incorrect.")
                    return sql_secondo
            else:
                print("[error]: If there is a spatial relationship, the number of places should also be 1.")
                return sql_secondo
        else:
            print("[error]: The number of spatial relationships should be 1 or 2.")
        ########################################单独的normal basic 单属性查询#################

    elif query_type == "Normal Basic Query":
        operator = "sortbyh"
        # print("get in normal query")
        if spatial_relations[0]['name']:
            if obj_id:
                # if is_less:
                #     if is_increasing:
                #         sql_secondo = "query " +spatial_relations[0]['name']+ "feed filter [." + spatial_relations[0]['place_name_attr'] +"<"+ sorted_attr + "]" + operator \
                #         + "["+ spatial_relations[0]['place_name_attr']+"]" + "project["+ spatial_relations[0]['place_name_attr'] + "] consume;"
                #     elif is_decreasing:
                #         sql_secondo = "query " +spatial_relations[0]['name']+ "feed filter [." + spatial_relations[0]['place_name_attr'] +"<"+ sorted_attr + "]" + operator \
                #         + "["+ spatial_relations[0]['place_name_attr']+"desc]" + "project["+ spatial_relations[0]['place_name_attr'] + "] consume;"
                # elif is_more:
                #     if is_increasing:
                #         sql_secondo = "query " +spatial_relations[0]['name']+ "feed filter [." + spatial_relations[0]['place_name_attr'] +">"+ sorted_attr + "]" + operator \
                #         + "["+ spatial_relations[0]['place_name_attr']+"]" + "project["+ spatial_relations[0]['place_name_attr'] + "] consume;"
                #     elif is_decreasing:
                #         sql_secondo = "query " +spatial_relations[0]['name']+ "feed filter [." + spatial_relations[0]['place_name_attr'] +">"+ sorted_attr + "]" + operator \
                #         + "["+ spatial_relations[0]['place_name_attr']+"desc]" + "project["+ spatial_relations[0]['place_name_attr'] + "] consume;"
                sql_secondo = "query " + spatial_relations[0]['name'] + " feed filter [." + spatial_relations[0]['place_name_attr'] + "=" + obj_id + "]" + " consume;"
                relation_sql_secondo = "select * from " + spatial_relations[0]['name'] + " where " +spatial_relations[0]['place_name_attr'] + "=" + obj_id
            elif sorted_attr:
                if is_less:
                    if is_increasing:
                        sql_secondo = "query " + spatial_relations[0]['name'] + " feed filter [." + \
                                      spatial_relations[0]['place_name_attr'] + "<" + sorted_attr[0] + "] " + operator \
                                      + "[" + spatial_relations[0]['place_name_attr'] + "]" + " project[" + \
                                      spatial_relations[0]['place_name_attr'] + "] consume;"
                        relation_sql_secondo = "select * from " + spatial_relations[0]['name'] + " where " + spatial_relations[0]['place_name_attr'] + "<" + sorted_attr[0] + " sort by " + spatial_relations[0]['place_name_attr']
                    elif is_decreasing:
                        sql_secondo = "query " + spatial_relations[0]['name'] + " feed filter [." + \
                                      spatial_relations[0]['place_name_attr'] + "<" + sorted_attr[0] + "] " + operator \
                                      + "[" + spatial_relations[0]['place_name_attr'] + " desc]" + " project[" + \
                                      spatial_relations[0]['place_name_attr'] + "] consume;"
                        relation_sql_secondo = "select * from " + spatial_relations[0]['name'] + " where " + \
                                               spatial_relations[0]['place_name_attr'] + "<" + sorted_attr[0] + " sort by " + spatial_relations[0]['place_name_attr']+ " desc"
                    else:
                        sql_secondo = "query " + spatial_relations[0]['name'] + " feed filter [." + \
                                      spatial_relations[0]['place_name_attr'] + "<" + sorted_attr[0] + "] " + \
                                      " project[" + spatial_relations[0]['place_name_attr'] + "] consume;"
                        relation_sql_secondo = "select * from " + spatial_relations[0]['name'] + " where " + \
                                               spatial_relations[0]['place_name_attr'] + "<" + sorted_attr[0]
                elif is_more:
                    if is_increasing:
                        sql_secondo = "query " + spatial_relations[0]['name'] + " feed filter [." + \
                                      spatial_relations[0]['place_name_attr'] + ">" + sorted_attr[0] + "] " + operator \
                                      + "[" + spatial_relations[0]['place_name_attr'] + "]" + " project[" + \
                                      spatial_relations[0]['place_name_attr'] + "] consume;"
                        relation_sql_secondo = "select * from " + spatial_relations[0]['name'] + " where " + \
                                               spatial_relations[0]['place_name_attr'] + ">" + sorted_attr[0] + " sort by " + spatial_relations[0]['place_name_attr']
                    elif is_decreasing:
                        sql_secondo = "query " + spatial_relations[0]['name'] + " feed filter [." + \
                                      spatial_relations[0]['place_name_attr'] + ">" + sorted_attr[0] + "] " + operator \
                                      + "[" + spatial_relations[0]['place_name_attr'] + " desc]" + " project[" + \
                                      spatial_relations[0]['place_name_attr'] + "] consume;"
                        relation_sql_secondo = "select * from " + spatial_relations[0]['name'] + " where " + \
                                               spatial_relations[0]['place_name_attr'] + ">" + sorted_attr[0] + " sort by " + spatial_relations[0]['place_name_attr'] + " desc"
                    else:
                        sql_secondo = "query " + spatial_relations[0]['name'] + " feed filter [." + \
                                      spatial_relations[0]['place_name_attr'] + ">" + sorted_attr[0] + "] " + \
                                      " project[" + \
                                      spatial_relations[0]['place_name_attr'] + "] consume;"
                        relation_sql_secondo = "select * from " + spatial_relations[0]['name'] + " where " + \
                                               spatial_relations[0]['place_name_attr'] + ">" + sorted_attr[0]
                else:
                    sql_secondo = "query " + spatial_relations[0]['name'] + " feed filter [." + spatial_relations[0]['place_name_attr'] + "=" + sorted_attr[0] + "] consume;"
                    # sql_secondo = "query " + spatial_relations[0]['name']
                    relation_sql_secondo = "select * from " + spatial_relations[0]['name'] + " where " + \
                                           spatial_relations[0]['place_name_attr'] + "=" + sorted_attr[0]
            else:
                sql_secondo = "query " + spatial_relations[0]['name'] + ";"
                relation_sql_secondo = "select * from " + spatial_relations[0]['name']
        print("relation_sql_secondo:",relation_sql_secondo)
        return sql_secondo
    # else:
    #     print("[error]: The number of spatial relationships should be 1 or 2.")
    # elif query_type == "Time interval query" or query_type == "Range Query ":
    #     sql_secondo = time_interval_query()
    if query_type == "Time Interval Query" or query_type == "Time Point Query" or query_type == "Spatio-Temporal Range Query" or query_type == "Time Range Query" or query_type == "Moving Objects Nearest Neighbor Query" or query_type == "Spatio-temporal Join Query" or query_type == "Similarity Query":
        sql_secondo = time_interval_query(obj_id, place, time, spatial_relations,num_neighbors)
    return sql_secondo

#    query_type, spatial_relations, place, num_neighbors, max_distance, time, obj_id, sorted_attr, is_less, is_more, is_decreasing, is_increasing = NLU.get_semantic_information(sentence)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python secondo.py <sentence> <object>")
        sys.exit(1)
    str1 = str(sys.argv[1])
    str2 = str(sys.argv[2])
    sql = secondo(str1, str2)
    print(sql)

# if __name__ == '__main__':
    # 注意：如果地点名称由好多单词组成，最好将每个单词首字母大写后放在一起组成一个单词
    # 范围查询
    # str1 = "Which rbahnhof are located in thecenter?"
    # str1 = "What strassen run through thecenter?"
    # str1 = "What kinos are there in the TreptowerPark?"
    # 最近邻居查询
    # str2 = "Find the five closest kinos to the BGrenzenLine."
    # str2 = "Find the five closest Ubahn to the westhafen."
    # str2 = "Find the one-hundred nearest kneipen to the flaechen named Viktoriapark?"
    # str2 = "Show me some trajecories of some trains"
    # str2 = "list the trains which ids are greater than 5."
    # str2="what is the temperature at 7am?"
    # str2 = "Where were the trains at 8am?"
    # str2 = "Returns the distance between mehringdamm and alexanderplatz."
    # str2="list the trains which ids are less than 387 and sort them in decreasing order"
    # str2 = "Show me five nearest neighbors to the train 5 between 8am to 10am."
    # join 查询示例
    # str3 = "What are the ubahn that go through each sehenswuerdreg."
    # str3 = "In each sehenswuerdreg, list the details of the kinos."
    # str3 = "What kinos are within one kilometer of each Flaechen?"
    # str3 = "What kinos are within 1.5 kilometers of each Flaechen?"
    # 聚合查询示例，俩关系
    # str4 = "How many kinos are in each Flaechen?"
    # str4 = "How many strassens does each RBahn intersect?"
    # str4 = "Please list the Flaechen that contains the most kinos."
    # str4 = "Please list the RBahn that intersects at most strassen."
    # 聚合查询示例，一个关系一个地点
    # str4 = "How many kinos are there in TreptowerPark?"
    # str4 = "What is the total area where TreptowerPark and WFlaechen intersect?"
    # str4 = "Which WFlaechen has the largest area of intersection with TreptowerPark?"
    # str4 = "How many kinos are there in thecenter?"
    # str4 = "What is the total area where koepenick and WFlaechen intersect?"
    # str4 = "Which WFlaechen has the largest area of intersection with koepenick?"
    #
    # 基础查询示例
    # str5 = "Returns the distance between mehringdamm and alexanderplatz."
    # str5 = "Returns the distance between mehringdamm and TreptowerPark."
    # str5 = "Returns the distance between Viktoriapark and TreptowerPark."
    #
    # str5 = "Returns the direction from mehringdamm to alexanderplatz."
    # str5 = "Returns the direction from mehringdamm to TreptowerPark."
    # str5 = "Returns the direction from Viktoriapark to TreptowerPark."
    #
    # str5 = "Returns the length of PotsdamLine."
    # str5 = "Returns the length of U7."
    #
    # str5 = "What's the area of thecenter."
    # str5 = "Returns the area of Viktoriapark."


    # 注意：在南京路网数据库中，道路名字为纯数字的一定要在前面加一个字母 r，否则该道路名字无法识别
    # str4 = "What are the roads that intersect the r771668488 road?"
    # str4 = "Find the six closest junction to the r771668488."
    # sql_secondo = secondo(str2)
    # print("sql_secondo:",sql_secondo)