# plugins/weibo_forwarder/__init__.py
# data save to: data/weibo_forwarder/*

__plugin_name__ = '微博转发'
__plugin_usage__ = r"""
自动转发已关注列表的最新微博消息，更新频率为5分钟一次

支持指令：
weibo_show_list 查看已关注列表
weibo_list_add 添加关注
weibo_list_del 删除关注
"""

'''
notes: container id 是否会改变？
正则表达式是否需要编译
'''

import os
from os import path
import re
import requests
import json

import nonebot
from nonebot import on_command, CommandSession, logger, argparse

BASE_DIR = path.join('data', 'weibo_forwarder')
FILE_FOLLOW = path.join(BASE_DIR, 'follow.json')
RE_GET_TEXT = re.compile(r'\s|\n|<.*?>', re.S)

'''
follow_list:
{
    {
        'nickname': XXX,
        'uid': XXX,
        'last_update': XXX,
    },
    {
        XXX
    },
    ...
}
'''


class Singleton(object):  # 单例
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            orig = super(Singleton, cls)
            cls._instance = orig.__new__(cls, *args, **kwargs)
        return cls._instance


class FollowManager(Singleton):
    __follow_list = None

    def __init__(self):
        # 创建目录
        if not path.isdir(BASE_DIR):
            os.mkdir(BASE_DIR)
        # 创建follow_list.json
        if not path.isfile(FILE_FOLLOW):
            with open(FILE_FOLLOW, 'w') as f:
                f.write('{}')  # 空字典
        try:
            with open(FILE_FOLLOW, 'r') as f:
                obj = json.loads(f.read())
        except Exception as e:
            logger.error('file is not a json, rewriting')
            with open(FILE_FOLLOW, 'w') as f:
                f.write('{}')

        with open(FILE_FOLLOW, 'r') as f:
            self.__follow_list = json.loads(f.read())

    async def __save_data(self):
        with open(FILE_FOLLOW, 'w') as f:
            f.write(json.dumps(self.__follow_list))

    async def add_follow(self, group_id, person):
        following = self.__follow_list.setdefault(group_id, [])
        following.append(person.copy())
        await self.__save_data()

    async def del_follow(self, group_id, person):
        if person == None:
            return
        following = self.__follow_list.get(group_id)
        if following == None:
            return
        following.remove(person)
        await self.__save_data()

    def get_follow_list(self, group_id):
        following = self.__follow_list.get(group_id)
        if following == None:
            return []
        return following.copy()

    def get_person_by_uid(self, group_id, uid):
        following = self.__follow_list.get(group_id)
        if following == None:
            return None
        for person in following:
            if person['uid'] == uid:
                return person.copy()  # 不允许外部修改，所以返回copy
        return None

    def get_person_by_nickname(self, group_id, nickname):
        following = self.__follow_list.get(group_id)
        if following == None:
            return None
        for person in following:
            if person['nickname'] == nickname:
                return person.copy()
        return None


follow_manager = FollowManager()


def GET_home_page_by_uid(uid):
    # cost time, should await
    url_home_page = 'https://m.weibo.cn/api/container/getIndex?type=uid&value='+uid
    rsp_home_page = requests.get(url_home_page)
    home_page = rsp_home_page.json()
    return home_page


async def get_user_info_by_uid(uid):
    home_page = GET_home_page_by_uid(uid)
    return home_page['data']['userInfo']


async def get_tab_by_uid_key(uid, tab_key):
    home_page = GET_home_page_by_uid(uid)
    for tab in home_page['data']['tabsInfo']['tabs']:
        if tab['tabKey'] == tab_key:
            return tab
    return None


async def get_nickname_by_uid(uid):
    user_info = await get_user_info_by_uid(uid)
    return user_info['screen_name']


def GET_search_page_by_nickname(nickname):
    # cost time, shold await
    url_search_page = 'https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D3%26q%3D' + \
        nickname+'&page_type=searchall'
    rsp_search_page = requests.get(url_search_page)
    search_page = rsp_search_page.json()
    return search_page


async def get_user_by_nickname(nickname):
    search_page = GET_search_page_by_nickname(nickname)
    for card_outer in search_page['data']['cards']:
        if card_outer['card_type'] == 11:
            for card in card_outer['card_group']:
                if card['card_type'] == 10:
                    user = card['user']
                    if user['screen_name'] == nickname:
                        # found
                        user['desc1'] = card['desc1']
                        user['desc2'] = card['desc2']
                        return user
    return None


async def get_uid_by_nickname(nickname):
    # return str
    user = await get_user_by_nickname(nickname)
    return str(user['id'])


@on_command('weibo_show_list', aliases=('微博关注', '微博关注列表'), only_to_me=False)
async def weibo_show_list(session: CommandSession):
    # 确保是群消息
    post_type = session.ctx.get('post_type', '')
    message_type = session.ctx.get('message_type', '')
    if post_type != 'message' or message_type != 'group':
        await session.send('该功能需要在群中使用')
        return
    # 确保群号存在
    group_id = str(session.ctx.get('group_id', ''))
    if group_id == '':
        await session.send('获取群号失败')
        return
    following = follow_manager.get_follow_list(group_id)
    reply = ''
    if len(following) > 0:
        reply = '关注列表：'
        for person in following:
            reply += '\n'+person['nickname']
    else:
        reply = '关注列表为空'

    await session.send(reply)


@on_command('weibo_list_add', aliases=('添加微博关注'), only_to_me=False, shell_like=True)
async def weibo_list_add(session: CommandSession):
    USAGE = '''添加微博关注，uid或nickname至少输入一种，优先使用uid

使用方法：
!weibo_list_add [OPTIONS]

OPTIONS：
-h, --help
  显示本使用帮助
-u UID, --uid UID
  输入要关注用户的uid
-n NICKNAME, --nickname NICKNAME
  输入要关注用户的昵称
'''
    # 确保是群消息
    post_type = session.ctx.get('post_type', '')
    message_type = session.ctx.get('message_type', '')
    if post_type != 'message' or message_type != 'group':
        await session.send('该功能需要在群中使用')
        return
    # 确保是管理员进行设置
    role = session.ctx.get('sender', {}).get('role', 'member')
    if role != 'owner' and role != 'admin':
        await session.send('只能由群主或管理员进行设置，你的角色'+role)
        return
    # 确保群号存在
    group_id = str(session.ctx.get('group_id', ''))
    if group_id == '':
        await session.send('获取群号失败')
        return
    # 获取参数
    person = {
        'uid': '',
        'nickname': ''
    }
    parser = argparse.ArgumentParser(session=session, usage=USAGE)
    parser.add_argument('-u', '--uid', type=str, default='', required=False)
    parser.add_argument('-n', '--nickname', type=str,
                        default='', required=False)
    args = parser.parse_args(session.argv)
    if args.uid != '':  # 存在uid，根据uid获取用户昵称
        person['uid'] = args.uid
        person['nickname'] = await get_nickname_by_uid(args.uid)
    elif args.nickname != '':  # 存在nickname，根据昵称搜索出uid并记录
        person['nickname'] = args.nickname
        person['uid'] = await get_uid_by_nickname(args.nickname)
    else:  # error
        await session.send('请输入uid或nickname，请使用 --help 参数查询使用帮助')
        return

    await follow_manager.add_follow(group_id, person)
    await session.send('已添加:\n昵称:'+person['nickname']+'\n'+'uid:'+person['uid'])


@on_command('weibo_list_del', aliases=('取消微博关注'), only_to_me=False, shell_like=True)
async def weibo_list_del(session: CommandSession):
    USAGE = '''取消微博关注，uid或nickname至少输入一种，优先使用uid

使用方法：
!weibo_list_del [OPTIONS]

OPTIONS：
-h, --help
  显示本使用帮助
-u UID, --uid UID
  输入要取消关注用户的uid
-n NICKNAME, --nickname NICKNAME
  输入要取消关注用户的昵称
'''
    # 确保是群消息
    post_type = session.ctx.get('post_type', '')
    message_type = session.ctx.get('message_type', '')
    if post_type != 'message' or message_type != 'group':
        await session.send('该功能需要在群中使用')
        return
    # 确保是管理员进行设置
    role = session.ctx.get('sender', {}).get('role', 'member')
    if role != 'owner' and role != 'admin':
        await session.send('只能由群主或管理员进行设置，你的角色'+role)
        return
    # 确保群号存在
    group_id = str(session.ctx.get('group_id', ''))
    if group_id == '':
        await session.send('获取群号失败')
        return
    # 获取参数
    parser = argparse.ArgumentParser(session=session, usage=USAGE)
    parser.add_argument('-u', '--uid', type=str, default='', required=False)
    parser.add_argument('-n', '--nickname', type=str,
                        default='', required=False)
    args = parser.parse_args(session.argv)

    person = None
    if args.uid != '':
        person = follow_manager.get_person_by_uid(group_id, args.uid)
    elif args.nickname != '':
        person = follow_manager.get_person_by_nickname(group_id, args.nickname)
    else:  # error
        await session.send('请输入uid或nickname，请使用 --help 参数查询使用帮助')
        return

    if person == None:
        await session.send('没有找到对应的账号')
        return
    await follow_manager.del_follow(group_id, person)
    await session.send('已删除:\n昵称:'+person['nickname']+'\n'+'uid:'+person['uid'])


@on_command('weibotest', only_to_me=False)
async def weibotest(session: CommandSession):
    uid = '6204112864'  # 孤影
    reply = ''
    try:
        tab = await get_tab_by_uid_key(uid, 'weibo')
        container_id = tab['containerid']

        page0 = 'https://m.weibo.cn/api/container/getIndex?type=uid&value=' + \
            uid+'&containerid='+container_id+'&page=0'

        rsp_page0 = requests.get(page0)
        page0 = rsp_page0.json()
        cards = page0['data']['cards']

        # 将匹配到的内容用空替换，即去除匹配的内容，只留下文本
        for card in cards:
            if card['card_type'] != 9:
                continue
            link = card['scheme']
            create_time = card['mblog']['created_at']
            content = card['mblog']['text']
            content = RE_GET_TEXT.sub('', content)
            print(create_time+'\n')
            print(content+'\n\n')
            reply += create_time+'\n'
            reply += content+'\n'
            reply += link+'\n'
    except Exception as e:
        await session.send('error: ' + str(e))
        raise e

    await session.send(reply)
