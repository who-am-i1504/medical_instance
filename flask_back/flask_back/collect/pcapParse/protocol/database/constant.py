import ast

config = None
if config is None:
    with open('config/config.cfg', 'r') as f:
        data = f.read().replace('\n', '')
        config = ast.literal_eval(data)
mysqllink = config['mysql_username'] + ':' + config['mysql_password']+'@'+config['mysql_server']