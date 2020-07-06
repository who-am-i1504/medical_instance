import ast
config = None
if config is None:
    with open('config/config.cfg', 'r') as f:
        data = f.read().replace('\n', '')
        config = ast.literal_eval(data)
RTE_SDK=config['RTE_SDK']
RTE_TARGET=config['RTE_TARGET']
capture_path = config['capture_path']
pdump_path = config['pdump_path']
DeletePcap = config['DeletePcap']
# SysPas = config['SysPas']