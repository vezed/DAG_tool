from src.Generator.dag import DAG


def get_property(dag: DAG, property_name):
    if property_name == '长度':
        return dag.longest_path_length
    elif property_name == '路径':
        return dag.paths
    elif property_name == '最长路径':
        return dag.longest_paths
    elif property_name == '宽度':
        return dag.longest_anti_chain_length
    elif property_name == '反链':
        return dag.anti_chains
    elif property_name == '最长反链':
        return dag.longest_anti_chain
    elif property_name == '最大入度':
        return dag.max_in_degree
    elif property_name == '最小入度':
        return dag.min_in_degree
    elif property_name == '平均入度':
        return dag.ave_in_degree
    elif property_name == '最大出度':
        return dag.max_out_degree
    elif property_name == '最小出度':
        return dag.min_in_degree
    elif property_name == '平均出度':
        return dag.ave_out_degree
