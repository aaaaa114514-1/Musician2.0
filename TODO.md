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
- 非法的连写命令将被指出

### 重构设置功能

+ 重构 `savedata.txt` 文件为 `settings.json` 文件
+ 增加 `set` 语句，支持应用内展示配置、修改配置（带合法性校验）

### 增加存储常用指令功能

+ 增加 `common_commands.json` 文件，存储常用指令
+ 常用指令可以在打开应用后直接通过上/下键直接选择
+ 增加 `common` 语句，支持应用内查看、增删常用指令

### 增加 `timelimit` 播放到固定时间功能

+ 重构了 `timelimit` 处理代码

+ 增加支持 `timelimit 14:15` 或 `timelimit 23:59:59` 的功能，自动播放直到下一次到达指定的时刻

### 增加歌曲 Tag 功能，重构存储逻辑

+ 增加tags.json存储每首歌的tag
+ 替代了原本的 Lis 目录逻辑，而是使用指定tag来播放音乐
+ 标签必须是由大小写敏感的字母、数字（可以没有）、下划线（可以没有）组成的，不能纯数字
+ `tag` 标签
  + `tag` 列出所有标签和标签下的曲目数量
  + `tag -l` 列出所有标签和标签下的曲目
  + `tag test` 列出标签 `test` 下的所有曲目
  + `tag -a test 1-4 6` 把当前目录下的第1-4、6首曲子打上标签 `test`
  + `tag -d test` 删除标签 `test` ，洗脱所有曲目的这个标签
  + `tag -d test 2-3 7` 把带 `test` 标签的低2-3、7首曲子洗脱 `test` 标签

+ `play` 新增内容
  + `play test` 播放 `test` 中的曲目（这里的 `test` 可以按照任意顺序传入参数）
+ `showlist` 新增内容
  + `showlist test` 列出标签 `test` 下的所有曲目
+ `save` 语法重构
  + `save` 把 `savelist` 中的歌曲保存到曲库目录
  + `save test1 test2` 把 `savelist` 中的歌曲保存到曲库目录，并把这些歌曲统一打上 `test1` `test2` 标签

## 待修改

+ 增加歌曲Tag功能，以Tag代替Lis目录功能，，支持play <tag> 选择功能，支持showlist 展示每首歌的tag
+ showlist 增加展示指定目录下所有文件功能（默认为Lis目录）
+ （尝试增加showlist显示歌曲长度功能，如果会导致延迟就改为 showlist -t 显示）
+ 重构 history 指令的展示面板
+ 修Kugou音乐的爬虫
+ 使用安装包安装
+ 添加心动模式，采用评价系统打分推荐















