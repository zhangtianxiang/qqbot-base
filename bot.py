from os import path

import nonebot
from nonebot import on_command, CommandSession

import config


@on_command('help', aliases=['使用帮助', '帮助', '使用方法'], only_to_me=False)
async def help(session: CommandSession):
    # 获取设置了名称的插件列表
    plugins = list(filter(lambda p: p.name, nonebot.get_loaded_plugins()))

    arg = session.current_arg_text.strip().lower()
    if not arg:
        # 如果用户没有发送参数，则发送功能列表
        await session.send('我现在支持的功能有：\n\n' + ''.join(p.name for p in plugins))
    else:
        # 如果发了参数则发送相应命令的使用帮助
        for p in plugins:
            if p.name.lower() == arg:
                await session.send(p.usage)
                return
        await session.send('未找到该插件')


if __name__ == '__main__':
    nonebot.init(config)
    nonebot.load_plugins(
        path.join(path.dirname(__file__), 'plugins'),
        'plugins'
    )
    nonebot.run()
