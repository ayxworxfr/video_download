import re
import os
import sys
import requests
import logging
import datetime
import importlib
from concurrent.futures import ThreadPoolExecutor  # 线程池
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex

class trans_ts:
    """
    url: ts文件下载地址前缀
    path: 文件保存地址
    """
    # 请自行修改
    def __init__(self, path = 'I:\\PythonWorkSpace\\video_download\\download', home = 'https://zuixin.zuixinbo.com/20171116/hkRBI61Z/307kb/hls/', filename = 'test.mp4'):
        self.path = path
        self.home = home
        self.filename = filename

    # 功能：失败提示，失败重试，失败记录日志，线程池提高并发，超时重试。
    def start(self):
        pool = ThreadPoolExecutor(15)
        
        # for name in range(2049001, 2054500):  # 【根据url修改】
        for name in range(2049001, 2049011):  # 【根据url修改】
            # 处理name  000
            url = home + 'PHh5L' + str(name) + ".ts"
            pool.submit(tt.download(url))


        # 作用1：关闭进程池入口不能再提交了   作用2：相当于jion 等待进程池全部运行完毕
        pool.shutdown(wait=True)
        self.merge()


    def download(self, name):
        file_name = re.findall('.*/(.*)', name)[0]
        print(file_name, "正在下载……")
        try:
            res = requests.get(name, timeout=15)
            temp_size = 0
            total_size = int(res.headers['Content-Length'])     # 获取将要下载文件的大小
            content = res.content
            file_path = self.path + "\\" + file_name
            with open(file_path, "wb") as f:
                # iter_content()函数就是得到文件的内容，
                # 有些人下载文件很大怎么办，内存都装不下怎么办？
                # 那就要指定chunk_size=1024，大小自己设置，
                # 意思是下载一点写一点到磁盘。
                for chunk in res.iter_content(chunk_size=1024):
                    if chunk:
                        temp_size += len(chunk)
                        f.write(chunk)
                        f.flush()
                        #############花哨的下载进度部分###############
                        done = int(50 * temp_size / total_size)
                        # 调用标准输出刷新命令行，看到\r回车符了吧
                        # 相当于把每一行重新刷新一遍
                        sys.stdout.write("\r[%s%s] %d%%" % ('█' * done, ' ' * (50 - done), 100 * temp_size / total_size))
                        sys.stdout.flush()
            print()
            print(file_name + '  下载成功')

        except Exception as e:
            # 报错提示
            print(file_name + '\x1b[1;30;41m 下载失败 \033[0m')
            print(e)
            print(file_name + '下载失败')

            # 记录日志
            my_log = logging.getLogger('lo')
            my_log.setLevel(logging.DEBUG)
            file = logging.FileHandler('error.log', encoding='utf-8')
            file.setLevel(logging.ERROR)
            my_log_fmt = logging.Formatter('%(asctime)s-%(levelname)s:%(message)s')
            file.setFormatter(my_log_fmt)
            my_log.addHandler(file)
            my_log.error(file_name + ' 下载失败 ')
            my_log.error(e)

            # 重新下载
            return self.download(name)  # 如果报错，重新执行一遍

    def merge(self):
        savefile = self.path + '/' + self.filename
        if not os.path.exists(savefile):
            f = open(savefile, 'w')
            f.close()

        files = []
        path_list=os.listdir(self.path)
        for file_name in path_list:
            if os.path.splitext(file_name)[1] == '.ts':
                files.append(file_name)

        # 合并ts文件
        os.chdir(self.path)
        shell_str = '+'.join(files)
        shell_str = 'copy /b '+ shell_str + ' ' + file_name
        print(shell_str)
        os.system(shell_str)
        # 删除ts文件
        os.system('del /Q *.ts')



if __name__ == '__main__':
    url = "http://bili.let-1977cdn.com/20190818/41VtSLrR/index.m3u8" 
    # https://zuixin.zuixinbo.com/20171116/hkRBI61Z/307kb/hls/PHh5L2049001.ts
    filename = 'test.mp4'
    home = 'https://zuixin.zuixinbo.com/20171116/hkRBI61Z/307kb/hls/'
    savefile = 'I:\\PythonWorkSpace\\video_download\\download'
    tt = trans_ts(savefile, home, filename)
    tt.start()

    

