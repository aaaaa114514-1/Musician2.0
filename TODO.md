# TODO-List

## 一键完成编译

```bash
pyinstaller --onefile --noconsole --icon=Icon.ico main.py --name musician
```

## 已经完成的修改

### 重构代码为多文件

```bash
musician_project/
├── core/
│   ├── __init__.py
│   ├── player.py       # player 类和后台检查线程
│   └── history.py      # 历史记录管理
├── services/
│   ├── __init__.py
│   ├── kugou.py        # 酷狗搜索与下载
│   └── netease.py      # 网易云缓存解密
├── utils/
│   ├── __init__.py
│   ├── file_utils.py    # 文件名转换、MP3转换
│   └── search_utils.py  # 模糊匹配
├── ui/
│   ├── __init__.py
│   └── handlers.py     # 所有的 handle_xxx 函数
└── main.py             # 主程序循环
```

### 支持原来指令基础上，增加简化连写命令

- `play -m` Mode:
  - `play -m s`: 切换到单曲循环并开始
  - `play -m c`: 切换到列表循环并开始
  - `play -m r`: 切换到随机播放并开始
- `play -v` Volume:
  - `play -v 50`: 播放的同时将音量设为 50%
- `play -t` Timelimit:
  - `play -t 60`: 播放的同时设置 60 分钟后自动停止
- `<Command> -h` Help:
  - `timelimit -h`: 展示指令 `timelimit` 的用法

## 待修改

+ （尝试增加储存常用指令，快捷调用功能）
+ 重构settings配置文件格式为.json，增加 set 语句，实现应用内调配置功能

+ 增加歌曲Tag功能，以Tag代替Lis目录功能，增加tags.json存储所有tag和每首歌的tag，支持play <tag> 选择功能，支持showlist 展示每首歌的tag
+ showlist 增加展示指定目录下所有文件功能（默认为Lis目录）
+ （尝试增加showlist显示歌曲长度功能，如果会导致延迟就改为 showlist -t 显示）
+ timelimit 增加播放到固定时间功能

+ 修Kugou音乐的爬虫
+ 使用安装包安装

+ 添加心动模式，采用评价系统打分推荐









