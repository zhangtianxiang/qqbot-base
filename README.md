# qqbot-base

## 插件约定

插件应该直接放入plugins目录下，支持文件或文件夹的方式。

格式如下，包括单个文件的`ppy`和文件夹形式的`weibo_forwarder`两个插件：

```
plugins
|   .gitignore
|   ppy.py
|
+---ppy
|       new_ranked.json
|
\---weibo_forwarder
    |   __init__.py
    |
    \---data
            follow.json
            record.json
```

其中插件的数据应当存在插件名对应的文件夹下，该目录可以通过`util.plugin_dir(__file__)`获取。需要注意这个函数通过判断`__file__`是否为`__init__.py`来解析的，应该在类似于如上所示的`ppy.py`与`__init__.py`两类位置中使用，而非其它文件。因此，建议在初始化插件时便将其存储下来。

这里更推荐`weibo_forwarder`形式的插件，这样也便于维护成单独的`git`。

## 配置

见`config.py`，其中包含nonebot本身的配置和本框架需要的配置。

## 依赖

见`requirements.txt`，使用`pipreqs ./ --encoding=utf8`生成依赖。
