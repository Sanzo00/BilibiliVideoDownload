# !/usr/bin/python
# -*- coding:utf-8 -*-

import requests, time, hashlib, urllib.request, re, json
from moviepy.editor import *
import os, sys, threading
import imageio
imageio.plugins.ffmpeg.download()

S = threading.Semaphore(3)
currentPage = []
video = {}
targetPath = ''
Title = ''

currentPath = os.path.join(sys.path[0], 'bilibili_video')
if not os.path.exists(currentPath):
    os.makedirs(currentPath)

# 访问API地址
def get_play_list(start_url, bvid, cid, quality):
    # appkey = 'iVGUTjsxvpLeuDCf'
    # sec = 'aHRmhWMLkdeMuILqORnYZocwMBpMEOdt'
    # params = 'appkey=%s&cid=%s&otype=json&qn=%s&quality=%s&type=' % (appkey, cid, quality, quality)
    # chksum = hashlib.md5(bytes(params + sec, 'utf8')).hexdigest()
    # url_api = 'https://interface.bilibili.com/v2/playurl?%s&sign=%s' % (params, chksum)
    #
    # headers = {
    #     'Referer': start_url,
    #     'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
    # }
    # html = requests.get(url_api, headers=headers).json()
    # video_list = []
    # for i in html['durl']:
    #     video_list.append(i['url'])
    # return video_list

    url_api = 'https://api.bilibili.com/x/player/playurl?cid={}&bvid={}&qn={}'.format(cid, bvid, quality)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        'Cookie': 'SESSDATA=db32a219%2C1612575405%2C6b126*81', # 有效期1个月
        'Host': 'api.bilibili.com'
    }

    html = requests.get(url_api, headers=headers).json()
    data = html['data']
    video_list = []
    for i in data['durl']:
        video_list.append(i['url'])
    return video_list

# 下载视频
def Schedule_cmd(title, page):
    start_time = time.time()
    def Schedule(blocknum, blocksize, totalsize):
        recv_size = blocknum * blocksize

        speed = recv_size / (time.time() - start_time)
        speed_str = " Speed: %s/s" % format_size(speed)
        percent = recv_size / totalsize
        percent_str = "%.2f%%" % (percent * 100)
        n = round(percent * 50)

    return Schedule

# 字节bytes转化K\M\G
def format_size(bytes):
    KB = bytes / 1024
    M = KB / 1024;
    G = M / 1024;
    if M >= 1024:
        return '%.3fG' % (G)
    elif KB >= 1024:
        return '%.3fM' % (M)
    else:
        return '%.3fkB' % (KB)

#  下载视频
def down_video(video_list, title, start_url, page):
    S.acquire()
    num = 1
    for i in video_list:
        opener = urllib.request.build_opener()
        opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'),
            ('Accept', '*/*'),
            ('Accept-Language', 'en-US,en;q=0.5'),
            ('Accept-Encoding', 'gzip, deflate, br'),
            ('Range', 'bytes=0-'),  # Range 的值要为 bytes=0- 才能下载完整视频
            ('Referer', start_url),
            ('Origin', 'https://www.bilibili.com'),
            ('Connection', 'keep-alive'),
        ]
        urllib.request.install_opener(opener)
        reporthook = Schedule_cmd(title, page)
        currentPage.append(page)

        video_name = r'{}-{}.mp4'.format(title, num)
        if title not in video:
            video[title] = []
        video[title].append(video_name)

        print('P{} is downloading...'.format(page))

        urllib.request.urlretrieve(url=i, filename=os.path.join(currentPath, video_name),reporthook=reporthook)  # 写成mp4也行  title + '-' + num + '.flv'

        currentPage.remove(page)
        num += 1

        print('P{} has done.'.format(page))

    S.release()

# 合并视频
def combine_video(title_list):
    for title in title_list:
        current_video_path = os.path.join(currentPath ,title)
        if len(video[title]) == 1:
            src = os.path.join(currentPath, video[title][0])
            dst = os.path.join(targetPath, title+'.mp4')
            os.rename(src, dst)
        else:
            print('[正在合并视频...]:' + title)
            L = []
            for i in video[title]:
                filePath = os.path.join(currentPath, i)
                L.append(VideoFileClip(filePath))
            final_clip = concatenate_videoclips(L)
            final_clip.to_videofile(os.path.join(targetPath, r'{}.mp4'.format(title)), fps=30, remove_temp=True)
            print('[视频合并完成]' + title)

            for i in video[title]:
                filePath = os.path.join(currentPath, i)
                os.remove(filePath)

if __name__ == '__main__':

    start_time = time.time()
    # 解析视频链接
    start = input('请输入B站视频链接:')
    bvid = re.search(r'/BV([A-Za-z0-9]{10})/*', start).group(1)
    start_url = 'https://api.bilibili.com/x/web-interface/view?bvid=' + bvid

    print('1080p:80    720p:64    480p:32    360p:16')
    quality = input('请输入清晰度(80、64、32、16):')
    if quality not in ['80', '64', '32', '16']:
        quality = '80'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
    }
    print(start_url)
    html = requests.get(start_url, headers=headers).json()
    data = html['data']

    Title = re.sub(r'\/\\:*?"<>|', '', data['title'])
    targetPath = os.path.join(currentPath, Title)
    if not os.path.exists(targetPath):
        os.makedirs(targetPath)

    page_list = []
    if '?p=' in start: # 单p
        p = re.search(r'\?p=(\d+)',start).group(1)
        page_list.append(data['pages'][int(p) - 1])
    else: # 多p
        page_list = data['pages']

    threadpool = []
    title_list = []

    for i, item in enumerate(page_list):
        cid = str(item['cid'])
        title = item['part']
        title = re.sub(r'\/\\:*?"<>|', '', title)
        if len(page_list) == 1:
            title = Title
        title_list.append(title)

        page = str(item['page'])
        cur_url = start_url + "/?p=" + page
        video_list = get_play_list(cur_url, bvid, cid, quality)

        thr = threading.Thread(target=down_video, args=(video_list, title, cur_url, page))
        threadpool.append(thr)
        s = ('#' * round(i/len(page_list)*50)).ljust(50, '-')
        print('加载视频cid:[{}] {}/{}\r'.format(s,i,len(page_list)), end='')
    print('加载视频cid:[{}] {}/{}\r'.format('#'*50, len(page_list), len(page_list)))

    for thr in threadpool:
        thr.start()

    for thr in threadpool:
        thr.join()

    combine_video(title_list)

    end_time = time.time()
    seconds = (end_time - start_time) % 60;
    minutes = (end_time - start_time) // 60;
    print('下载完成，耗时%d分%.1f秒' % (minutes, seconds))

    # windows打开下载目录
    if (sys.platform.startswith('win')):
        os.startfile(targetPath)
