import re
import os
import sys
import requests
import logging
import datetime
import aiohttp #表示http请求是异步方式去请求的
import asyncio #当异步请求返回时,通知异步操作完成
import configparser

class ParseM3u8:
    base = ''           # 网站根目录
    step_size = 20      # 异步步长
    total_ts = 0        # 总ts数量
    current = 1         # 正在下载ts编号
    isRealM3u8 = True   # 是否是真正的m3u8链接
    savePath = 'default'
    list_ts = []
    headers = {
        # 'Connection': 'keep - alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
    }

    # 设置是否是真正的m3u8链接
    def setIsRealM3u8(self, isRealM3u8 = True):
        self.isRealM3u8 = isRealM3u8

    # 设置异步步长
    def setStepSize(self, step_size):
        self.step_size = step_size

    # 设置保存路径
    def setSavePath(self, savePath):
        self.savePath = savePath

    # 功能：失败提示，失败重试，失败记录日志，线程池提高并发，超时重试。
    def start(self, url, filename):
        if '/' not in self.savePath and '\\' not in self.savePath:
            download_path = os.getcwd() + "\\" + self.savePath
            self.savePath = download_path
        else:
            download_path = self.savePath
        if not os.path.exists(download_path):
            os.mkdir(download_path)

        #新建日期文件夹
        download_path = os.path.join(download_path, datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
        os.mkdir(download_path)
        self.path = download_path

        # 解析m3u8
        self.parseM3u8(url)

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
                # 更新 base
                self.base = url.rsplit("/", 1)[0]
                if(re.findall(r'.*?//(.*?)//', url) != []):
                    self.base = url.rsplit("//", 1)[0]
                str_tem = text_tem.split("\n")[2]
                # 默认self.base不是以'/'结尾，如果str_tem[0]没有以'/'开头则self.base以'/'结尾
                self.base = self.base if(str_tem[0] == '/') else (self.base + '/')
                url_real = self.base + str_tem

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
                self.list_ts.append(item)
            print(len(self.list_ts), "个url解析完成")
        except Exception as e:
            return self.parseM3u8(url)

    async def download(self, name):
        file_name = re.findall('.*/(.*)', name)[0]
        try:
            async with aiohttp.request("GET", name, headers = self.headers) as res:
                data = await res.read()

            file_path = self.path + "\\" + file_name
            with open(file_path, "wb") as f:
                f.write(data)
                f.flush()

            res.close()
            self.current += 1

        # 报错提示
        except Exception as e:
            # 记录日志
            """
            my_log = logging.getLogger('lo')
            my_log.setLevel(logging.DEBUG)
            file = logging.FileHandler('error.log', encoding='utf-8')
            file.setLevel(logging.ERROR)
            my_log_fmt = logging.Formatter('%(asctime)s-%(levelname)s:%(message)s')
            file.setFormatter(my_log_fmt)
            my_log.addHandler(file)
            my_log.error(file_name + '下载失败 ')
            my_log.error(e)
            """

            # 重新下载
            async with self.download(name) as r:
                return

    def merge(self, path, filename):
        os.chdir(path)
        cmd = "copy /b * new.tmp"
        os.system(cmd)
        os.system('del /Q *.ts')
        os.system('del /Q *.mp4')
        os.system('del /Q *.mp4')
        os.rename("new.tmp", filename)
        cmd_copy = "copy " + filename + " " + self.savePath
        os.system(cmd_copy)
        os.remove(filename)
        os.chdir(os.path.abspath(os.path.dirname(os.getcwd())))
        os.rmdir(path)
        os.system('cls')



if __name__ == '__main__':
    cf = configparser.ConfigParser()
    cf.read(r".\config.ini", encoding="utf-8-sig")

    # url = "http://bili.let-1977cdn.com/20190818/FQRL7kuS/index.m3u8"              # 保存真正m3u8文件的m3u8文件
    # url = "http://bili.let-1977cdn.com/20190818/FQRL7kuS/800kb/hls/index.m3u8"
    url = "https://cn1.ruioushang.com/hls/20190908/eeb179af66aa56eb381d7f7edba0fcfb/1567926692/index.m3u8"
    filename = '罗小黑战记大电影.mp4'
    speed = 20
    isRealM3u8 = True

    type = cf.getint("Mode", "type")
    speed = int(cf.get("Download", "speed"))
    savePath = cf.get("Download", "savePath")
    isRealM3u8 = False if (cf.get("Download", "isRealM3u8") == 'False') else True
    if type == 1:
        url = cf.get("Download", "url")
        filename = cf.get("Download", "filename") + ".mp4"
    else:
        print("请输入m3u8文件url: ")
        url = input()
        print("请输入保存文件名称: ")
        filename = input() + ".mp4"
    
    print(filename, '正在下载...')
    pm = ParseM3u8()
    pm.setStepSize(speed)
    pm.setSavePath(savePath)
    pm.setIsRealM3u8(isRealM3u8)
    pm.start(url, filename)