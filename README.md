# video_download

​	本项目支持下载的[网站](https://t.cn/AiRhTVdv)，只要修改**config.init**配置文件里里面的**m3u8文件的url**和最后保存的**文件名称filename**，即可下载自己想要下载的视频，有三种读取模式 0-默认 1-input输入 2-配置文件读取，项目核心代码在**ParseM3u8.py**里，另外项目支持**断线重连**，只要代码还在运行网络好转后会继续下载



双击**run.bat**文件即可下载 罗小黑战记大电影



**ParseM3u8.exe**是我已经静态编译的文件，与**config.ini**文件一起使用，你也可以运行install.bat编译自己修改的ParseM3u8.py文件