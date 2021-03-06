"""
https://blog.csdn.net/cymy001/article/details/78218024

https://t.cn/AiRhTVdv
"""


import re
import os
import sys
import requests
import logging
import datetime
import aiohttp #表示http请求是异步方式去请求的
import asyncio #当异步请求返回时,通知异步操作完成

class ParseM3u8:
    base = ''       # 网站根目录
    step_size = 20  # 异步步长
    total_ts = 0    # 总ts数量
    current = 1     # 正在下载ts编号
    list_ts = []
    headers = {
        # 'Connection': 'keep - alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
    }

    def __init__(self, isRealM3u8 = True):
        self.isRealM3u8 = isRealM3u8

    # 设置异步步长
    def setStepSize(self, step_size):
        self.step_size = step_size

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

        # 解析m3u8
        self.parseM3u8(url)

        """
        # 一次下载所有ts文件
        tasks = [self.download(item) for item in self.list_ts]
        # 由于是异步请求,download(item)并不会被马上执行,只是占用了一个位置
        loop = asyncio.get_event_loop()  # loop的作用是——做完任务,事件通知
        loop.run_until_complete(asyncio.wait(tasks))
        loop.close()
        """

        self.total_ts = len(self.list_ts)
        step = int(self.total_ts / self.step_size) + 1
        loop = asyncio.get_event_loop()  #loop的作用是——做完任务,事件通知
        for i in range(0, self.total_ts, step):
            temp_size = self.current
            total_size = self.total_ts
            ################下载进度部分################
            done = int(50 * temp_size / total_size)
            # 调用标准输出刷新命令行，看到\r回车符了吧
            # 相当于把每一行重新刷新一遍
            sys.stdout.write("\r[%s%s] %d%%" % ('█' * done, ' ' * (50 - done), 100 * temp_size / total_size))
            sys.stdout.flush()

            list_step = self.list_ts[i: i + step]
            tasks = [self.download(item) for item in list_step]
            #由于是异步请求,download(item)并不会被马上执行,只是占用了一个位置
            loop.run_until_complete(asyncio.wait(tasks))
        loop.close()

        # 合并为mp4文件
        self.merge(download_path, filename)
        print(filename, "下载完成")

    def parseM3u8(self, url):
        # 根据实际情况修改(不同m3u8文件base截取方式可能不同)
        self.base = re.findall(r'(.*//.*?)/', url)[0]
        if(url[:5] != 'https'):
            self.base = url.rsplit("/", 1)[0] + "/"
            
        try:
            url_real = url
            # 得到真正的m3u8 url
            if not self.isRealM3u8:
                text_tem = requests.get(url, timeout=10).text  # 获取M3U8文件内容
                url_real = self.base + text_tem.split("\n")[2]
                # print("url_real: ", url_real)
                # 更新 base
                self.base = re.findall(r'(.*//.*?/)', url)
                if(url[:5] != 'https'):
                    self.base = url.rsplit("/", 1)[0] + "/"


            all_content = requests.get(url_real, timeout=10).text  # 获取第一层M3U8文件内容
            if "#EXTM3U" not in all_content:
                raise BaseException("非M3U8的链接")

            if "EXT-X-STREAM-INF" in all_content:  # 第一层
                file_line = all_content.split("\n")
                for line in file_line:
                    if '.m3u8' in line:
                        url = self.base + line     # 拼出第二层m3u8的URL
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

    async def download(self, name):
        file_name = re.findall('.*/(.*)', name)[0]
        # print(file_name, "正在下载……")
        try:
            # print("pd_url: ", name)
            # res = requests.get(name, headers = self.headers, timeout=15)
            # data = res.content

            async with aiohttp.request("GET", name, headers = self.headers) as res:
                data = await res.read()

            file_path = self.path + "\\" + file_name
            with open(file_path, "wb") as f:
                f.write(data)
                f.flush()

            res.close()
            self.current += 1
            # print(file_name, '下载成功')

        # 报错提示
        except Exception as e:
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
            # 重新下载
            async with self.download(name) as r:
                return

    def merge(self, path, filename):
        os.chdir(path)
        cmd = "copy /b * new.tmp"
        os.system(cmd)
        os.system('del /Q *.ts')
        os.system('del /Q *.mp4')
        os.rename("new.tmp", filename)
        os.system('cls')



if __name__ == '__main__':
    # url = "http://bili.let-1977cdn.com/20190818/FQRL7kuS/index.m3u8"              # 保存真正m3u8文件的m3u8文件
    url = "http://bili.let-1977cdn.com/20190818/FQRL7kuS/800kb/hls/index.m3u8"
    # url = "https://cn1.ruioushang.com/hls/20190908/eeb179af66aa56eb381d7f7edba0fcfb/1567926692/index.m3u8"
    filename = '第二集.mp4'
    pm = ParseM3u8()
    pm.start(url, filename)
