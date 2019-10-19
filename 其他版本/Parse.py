# -*- coding:utf-8 -*-  
import os
import sys
import requests
import time
import datetime
import importlib
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex
 
importlib.reload(sys)

class Download:
	headers = {
		# 'Connection': 'keep - alive',
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
	}

	def download(self, url, filename):
		download_path = os.getcwd() + "\download"
		if not os.path.exists(download_path):
			os.mkdir(download_path)
			
		#新建日期文件夹
		download_path = os.path.join(download_path, datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
		#print download_path
		os.mkdir(download_path)

		# 得到真正的m3u8 url
		text_tem = requests.get(url).text  # 获取M3U8文件内容 
		url_real = url.rsplit("/", 3)[0] + text_tem.split("\n")[2]
		print("url_real: ", url_real)
			
		all_content = requests.get(url_real).text  # 获取第一层M3U8文件内容
		if "#EXTM3U" not in all_content:
			raise BaseException("非M3U8的链接")
	 
		if "EXT-X-STREAM-INF" in all_content:  # 第一层
			file_line = all_content.split("\n")
			for line in file_line:
				if '.m3u8' in line:
					url = url.rsplit("/", 1)[0] + "/" + line # 拼出第二层m3u8的URL
					all_content = requests.get(url).text
	 
		file_line = all_content.split("\n")
	 
		unknow = True
		key = ""
		for index, line in enumerate(file_line): # 第二层
			if "#EXT-X-KEY" in line:  # 找解密Key
				method_pos = line.find("METHOD")
				comma_pos = line.find(",")
				method = line[method_pos:comma_pos].split('=')[1]
				print("Decode Method：", method)
				
				uri_pos = line.find("URI")
				quotation_mark_pos = line.rfind('"')
				key_path = line[uri_pos:quotation_mark_pos].split('"')[1]
				
				key_url = url.rsplit("/", 1)[0] + key_path # 拼出key解密密钥URL
				res = requests.get(key_url)
				key = res.content
				print("key：" , key)
				
			if "EXTINF" in line: # 找ts地址并下载
				unknow = False
				pd_url = url.rsplit("/", 3)[0] + file_line[index + 1] # 拼出ts片段的URL
				c_fule_name = file_line[index + 1].rsplit("/", 1)[-1]
				self.download_ts(key, pd_url, c_fule_name, download_path)

		if unknow:
			raise BaseException("未找到对应的下载链接")
		else:
			print("下载完成")
		self.merge_file(download_path, filename)
	 
	
	def download_ts(self, key, url, c_fule_name, download_path):
		try:
			print(url, "正在下载...")
			res = requests.get(url, headers = self.headers, timeout = 15)
			if len(key): # AES 解密
				cryptor = AES.new(key, AES.MODE_CBC, key)
				with open(os.path.join(download_path, c_fule_name + ".mp4"), 'ab') as f:
					f.write(cryptor.decrypt(res.content))
			else:
				with open(os.path.join(download_path, c_fule_name), 'ab') as f:
					f.write(res.content)
					f.flush()	
				"""
				content = res.content
				with open(download_path + "\\" + c_fule_name, 'wb')as f:
					f.write(content)
				"""	
		except Exception as e:
			print(e)
			print("Connection refused by the server..")
			print("Let me sleep for 5 seconds")
			time.sleep(5)
			print("Was a nice sleep, now let me continue...")
			return self.download_ts(key, url, c_fule_name, download_path)

	def merge_file(self, path, filename):
		os.chdir(path)
		cmd = "copy /b * new.tmp"
		os.system(cmd)
		os.system('del /Q *.ts')
		os.system('del /Q *.mp4')
		os.rename("new.tmp", filename)
    
if __name__ == '__main__': 
	d = Download()
	url = "http://bili.let-1977cdn.com/20190818/41VtSLrR/index.m3u8"
	filename = "第一集.mp4"
	d.download(url, filename)
	# pm.merge_file(r"I:\PythonWorkSpace\video_download\download\temp", filename)
	
