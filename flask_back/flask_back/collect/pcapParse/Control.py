from .constant import RTE_SDK, RTE_TARGET, capture_path, pdump_path
from subprocess import Popen, PIPE
from .protocol.parse import parse as PduParse
from .protocol.database.tables import DBSession
from .protocol.database.tables import CollectResult
from queue import Queue
import threading
import time as tim
import datetime
import io
import os
from . import dpktConstruct
from . import dpktHttpConstruct
from . import PduConstruct
import logging
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
logging.basicConfig(filename='Control.log', level=logging.DEBUG, format=LOG_FORMAT,datefmt=DATE_FORMAT)
# 环境变量
# env = {
#     'DPDKPath':'sdfsadfsa',
#     'DPDKLIB':'sfdasdfhasd'
# }

# 子程序运行的目录
# cwd = '/usr/home/....'

# shell 指定的命令会在shell里解释执行
# shell = True

# args参数。可以是一个字符串，可以是一个包含程序参数的列表。
# 要执行的程序一般就是这个列表的第一项，或者是字符串本身
# args = ['cat', 'test.txt']
# args = 'cat test.txt'
# 执行失败，因为没有指定执行程序的路径

# 0表示不缓冲，1表示行缓冲，其他正数表示进行的缓冲去字节数，负数表
# bufsize = 0

# 指定要执行的程序，它一般很少被用到：一般程序可以由args指定
# 如果shell = True， executable 可以用于指定哪个shell来执行
# （比如bash、csh、zsh等）
# window下，只有当你要执行的命令确实是shell内建命令（比如 dir, copy等），才需要指定shell=True
######## executable

# stdin, stdout, stderr指定子程序的标准输入，标准输出和标准错误。
# 可选的值由PIPE或者一个有效的文件描述符（其实是个正整数）或者一个文件对象
# 或者None。如果是PIPE，则表示需要创建一个新的管道，如果是None，不会
# 做任何重定向工作，子进程的文件描述符会集成父进程的。
# stdin = None
# stdout = None
# stderr = None

# 如果把preexec_fn设置为一个可调用的对象（比如函数），就会在子进程被执行
# 前被调用。仅限linux
######preexec_fn

# close_fds为True，Linux下会在开子进程前把除了0、1、2以外的文件描述符
# 都先关闭。在Windows下也不会继承其他文件描述符
# close_fds = True

# 如果universal_newlines设置为True, 则子进程的stdout和stderr被视为文本
# 对象，并且不管是Linux的行结束符还是其他系统的行结束符都被视为统一的'\n'
# universal_newlines=True

# subprocess.PIPE 一个可以被用于Popen的stdin、stdout、stderr等三个参数的特殊值。
# 表示需要创建一个新的管道。
# subprocess.STDOUT 一个可以被用于Popen的stderr参数的输出值，表示子程序的标准错误
# 汇合到标准输出

# 执行命令，并等待命令借宿，再返回子进程的返回值，参数同Popen
# subprocess.call(*popenargs, **kwargs)
# subprocess.call('ifconfig', shell=True)

# 执行上面的call命令，并检查返回值，如果子进程返回非0，则会抛出异常
# subprocess.check_call(*popenargs, **kwargs)
# subprocess.check_call('ifconfig')

# 执行程序，并返回标准输出
# subprocess.check_output(*popenargs, **kwargs)
# subprocess.check_output('ifconfig')

# Popen对象
# poll() 检查是否结束，设置返回值
# wait() 等待结束，设置返回值
# communicate() 参数是标准输入，返回标准输出和标准出错
# send_signal() 发送信号
# terminate() 终止进程，unix对应SIGTERM信号，windows下调用api函数TerminateProcess（）
# kill() 杀死(unix对应SIGKILL信号)，windows下同上
# stdin, stdout, stderr
# pid 进程ID
# returncode 进程返回值


# shell = subprocess.Popen('env', env={'test':'123', 'testtext':'zzz'})


# que = queue.Queue(maxsize=3)

_NoRUN_ = 1
_Running_ = 2
_Finished_ = 3
device_id = 0

CollectResource = threading.Lock()

class CollectThread:

    def __init__(self, threadnum = 1):
        # self.ThreadNum = 0
        self.parent_env = None
        self.ThreadPool = []
        self.pcapThreadPool = []
        self.pcapPath = []
        self._dealEnv()
        self.queue = Queue(maxsize=threadnum)
        self.state= _NoRUN_
        self.Thread = threading.Thread(target=self._runSample)
        self.Thread.start()
        logging.info('Main Thred Starting, And Watched Thread Starting.  ' + threading.current_thread().getName())

    def _dealEnv(self):
        Env = Popen('env', universal_newlines=True, stdout=PIPE)
        Env.wait()
        output = Env.stdout.read()
        outlist = output.split('\n')
        self.parent_env = {}
        for x in outlist:
            if x.find('=') != -1:
                self.parent_env[x[0:x.find('=')]]=x[x.find('=') + 1:]
        self.parent_env['RTE_SDK'] = RTE_SDK
        self.parent_env['RTE_TARGET'] = RTE_TARGET
        logging.info('The inital Env is ' + str(self.parent_env) + '  ' + threading.current_thread().getName())

    def put(self, item):
        if self.getState() == _Running_:
            logging.info('add the collect task is Failed.   ' + threading.current_thread().getName())
            return False
        logging.info('add The Collect task is Success.  ' + threading.current_thread().getName())
        self.queue.put(item)
        return True

    def _startJob(self, protocol, time, path):
        currentPath = tim.time()
        currentPath = str(int(currentPath))
        if not os.path.exists(os.path.join(capture_path, currentPath)):
            logging.info('make a new diectory for pcap files. ' + threading.current_thread().getName())
            os.mkdir(path=os.path.join(capture_path, currentPath))
        cmd = 'sudo '+ os.path.join(pdump_path, 'dpdk-pdump') + ' -- ' + ' --pdump '
        params = "'device_id="
        params += str(device_id) + ','
        params +='time='
        params += str(time) + ','
        if 'HL7' in protocol:
            params += 'hl7-dev='
            params += os.path.join(capture_path, currentPath, 'hl7.pcap')
            params += "'"
        if 'DICOM' in protocol:
            params += 'dicom-dev='
            params += os.path.join(capture_path, currentPath, 'dicom.pcap')
            params += ','
            params += 'http-dev='
            params += os.path.join(capture_path, currentPath, 'http.pcap')
            params += ','
            params += 'ftp-dev='
            params += os.path.join(capture_path, currentPath, 'ftp.pcap')
            params += "'"
        if protocol == 'ASTM':
            params += 'astm-dev='
            params += os.path.join(capture_path, currentPath, 'astm.pcap')
            if 'http-dev' in params:
                params += "'"
            else:
                params += ','
                params += 'http-dev='
                params += os.path.join(capture_path, currentPath, 'http.pcap')
                params += ','
                params += 'ftp-dev='
                params += os.path.join(capture_path, currentPath, 'ftp.pcap')
                params += "'"
        cmd += params
        logging.info('create script for collect task.   ' + threading.current_thread().getName())
        logging.info(cmd)
        return cmd, currentPath
    
    def getState(self):
        
        try:
            CollectResource.acquire()
            if self.state == _NoRUN_:
                if self.queue.empty():
                    return _NoRUN_
                return _Running_
            elif self.state == _Finished_:
                if not self.queue.empty():
                    return _Running_
                return self.state
            else:
                return self.state
        finally:
            CollectResource.release()
        pass

    def _runPopen(self, script):
        process = Popen(args=script, 
            shell=True, 
            env=self.parent_env, 
            # stdin=PIPE, 
            stdout=PIPE, 
            stderr=PIPE, 
            universal_newlines=True)
        # for i in process.communicate():
        #     logging.info(i)
        return process
    
    def _runSample(self):
        while True:
            try:
                CollectResource.acquire()
                if self.state == _NoRUN_:
                    # 没有正在运行的数据包捕获程序
                    if self.queue.empty() and len(self.ThreadPool) == 0:
                        # logging.info('no running collect task.   ' + threading.current_thread().getName())
                        pass
                    else:
                        logging.info('have a running collect task.  ' + threading.current_thread().getName())
                        item = self.queue.get()
                        script, currentPath = self._startJob(item['protocol'], item['time'], item['path'])
                        item['currentPath'] = currentPath
                        self.pcapPath.append(item)
                        session = DBSession()
                        try:
                            a = session.query(CollectResult).filter(CollectResult.id == item['id']).one()
                            a.start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            # print(a.start_time)
                            session.commit()
                        except:
                            session.rollback()
                        finally:
                            session.close()
                        process = self._runPopen(script)
                        # process.returncode=0
                        self.ThreadPool.append(process)
                        self.state = _Running_
                elif self.state == _Running_:
                    # 若有正在运行的程序
                    for i in self.ThreadPool:
                        # print(i.poll())
                        code = i.poll()
                        if not code is None:
                            for j in i.communicate():
                                logging.info(j)
                            logging.info('Have a collect Task is run success,start State move to Finished.   ' + threading.current_thread().getName())
                            self.ThreadPool.remove(i)
                            self.state = _Finished_
                            currentMessage = self.pcapPath.pop(0)
                            currentPath = os.path.join(capture_path, currentMessage['currentPath'])
                            size = 0
                            for path in os.listdir(currentPath):
                                threadOperator = None
                                if not os.path.isdir(os.path.join(currentPath, path)):
                                    filepath = os.path.basename(path)
                                    if not 'pcap' in filepath:
                                        continue
                                    size += os.path.getsize(os.path.join(currentPath, filepath))
                                    if 'hl7' in filepath:
                                        threadOperator = threading.Thread(name='hl7-ReConstruct'+'-' + currentPath, target=dpktConstruct.construct, args=[currentPath, filepath, 'hl7'])
                                    elif 'dicom' in filepath:
                                        threadOperator = threading.Thread(name='dicom-ReConstruct' + '-' + currentPath, target=PduConstruct.construct, args=[currentPath, filepath, 'dicom'])
                                        pass
                                        # threadOperator = threading.Thread(name='dicom-ReConstruct'+'-' + currentPath,target=PduParse, args=[os.path.join(currentPath, filepath)])
                                    elif 'astm' in filepath:
                                        threadOperator = threading.Thread(name='astm-ReConstruct'+'-' + currentPath,target=dpktConstruct.construct, args=[currentPath, filepath, 'astm'])
                                    elif 'http' in filepath:
                                        threadOperator = threading.Thread(name='http-ReConstruct'+'-' + currentPath,target=dpktHttpConstruct.construct, args=[currentPath, filepath, currentMessage['protocol'] + '|http', True])
                                        # continue
                                    elif 'ftp' in filepath:
                                        threadOperator = threading.Thread(name='ftp-ReConstruct'+'-' + currentPath,target=dpktConstruct.construct, args=[currentPath, filepath, currentMessage['protocol'] + '|ftp'])
                                        # continue
                                    self.pcapThreadPool.append(threadOperator)
                                    threadOperator.start()
                                    logging.info(filepath + ' pcap file reconstruct thread is starting.  ' + threading.current_thread().getName())
                            self.queue.task_done()
                            if not currentMessage['id'] is None:
                                # session.execute('update `collect_result` set `end_time`=%s, 
                                # `size`=%d where `id` = %d;'%(datetime.datetime.now()
                                # .strftime("%Y-%m-%d %H:%M:%S"), size, currentMessage['id'])).fetchall()
                                # session.commit()
                                session = DBSession()
                                try:
                                    a = session.query(CollectResult).filter(CollectResult.id == currentMessage['id']).one()
                                    a.size = size
                                    a.end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    # print(a.end_time)
                                    session.commit()
                                except:
                                    session.rollback()
                                finally:
                                    session.close()
                        pass
                elif self.state == _Finished_:
                    # 若正在处理的程序已经完成，然后处理pcap文件
                    # 本状态可以进入运行状态
                    for t in self.pcapThreadPool:
                        if t.isAlive():
                            continue
                        self.pcapThreadPool.remove(t)
                    if len(self.pcapThreadPool) == 0:
                        self.state = _NoRUN_
                        continue
                    if not self.queue.empty():
                        item = self.queue.get()
                        script, currentPath = self._startJob(item['protocol'], item['time'], item['path'])
                        self.pcapPath.append(currentPath)
                        process = self._runPopen(script)
                        self.ThreadPool.append(process)
                        self.state = _Running_
            finally:
                CollectResource.release()
            tim.sleep(1)
        pass

MainCollect = CollectThread()
# if __name__ == '__main__':
#     c = CollectThread()
#     while not c.put({'protocol':'DICOM', 'time':1, 'path':os.path.join(os.getcwd(), 'pcap')}):
#         continue
    # print(os.path.isfile('/home/yjn/Code/medical_instance/test6.pcap'))
