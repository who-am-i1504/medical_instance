import threading
import time
from subprocess import Popen, PIPE
from queue import Queue
import io

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

class CollectThread:

    def __init__(self, threadnum = 1):
        self.ThreadNum = 0
        self.parent_env = None
        self.ThreadPool = []
        self._dealEnv()
        self.queue = Queue(maxsize=threadnum)

    def _dealEnv(self):
        Env = Popen('env', universal_newlines=True, stdout=PIPE)
        Env.wait()
        output = Env.stdout.read()
        outlist = output.split('\n')
        self.parent_env = {}
        for x in outlist:
            if x.find('=') != -1:
                self.parent_env[x[0:x.find('=')]]=x[x.find('=') + 1:]

    def _startJob(self, protocol, time, path):
        currentPath = str(int(time.time()))
        if not os.exists(os.path.join(os.getcwd(), currentPath)):
            os.mkdir(os.path.join(os.getcwd(), currentPath))
        cmd = ['sudo', './dpdk-pdump', '--', '--pdump']
        params = 'device_id='
        params += device_id + ','
        params +='time='
        params += str(time) + ','
        if 'HL7' in protocol:
            params += 'hl7-dev='
            params += os.path.join(os.getcwd(), currentPath, 'hl7.pcap')
            params += ','
        if 'DICOM' in protocol:
            params += 'dicom-dev='
            params += os.path.join(os.getcwd(), currentPath, 'dicom.pcap')
            params += ','
        if protocol == 'ASTM':
            params += 'astm-dev='
            params += os.path.join(os.getcwd(), currentPath, 'astm.pcap')
            params += ','
        params += 'http-dev='
        params += os.path.join(os.getcwd(), currentPath, 'http.pcap')
        params += ','
        params += 'ftp-dev='
        params += os.path.join(os.getcwd(), currentPath, 'http.pcap')
        params += ','
        pass
    
    def getState(self):
        pass

    def runSample(self):
        pass


if __name__ == '__main__':
    c = CollectThread()
    print(c.dealEnv())