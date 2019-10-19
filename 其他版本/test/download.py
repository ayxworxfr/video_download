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

class download:
    base = ''       # 网站根目录
    list_ts = []
    headers = {
		# 'Connection': 'keep - alive',
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
	}

    # 功能：失败提示，失败重试，失败记录日志，线程池提高并发，超时重试。
    def start(self, url, filename):
        download_path = os.getcwd() + "\download"
        if not os.path.exists(download_path):
            os.mkdir(download_path)

        #新建日期文件夹
        download_path = os.path.join(download_path, datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
        print("download_path: ", download_path)
        os.mkdir(download_path)
        self.path = download_path

        pool = ThreadPoolExecutor(5)
        # 解析m3u8
        self.parseM3u8(url)
        # 使用解析出来的ts地址下载
        for item in self.list_ts:
            pool.submit(self.download(item))

        # 作用1：关闭进程池入口不能再提交了   作用2：相当于jion 等待进程池全部运行完毕
        pool.shutdown(wait=True)
        self.merge(download_path, filename)

    def parseM3u8(self, url):
        # 得到真正的m3u8 url
        self.base = url.rsplit("/", 3)[0]
        try:
            text_tem = requests.get(url, timeout=10).text  # 获取M3U8文件内容
            url_real = self.base + text_tem.split("\n")[2]
            print("url_real: ", url_real)


            all_content = requests.get(url_real, timeout=10).text  # 获取第一层M3U8文件内容
            if "#EXTM3U" not in all_content:
                raise BaseException("非M3U8的链接")

            if "EXT-X-STREAM-INF" in all_content:  # 第一层
                file_line = all_content.split("\n")
                for line in file_line:
                    if '.m3u8' in line:
                        url = url.rsplit("/", 1)[0] + "/" + line # 拼出第二层m3u8的URL
                        all_content = requests.get(url).text


            items = re.findall(r',\n(.*)\n#EXTINF', all_content)

            for item in items:
                item = self.base + item
                # print("pd_url: ", item)
                self.list_ts.append(item)

            print(len(self.list_ts), "个url解析完成")
        except Exception as e:
            print(e)
            print("重新解析m3u8")
            return self.parseM3u8(url)

    def download(self, name):
        file_name = re.findall('.*/(.*)', name)[0]
        print(file_name, "正在下载……")
        try:
            # print("pd_url: ", name)
            res = requests.get(name,headers = self.headers, timeout=15)
            content = res.content
            file_path = self.path + "\\" + file_name
            with open(file_path, "wb") as f:
                f.write(res.content)
                f.flush()
            # 带进度条的下载
            """
            temp_size = 0
            total_size = int(res.headers['Content-Length'])		# 获取将要下载文件的大小
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
            """
            print(file_name, '下载成功')

        except Exception as e:
            # 报错提示
            print(e)
            print(file_name, '下载失败')

            # 记录日志
            my_log = logging.getLogger('lo')
            my_log.setLevel(logging.DEBUG)
            file = logging.FileHandler('error.log', encoding='utf-8')
            file.setLevel(logging.ERROR)
            my_log_fmt = logging.Formatter('%(asctime)s-%(levelname)s:%(message)s')
            file.setFormatter(my_log_fmt)
            my_log.addHandler(file)
            my_log.error(file_name + '下载失败 ')
            my_log.error(e)

            # 重新下载
            return self.download(name)  # 如果报错，重新执行一遍

    def merge(self, path, filename):
        os.chdir(path)
        cmd = "copy /b * new.tmp"
        os.system(cmd)
        os.system('del /Q *.ts')
        os.system('del /Q *.mp4')
        os.rename("new.tmp", filename)



if __name__ == '__main__':
    url = "http://bili.let-1977cdn.com/20190818/FQRL7kuS/index.m3u8"
    filename = '第二集.mp4'
    d = download()
    d.start(url, filename)
    # d.merge(r"I:\PythonWorkSpace\video_download\其他版本\download\20190921_211521", "test.mp4")

    

