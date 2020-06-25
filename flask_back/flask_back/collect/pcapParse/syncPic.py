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
            try:
                fs = pyhdfs.HdfsClient(hosts=self.hadoop + ':' + str(self.port),user_name=self.username)
                if fs is None:
                    break
                if not fs.exists(self.hadoop_path):
                    break
                for i in os.listdir(self.pic_path):
                    self._sySubPath(os.path.join(self.pic_path, i), fs)
                time.sleep(3600)
                # dirs = fs.exists(os.jo)
                # print(dirs)
            except:
                break

    def _sySubPath(self, path, fs):
            if not os.path.exists(path):
                return
            if not os.path.isdir(path):
                if fs.exists(os.path.join(self.hadoop_path, path)):
                    return
                else:
                    fs.copy_from_local(os.path.join(path), os.path.join(self.hadoop_path, path))
            else:
                if fs.exists(os.path.join(self.hadoop_path, path)):
                    fs.mkdirs(os.path.join(self.hadoop_path, path))
                for i in os.listdir(path):
                    self._sySubPath(os.path.join(path, i), fs) 
SyncPicHadoop()
# if __name__ == '__main__':
#     sync_hadoop()