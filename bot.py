from os import path

import nonebot
from nonebot import on_command, CommandSession

import config


@on_command('help', aliases=['usage'], only_to_me=False)
async def help(session: CommandSession):
    plugins = list(filter(lambda p: p.name, nonebot.get_loaded_plugins()))

    arg = session.current_arg_text.strip().lower()
    if not arg:
        await session.send('现在支持的功能有：\n' + '\n'.join(p.name for p in plugins) + '\n使用 !help <功能> 查看详细信息')
    else:
        for p in plugins:
            if p.name.lower() == arg:
                await session.send(p.usage)
                return
        await session.send('未找到该插件')


if __name__ == '__main__':
    nonebot.init(config)
    nonebot.load_plugins(
        path.join(path.dirname(__file__), 'plugins'), 'plugins')
    nonebot.run()
