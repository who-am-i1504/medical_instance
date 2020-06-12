import pyhdfs
import ast
import os
import time
import threading
config = None
if config is None:
    with open('config/config.cfg', 'r') as f:
        data = f.read().replace('\n', '')
        config = ast.literal_eval(data)

class SyncPicHadoop:
    def __init__(self):
        self.hadoop, self.port, self.hadoop_path, self.pic_path, self.username = self.sync_hadoop()
        self.Thread = threading.Thread(target=self._syc_file)
        self.Thread.setDaemon(True)
        self.Thread.start()
        
    def sync_hadoop(self):
        hadoop = 'yl'
        port = 50070
        hadoop_path = '/usr/picture'
        pic_path = 'upload'
        username = 'yjn'
        if config is None:
            if 'hadoop' in config.keys():
                hadoop = config['hadoop']
            if 'hadoop_port' in config.keys():
                port = config['hadoop_port']
            if 'hadoop_pic_path' in config.keys():
                hadoop_path = config['hadoop_pic_path']
            if 'PicturePath' in config.keys():
                pic_path = config['PicturePath']
            if 'hadoop_username' in config.keys():
                username = config['hadoop_username']
        return hadoop, port, hadoop_path, pic_path, username
    
    def _syc_file(self):
        while True:
            fs = pyhdfs.HdfsClient(hosts=self.hadoop + ':' + str(self.port),user_name=self.username)
            if fs is not None:
                if fs.exists(self.hadoop_path):
                    for i in os.listdir(self.pic_path):
                        if fs.exists(os.path.join(self.hadoop_path, i)):
                            continue
                        else:
                            fs.copy_from_local(os.path.join(self.pic_path, i), os.path.join(self.hadoop_path, i))
            time.sleep(3600)
            # dirs = fs.exists(os.jo)
            # print(dirs)
SyncPicHadoop()
# if __name__ == '__main__':
#     sync_hadoop()