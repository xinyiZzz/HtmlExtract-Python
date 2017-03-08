#!/bin/bash
#-*-coding:utf-8-*-
'''
Name: 网页保存模块
Author：YunLong/XinYi 609610350@qq.com
Time：2016.4

输入：    例：[{'url': 'https://www.zhihu.com/','save_path': './zhihu',  'save_type': 'all'}]
            url             要下载的目标网页
            save_path       指定的保存路径
            save_type       all 默认保存网站全部信息， html为仅保存html文件
输出：    指定目录下存储网站文件

httrack常用参数：
    httrack  --near -%k -%B  -u2 -%u  网址  -N1001 -iC2 -r1 -T10 --retries 0 -J10240 --timeout 10 -R1 -H3 -O   指定目录
    --near 保存除了 .html外的扩展名文件 如 .css，.js，.png，.jpg等
    -%k  full query string
    -%B  tolerant requests (accept bogus responses on some servers, but not standard!)
    -u2 check document type if unknown (cgi,asp..) (u0 don't check, * u1 check but /, u2 check always)
    -%u url hacks: various hacks to limit duplicate URLs (strip //, www.foo.com==foo.com..) (--urlhack)
    -N1001  Identical to N1 exept that there is no "web" directory  网站保存的路径格式
    -iC2  网址更新，如果网址没有保存，添加无影响，如网站已经保存而未使用此参数，会进行交互式命令行验证
    -T10 设置连接超时 10s
    --retries 0  RN number of retries, in case of timeout or non-fatal errors (*R1) (--retries[=N])
    -J1024 速度不到1k/s的时候 放弃下载
    --timeout 10 timeout, number of seconds after a non-responding link is shutdown (--timeout)
    -R1 重试次数限制超限后是终止任务还是终止文件 待定？
    -H3 -H0 不终止任务 -H1 超时的时候终止任务 -H2 速度太慢的时候 -H3 速度太慢或者超时
    -O 指定下载路径
'''

import time
import os
import sys
import threading
import shutil
import json
from lxml import etree
from os.path import getsize as getsize
from os.path import join as pjoin
import copy
import beanstalkc
import re

from threadpool_spark import ThreadPoolSpark
sys.path.append('../html_extract')
from html_extract import get_title
sys.path.append('../server_base')
from utils import read_config_logging
logger = read_config_logging()


class WebSavestart():

    def __init__(self, pool_num=10):
        self.pool = ThreadPoolSpark(pool_num)
        self.task_result_list = []

    def generate_timestamp_dir_name(self):
        '''
        生成格式化当前时间, 例如: 2016-04-01_22-40-52
        '''
        return time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime(time.time()))

    def backup_website(self, backup_path):
        '''
        每次update一个网站，将原来的网站复制一份，以时间戳重新命名，留做备份,为了记录最新文件，将备份路径返回
        '''
        timestamp = self.generate_timestamp_dir_name()
        save_path = pjoin(backup_path, 'new')
        timestamp_path = pjoin(backup_path, timestamp)
        try:
            shutil.copytree(save_path, timestamp_path)
            return timestamp_path
        except Exception, e:
            logger['logger_file_error'].error('update copy error: %s', e)
            return False

    def count_resource_num(self, save_path):
        '''
        统计保存的网站的 images/目录下 js，css，pic(.jpg, .gif, .png), html_num 资源文件数
        '''
        pic_num = 0
        js_num = 0
        css_num = 0
        html_num = 0
        file_name_list = os.listdir(save_path)
        for file_name in file_name_list:
            if file_name.find('.htm') != -1:
                html_num += 1
        html_num = html_num - 2
        image_path = pjoin(save_path, 'images')
        if os.path.exists(image_path):
            file_name_list = os.listdir(image_path)
            for file_name in file_name_list:
                if file_name.find('.css') != -1:
                    css_num += 1
                elif file_name.find('.js') != -1:
                    js_num += 1
                elif file_name.find('.jpg') != -1 or file_name.find('.gif') != -1 or file_name.find('.png') != -1:
                    pic_num += 1
        return js_num, css_num, pic_num, html_num

    def update_task_list(self, task):
        '''
        多线程操作共享的类对象资源，互斥访问,将每个线程处理的url的保存结果存入 self.task_list
        每个线程处理的url的保存结果 为 {'url':xx, 'save_type':xx, 'save_path':xx, 'status':xx, 'js':xx,'pic':xx,'css':xx}
        '''
        if self.task_lock.acquire():
            self.task_result_list.append(task)
            self.task_lock.release()

    def is_exist_target_file(self, web_file_list, word):
        '''
        从文件名的列表中寻找是否存在 .html或者.htm的网页文件，找到则直接返回true
        '''
        for file_name in web_file_list:
            if file_name.find(word) != -1:
                return True
        return False

    def create_url_file(self, target_url, save_path):
        '''
        在保存网页的目录下创建url文件，文件中只存放保存网站的url
        '''
        file_name = pjoin(save_path, 'url_file')
        with open(file_name, 'w') as f:
            f.write(target_url)

    def change_html_name(self, top_index_file, web_file_path):
        '''
        操作httrack 保存网页的顶层目录的index.html文件，匹配出其要跳转的html文件，并将html文件名改为main.html
        如 ：<A HREF="web/mypage.html"> ,进入到web/下，将mypage.html 改名为 main.html
        '''
        with open(top_index_file) as f:
            content = f.read()
        tree = etree.HTML(content)
        href = tree.xpath(u"//a/@href")
        if href:
            page_name = href[0]
            page_name_old = pjoin(web_file_path, page_name)
            page_name_new = pjoin(web_file_path, 'main.html')
            if os.path.exists(page_name_old):
                os.rename(page_name_old, page_name_new)

    def check_save_status(self, target_url, save_path, save_type):
        '''
        保存完成后，判断网站是否成功保存,保存成功，将index-2.html 修改为 main.html，并返回 true，失败则返回false
        '''
        original_page_path = pjoin(save_path, 'index-2.html')
        new_page_path = pjoin(save_path, 'main.html')
        if os.path.exists(original_page_path):
            os.rename(original_page_path, new_page_path)
            return True
        # 如果 index.html 不存在，分两种情况，确实保存失败和 保存时未采用 /web/index.html格式
        else:
            if os.path.exists(save_path):
                web_file_list = os.listdir(save_path)
                top_index_file = pjoin(save_path, 'index.html')
                if len(web_file_list) > 1 and self.is_exist_target_file(web_file_list, 'htm') and os.path.exists(top_index_file):
                    self.change_html_name(top_index_file, save_path)
                    return True
                else:
                    # 对于保存失败的网站，将 url写入本地日志文件
                    logger['logger_file_info'].info(
                        "failed url: %s" % (target_url, ))
                    return False
            else:
                return False

    def judge_twice_url(self, save_path, save_type):
        '''
        根据指定的保存文件目录， 根据 title 和 mian.html文件大小来判断该网站是否存在跳页
        怀疑是否为跳转页面特征如下：
        1、title是否为 Page has moved
        2、页面htmml是否小于3KB
        '''
        page_path = pjoin(save_path, 'main.html')
        url_path = pjoin(save_path, 'url_file')
        with open(page_path, 'r') as f:
            content = f.read()
            title = get_title(content)
        if title == 'Page has moved' or getsize(page_path) <= 3072:
            with open(url_path, 'r') as f:
                url = f.read()
            redict_url = self.get_twice_page_url(content)
            # 保证是绝对路径
            if redict_url:
                if redict_url.find('http') != -1:
                    logger['logger_file_debug'].debug(
                        "redict_url: %s" % (redict_url, ))
                    self.re_download_twice_web(
                        redict_url, save_path, save_type)

    def get_twice_page_url(self, page_contents):
        '''
        从页面中提取出当前一级页面跳转的url
        '''
        feature_1 = u'<meta http-equiv="refresh".*?url=(.*?)">'
        there = re.compile(feature_1, re.I)
        m = there.search(page_contents)
        if m:
            return m.group(1)
        feature_2 = u'location.href="(.*?)";'
        there = re.compile(feature_2, re.I)
        m = there.search(page_contents)
        if m:
            return m.group(1)
        feature_3 = u'window.location="(.*?)";'
        there = re.compile(feature_3, re.I)
        m = there.search(page_contents)
        if m:
            return m.group(1)

    def re_download_twice_web(self, redict_url, save_path, save_type):
        '''
        重新发送指令下载二级页面，在当前线程中运行发送的指令
        '''
        try:
            if save_type == 'html':
                httrack_command = 'httrack -N1001 -iC2 -r1 -p1  --timeout 30 -R9 -O  ' + \
                    save_path + ' ' + redict_url
            else:
                httrack_command = 'httrack --near -%k -%B -N1001 -u2 -%u -iC2 -r1 --timeout 10 -T10 --retries 0 -J1024 -R1 -H3 -O  ' + \
                    save_path + ' ' + redict_url
            os.system(httrack_command)
        except Exception, e:
            logger['logger_file_error'].error('re_download save error: %s', e)
        self.check_save_status(redict_url, save_path, save_type)

    def read_log_file(self, log_file):
        '''
        (未使用，可加入log) 如果网页保存失败，提取httrack的保存日志中error部分
        '''
        with open(log_file) as f:
            log_content = f.read()
            error_content = log_content[log_content.find('Error:'):]
        return error_content

    def save_web_page(self, target_url, save_path, save_type):
        '''
        保存网页的执行函数，多线程执行
        '''
        backup_path = save_path
        save_path = pjoin(save_path, 'new')
        if not os.path.exists(backup_path):
            os.makedirs(backup_path)
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        try:
            if save_type == 'html':
                httrack_command = 'httrack -N1001 -iC2 -r1 -p1  --timeout 30 -R9 -O  ' + \
                    save_path + ' ' + target_url
            else:
                httrack_command = 'httrack --near -%k -%B -N1001 -u2 -%u -iC2 -r1 --timeout 10 -T10 --retries 0 -J1024 -R1 -H3 -O  ' + \
                    save_path + ' ' + target_url
            os.system(httrack_command)
            return True
        except Exception, e:
            logger['logger_file_error'].error('save error: %s', e)
        return False

    @staticmethod
    def handle_once_task(self, task):
        '''
        处理单个任务，进行网页保存并写入结果到task_result_list中
        '''
        task = copy.copy(task)
        if 'url' not in task or 'save_path' not in task or 'save_type' not in task:
            task['web_save_status'] = False
            logger['logger_file_debug'].debug(
                "task url or path error: %s", task)
        else:
            # 保存结束，未出错
            if self.save_web_page(task['url'], task['save_path'], task['save_type']) is True:
                # 保存成功，数据正确
                if self.check_save_status(task['url'], pjoin(task['save_path'], 'new'), task['save_type']) is True:
                    # 更新 save_path为带时间戳的网站路径
                    timestamp_path = self.backup_website(task['save_path'])
                    if timestamp_path is not False:  # 时间戳目录复制成功
                        self.create_url_file(task['url'], timestamp_path)
                        self.judge_twice_url(timestamp_path, task['save_type'])
                        js_num, css_num, pic_num, html_num = self.count_resource_num(
                            timestamp_path)
                        task['web_save_status'] = True
                        task['path'] = timestamp_path
                        resource_num = {}
                        resource_num['js_num'] = str(js_num)
                        resource_num['css_num'] = str(css_num)
                        resource_num['pic_num'] = str(pic_num)
                        resource_num['html_num'] = str(html_num)
                        task['web_save_resource_num'] = resource_num
                        logger['logger_file_debug'].debug(
                            "saved win url: %s, %s" % (task['url'], timestamp_path))
                    else:
                        task['web_save_status'] = False
                        logger['logger_file_debug'].debug(
                            "backup_website false url: %s, %s" % (task['url'], timestamp_path))
                else:
                    task['web_save_status'] = False
                    logger['logger_file_debug'].debug(
                        "check_save_status false url: %s, %s" % (task['url'], task['save_path']))
            else:
                task['web_save_status'] = False
                logger['logger_file_debug'].debug(
                    "save_web_page false url: %s, %s" % (task['url'], task['save_path']))
        self.update_task_list(task)

    def task_operate(self, task_list):
        '''
        网页保存的入口，启动线程池进行处理 task_list 为数组 [{url:xx,save_path:xx,'save_type': 'all'/'html'},{},...{}]
        例：[{'url': 'https://www.zhihu.com/','save_path': './zhihu', 'save_type': 'all'}]
        '''
        self.task_lock = threading.Lock()
        self.task_result_list = []
        for task in task_list:
            self.pool.run(func=self.handle_once_task,
                          args=(self, task))
        self.pool.wait()


if __name__ == '__main__':
    web = WebSavestart()
    task_list = [{'url': 'https://www.zhihu.com/',
                  'save_path': './zhihu', 'save_type': 'all'}]
    # task_list = [{'url':'http://016113.soufun.com','save_path':'./016113','task_type':'new'},{'url':'http://024fapiao.net','save_path':'./024fapiao','task_type':'new'},{'url':'http://033918.soufun.com','save_path':'./033918','task_type':'new'},{'url':'http://0419hgj.cn.alibaba.com/page/companyinfo.htm','save_path':'./0419hgj','task_type':'new'},{'url':'http://0502.sohu.com','save_path':'./0502','task_type':'new'},{'url':'http://0cr17ni4cu4nb.cn.alibaba.com','save_path':'./0cr17ni4cu4nb','task_type':'new'},{'url':'http://1.t.qq.com/qos.report.qq.com','save_path':'./qq','task_type':'new'},{'url':'http://100.asit.gov.cn','save_path':'./100','task_type':'new'},{'url':'http://1000.job1001.com','save_path':'./1000','task_type':'new'},{'url':'http://10086.cn/focus/roaming/international/cs/201004/t20100427_16140.htm','save_path':'./10086','task_type':'new'},{'url':'http://100w.tianya.cn','save_path':'./tianya','task_type':'new'},{'url':'http://102898788.qzone.qq.com','save_path':'./102898788','task_type':'new'},{'url':'http://107540.shop.pcpop.com','save_path':'./107540','task_type':'new'},{'url':'http://110.taobao.com/home/school.htm','save_path':'./taobao','task_type':'new'},{'url':'http://1110064.qidian.com','save_path':'./1110064','task_type':'new'}]
    web.task_operate(task_list)
