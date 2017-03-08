# !/usr/bin/python
#-*-coding:utf-8-*-

'''
Name: 抽取HTML中所有文本、中文、关键词、Title、ICP、链接及内外链比例、form表单、alert、meta、跳转、敏感词等信息
Author：XinYi 609610350@qq.com
Time：2016.4
'''

import codecs
import sys
import re
import chardet
import warnings
from lxml import etree
from os.path import join as pjoin
import os
from bs4 import BeautifulSoup

from jieba_call import jieba_textrank, jieba_POS_tagging, jieba_tfidf


reload(sys)
sys.setdefaultencoding('utf8')
warnings.filterwarnings('ignore', '.*', Warning, 'chardet')

_PATH = os.path.abspath('.')
RED_KEYWORDS = ["account", "admin", "administrator",
                "auth", "bank", "client", "confirm", "email", "host",
                "password", "pay", "private", "safe", "secure", "security",
                "sign", "user", "validation", "verification", "icbc"]
PATH_KEYWORDS = ["www", "net", "com", "cn"]


def utf8_open_file(file_path):
    '''
    以utf8格式打开文件
    '''
    try:
        content = codecs.open(file_path, 'r', 'utf-8').read()
    except:
        content = codecs.open(file_path, 'r').read()
    return content


def utf8_transfer(strs):
    '''
    utf8编码转换
    '''
    try:
        if isinstance(strs, unicode):
            strs = strs.encode('utf-8')
        elif chardet.detect(strs)['encoding'] == 'GB2312':
            strs = strs.decode("gb2312", 'ignore').encode('utf-8')
        elif chardet.detect(strs)['encoding'] == 'utf-8':
            strs = strs.decode('utf-8', 'ignore').encode('utf-8')
    except Exception, e:
        print 'utf8_transfer error', strs, e
    return strs


def replace_InvalidTag(Html):
    '''
    替换HTML中的无效标签
    '''
    re_cdata = re.compile('//<!\[CDATA\[[^>]*//\]\]>', re.I)  # 匹配CDATA
    Html = re_cdata.sub('', Html)
    re_cdata = re.compile('<!\[CDATA\[[^>]*//\]\]>', re.I)  # 匹配CDATA
    Html = re_cdata.sub('', Html)
    re_br = re.compile('<br\s*?/?>')  # 处理换行
    Html = re_br.sub('\n', Html)
    space_line = re.compile('\s+')  # 去掉多余的空行
    Html = space_line.sub('', Html)
    re_comment = re.compile('<!--[^>]*-->')  # 去掉HTML注释
    Html = re_comment.sub('', Html)
    re_style = re.compile('<style\s*[^>]*>(.*?)</style\s*>')
    Html = re_style.sub('', Html)
    re_script = re.compile('<script\s*[^>]*>(.*?)</script>')
    Html = re_script.sub('', Html)
    re_h = re.compile('</?[^>]*>')  # 处理html标签
    Html = re_h.sub('', Html)
    return Html


def replace_CharEntity(Html):
    '''
    替换常用HTML字符实体, 使用正常的字符替换HTML中特殊的字符实体
    '''
    CHAR_ENTITIES = {'nbsp': ' ', '160': ' ',
                     'lt': '<', '60': '<',
                     'gt': '>', '62': '>',
                     'amp': '&', '38': '&',
                     'quot': '"', '34': '"', }
    re_charEntity = re.compile(r'&#?(?P<name>\w+);')
    sz = re_charEntity.search(Html)
    while sz:
        key = sz.group('name')  # 去除&后d的entity,如&gt;为gt
        try:
            Html = re_charEntity.sub(CHAR_ENTITIES[key], Html, 1)
            sz = re_charEntity.search(Html)
        except KeyError:
            # 以空串代替
            Html = re_charEntity.sub('', Html, 1)
            sz = re_charEntity.search(Html)
    return Html


def html_filter(Html):
    '''
    对html过滤无效标签和字符实体
    '''
    Html = replace_InvalidTag(Html)
    Html = replace_CharEntity(Html)
    # Html = Html.replace(" ", "")
    return Html


def match_chinese(Html, punc=True):
    '''
    punc为True时抽取html中所有的中文和标点符号
    punc为False时只抽取中文
    '''
    Html = Html.decode('utf8')
    Html_zh = ''
    if punc == True:
        pattern = re.compile(u"[\u4e00-\u9fff，。、；！：（）“《》？”]+")
    else:
        pattern = re.compile(u"[\u4e00-\u9fff]+")
    results = pattern.findall(Html)
    for result in results:
        if result != ' ':
            Html_zh += result.strip() + ' '
    return Html_zh


def zh_check(data):
    '''
    判断data中是否含有中文
    '''
    data = utf8_transfer(data).decode('utf-8')
    re_script = re.compile(u'[\u4e00-\u9fa5]+')
    return 1 if re_script.search(data) else 0


def get_html_keyword(Html):
    '''
    用textrank抽取HTML中关键字
    '''
    if not zh_check(Html):  # jieba自带的textrank无法处理英文，所以用tfidf，但无法过滤词性
        Html = html_filter(Html)
        return jieba_tfidf(Html, allowPOS=())
    Html = html_filter(Html)
    Html = utf8_transfer(Html)
    return jieba_textrank(Html)


def get_html_keyword_tfidf(Html):
    '''
    用tfidf抽取HTML中关键字
    '''
    Html = html_filter(Html)
    Html = utf8_transfer(Html)
    return jieba_tfidf(Html)


def get_title(Html):
    '''
    用re抽取网页Title
    '''
    Html = utf8_transfer(Html)
    compile_rule = ur'<title>.*</title>'
    title_list = re.findall(compile_rule, Html)
    if title_list == []:
        title = ''
    else:
        title = title_list[0][7:-8]
    return title


def get_title_cut(Html):
    '''
    用re抽取网页Title，并选择其分词结果中的名词
    '''
    title = get_title(Html)
    return jieba_POS_tagging(title)


def get_ICP(Html):
    '''
    抽取网页ICP号
    '''
    compile_rule = ur'([\u4e00-\u9fa5]).?ICP([\u8bc1|\u5907]*)(\d{0,10})'
    ICP_list = re.findall(compile_rule, Html)
    if ICP_list == []:
        ICP = ''
    else:
        ICP = ICP_list[0][0] + ICP_list[0][2]
    return ICP


def get_div_num(Html):
    '''
    获得html中div标签的数量
    '''
    match = re.findall(r"<div.*?>(.*?)</div>", Html)
    return len(match)


def extract_html_feature(html_path):
    '''
    读取html文件，并抽取title分词后名词、正文关键词、ICP号, 均为字符串格式, 
    关键词由'/'分隔
    '''
    html = utf8_open_file(html_path)
    title_keyword = get_title_cut(html)
    text_keyword = get_html_keyword(html)
    ICP = get_ICP(html)  # 抽取html中ICP
    return title_keyword, text_keyword, ICP


def get_link_number(url, link_content_list):
    '''
    获得页面中链接（URL）总数、内链个数、外链个数、空链个数，返回一个字典
    link_content_list：网页中所有链接（URL）的列表
    输出格式：{'linkNum':10,'nonelinkNum':3,'insidelinkNum':2,'outsidelinkNum':5}
    '''
    domain = url_split(url)['domain']
    linkNum = 0  # 总链接数量
    nonelinkNum = 0  # 空链接数量
    outsidelinkNum = 0  # 外链数量
    insidelinkNum = 0  # 内链数量
    none_list = [None, "", "/", "#", " ", "http://#", "http://"]  # 空串集合
    for link_content in link_content_list:
        linkNum += 1
        # 如果获得的链接为NONE或空字符串，则认定为空链接
        if link_content in none_list:
            nonelinkNum += 1
        # 如果链接内容符合以下情况，则认为是内链：
        # 1 以#开头，且长度大于1
        # 2 以'/'开头的为相对路径
        # 3 以'javascript'开头
        elif (link_content.find('#') == 0 and len(link_content) > 1) \
                or (link_content.find('/') == 0) or (link_content.lower().find('javascript') == 0) \
                or (link_content.find('http://.') == 0) or (link_content.find('.../') == 0) \
                or (link_content.find('./') == 0) or (link_content.find('../') == 0):
            insidelinkNum += 1
        else:
            # 获取该链接的域名部分
            link_netloc = url_split(link_content)['domain']
            if link_netloc:
                try:
                    # 如果该链接的域名与本域域名不匹配，则认为该链接是外链
                    match = re.search(link_netloc, unicode(domain))
                    if match == None:  # 说明不匹配
                        outsidelinkNum += 1
                    else:
                        insidelinkNum += 1
                except:
                    raise
            else:  # 无法获取域名，例如url为'http://'

                nonelinkNum += 1
    return {'linkNum': linkNum, 'nonelinkNum': nonelinkNum,
            'insidelinkNum': insidelinkNum, 'outsidelinkNum': outsidelinkNum}


def get_link_numbaer_rate(linkNumDic):
    '''
    计算网页内外链比例
    linkNumDic：网页链接（URL）总数、内链个数、外链个数、空链个数的字典
    返回四种链接类型的比例列表
    '''
    if linkNumDic['linkNum'] == 0:
        return [0, 0, 0]
    else:
        linkNum = linkNumDic['linkNum']
        nonelinkNum = linkNumDic['nonelinkNum']
        insidelinkNum = linkNumDic['insidelinkNum']
        outsidelinkNum = linkNumDic['outsidelinkNum']
        none_link_percent = round(float(nonelinkNum) / linkNum, 2)
        inside_link_percent = round(float(insidelinkNum) / linkNum, 2)
        outside_link_percent = round(float(outsidelinkNum) / linkNum, 2)
        return [none_link_percent, inside_link_percent, outside_link_percent]


def get_a_link_number_bs4(url, soup):
    '''
    获取网页所有a标签中的链接，并分四类返回
    soup：BeautifulSoup实例对象
    '''
    mul_links = soup.find_all('a')
    link_content_list = []
    for link in mul_links:
        link_content_list.append(link.get('href'))
    return get_link_number(url, link_content_list)


def get_a_link_number(url, Html):
    '''
    获取网页所有a标签中的链接，并分四类返回
    '''
    page = etree.HTML(Html)
    mul_links = page.xpath('//a/@href')
    return get_link_number(url, mul_links)


def get_a_link_rate(url, Html):
    '''
    获取网页所有a标签中的链接的个数比例，并分四类返回
    '''
    linkNumDic = get_a_link_number(url, Html)
    return get_link_numbaer_rate(linkNumDic)


def get_src_links(page, Html):
    '''
    获取网页中所有具有src属性的标签，并分为css、js、pic、html四类
    '''
    # 补充抽取规则，和下面重复
    # imgSrcPattern1 = r'''<img\s*src\s*="?(\S+)"?'''
    # imgSrcPattern2 = r'''<script\s*src\s*="?(\S+)"?'''
    # imgSrcPattern3 = r'''<div\s*src\s*="?(\S+)"?'''
    # imgSrcPattern4 = r'''<embed\s*src\s*="?(\S+)"?'''
    # imgSrcPattern5 = r'''<INPUT\s*src\s*="?(\S+)"?'''
    # imgSrcPattern6 = r'''<frame\s*src\s*="?(\S+)"?'''
    # imgSrcPattern7 = r'''<iframe\s*src\s*="?(\S+)"?'''
    # imgSrcPattern8 = r'''<audio\s*src\s*="?(\S+)"?'''
    # imgSrcPattern9 = r'''<vedio\s*src\s*="?(\S+)"?'''
    # imgSrcPattern10 = r'''<track\s*src\s*="?(\S+)"?'''
    # imgSrcPattern11 = r'''<source\s*src\s*="?(\S+)"?'''
    css_list = page.xpath('//*/link[@rel="stylesheet"]/@href')
    js_list = page.xpath('//*/script/@src')
    pic_list = page.xpath('//*/link[@rel="shortcut icon"]/@href')
    pic_list += page.xpath('//*/link[@rel="Shortcut Icon"]/@href')
    pic_list += page.xpath('//*/link[@rel="icon"]/@href')
    pic_list += re.findall('url\((.*?)\)', Html, re.S)
    pic_list += page.xpath('//img/@original')
    pic_list += page.xpath('//img/@src')
    pic_list += page.xpath('//div/@src')
    pic_list += page.xpath('//input/@src')
    pic_list += page.xpath('//*/@background')
    html_list = page.xpath('//iframe/@src')
    html_list += page.xpath('//frame/@src')
    src_link_list = (['html_list', list(set(html_list))], ['pic_list', list(set(pic_list))],
                     ['css_list', list(set(css_list))], ['js_list', list(set(js_list))])
    return src_link_list


def get_src_link_number(url, Html):
    '''
    找到Html中所有src资源对应标签中css、js、pic、html的url数量
    '''
    Html = utf8_transfer(Html)
    page = etree.HTML(Html, parser=etree.HTMLParser(encoding='utf-8'))
    src_link_list = get_src_links(page, Html)
    src_link_number = {}
    for src_num in src_link_list:
        src_link_number[src_num[0]] = get_link_number(url, src_num[1])
    return src_link_number


def get_src_link_rate(url, Html):
    '''
    找到Html中所有src资源对应标签中css、js、pic、html的url数量的比例
    '''
    src_link_number = get_src_link_number(url, Html)
    src_link_rate = {}
    for src_name in src_link_number:
        src_link_rate[src_name] = get_link_numbaer_rate(
            src_link_number[src_name])
    return src_link_rate


def get_form_method_feature_bs4(soup):
    '''
    提取form中get/post方法的特征 ，如果存在GET方法返回1，否则如果全是POST方法返回0
    '''
    for form in soup.find_all('form'):
        form_mehtod = form.get('method')
        if form_mehtod == 'get':
            return 1
    return 0


def get_form_method_feature(Html):
    '''
    提取form中get/post方法的特征 ，如果存在GET方法返回1，否则如果全是POST方法返回0
    '''
    page = etree.HTML(Html)
    form_method = page.xpath('//form/@method')
    if form_method:
        if form_method[0] == 'get':
            return 1
    return 0


def getFormActionFeature(url, soup):
    '''
    提取form的Action 特征：post方法的action特征，post是将用户输入的值提交到指定服务器
    在此判断提交服务器的域名是否与当前页面域名一致
    post方法的action介绍：action有三种类型并为其赋权重值
        1、action为空值，即未将用户输入的值上传，其权重为1
        2、action为路径，仿冒网站多用相对路径，其权重为3
        3、action为完整的URL，则抽取其域名判断是否与当前页面域名一致，其权重为5
    '''
    result = 0
    # action的内容 为空 则结果加1 ；使用相对路径 结果加3，绝对路径-3；使用是完整的URL 则判断域名是否一致，一致-5，不一致+5
    # 遍历网页中所有的form表单，对结果进行累加，返回最后结果，结果越大，可疑程度越高
    weight_none = 1  # 链接为空权重
    weight_path = 3  # 链接为路径权重
    weight_domain = 5  # 链接为完整url权重
    none_list = [None, '', '/', '#']
    for form in soup.find_all('form'):
        form_mehtod = form.get('method')
        form_action = form.get('action')
        # 如果action 为空
        if (form_mehtod in none_list) or (form_action in none_list):
            result += weight_none
        # 如果action不为空，这里仅考虑method为post的情况
        else:
            if form_mehtod == 'post':
                # 获得action方法的域名，判定其是否为完整的URL，如果域名为空则不是。
                action_netloc = url_split(form_action)['domain']
                # 如果aciton 是完整的URL路径，则判断其域名是否与当前页面域名一致
                if action_netloc != '':
                    domain = url_split(url)['domain']
                    match = domain.find(action_netloc)
                    # 如果action域名与当前页面不一致
                    if match == -1:
                        result += weight_domain
                    # 如果action域名与当前页面一致
                    else:
                        result -= weight_domain
                # 如果aciton 是路径，仿冒网站多数会使用相对路径
                else:
                    if form_action[0] not in ['/', '.']:
                        result += weight_path
                    else:
                        result -= weight_path
            else:
                continue
    return result


def getFormInputFeature(soup):
    '''
    提取form的Input特征：提取input标签中 name id placeholder的值，判断其是否为敏感词汇，如 email password等 
    '''

    result = 0  # 包含敏感词汇的标签总数
    counter = 0  # form标签总数
    for form_input in soup.find_all('input'):
        input_name = form_input.get('name')
        input_id = form_input.get('id')
        input_placeholder = form_input.get('placeholder')
        input_type = form_input.get('type')
        # 仅考虑 没有隐藏的input标签
        if input_type != 'hidden':
            counter += 1
            for key in RED_KEYWORDS:
                    # 判断 name id placeholder 中是否包含关键字，如有一个包含即可跳出循环进行下一次判断
                if input_id and input_id.lower().find(key) != -1:
                    result += 1
                if input_name and input_name.lower().find(key) != -1:
                    result += 1
                if input_placeholder and input_placeholder.lower().find(key) != -1:
                    result += 1
    if counter:
        # 最后返回包含关键字的标签比例
        result = round(float(result) / counter, 2)
    return result


def get_twice_page_jump(Html):
    '''
    判断网页中是否有页面跳转
    '''
    re_script = re.compile(
        u'<meta http-equiv="refresh".*?url=(.*?)">', re.S | re.I)
    if re_script.search(Html):
        return 1
    re_script = re.compile(u'location.href="(.*?)";', re.S | re.I)
    if re_script.search(Html):
        return 1
    re_script = re.compile(u'window.location="(.*?)";', re.S | re.I)
    if re_script.search(Html):
        return 1
    return 0


def get_browser_judge_jump(Html):
    '''
    判断是否有浏览器判断跳转，比如有网站判断是否为PC端浏览器，若是则不显示网页
    '''
    re_script = re.compile(
        r"<script>([\s\S]*?)window.location.href\s*=\s*'/Default.asp'([\s\S]*?)</script>", re.S | re.I)
    return 1 if re_script.search(Html) else 0


def get_alert_sign(Html):
    '''
    判断网页中是否有alert
    '''
    re_script = re.compile(r"<script\s*[^>]*>alert.*?</script>", re.S | re.I)
    return 1 if re_script.search(Html) else 0


def extract_alert(html):
    '''
    保存网页中弹窗中的内容
    '''
    re_alert = re.compile(r"<script\s*[^>]*>alert.*?</script>", re.S)
    alert_content = re_alert.findall(html)
    if alert_content != []:
        # 删除字符中的换行符
        alert_str = alert_content[0].replace('\n', '')  # 只抽取网页第一个弹窗
        # 得到所需字符
        need_alert = alert_str[alert_str.find(
            'alert') + 7: alert_str.rfind(')') - 1].replace('\\n', '').replace('\\', '').decode('utf-8')
        return need_alert
    else:
        return False


def extract_meta(html):
    '''
    保存网页meta中有关搜索关键字的部分
    '''
    if chardet.detect(html)['encoding'] == 'utf-8':
        html = html.decode('utf-8')
    meta_list = []
    # 筛选html中meta的内容
    page = etree.HTML(html.lower())
    xpath_result = page.xpath(u"//meta/@content")
    for once_xpath_result in xpath_result:
        # 抽取包含中文字符的部分
        if zh_check(once_xpath_result) == True:
            meta_list.append(utf8_transfer(once_xpath_result).decode('utf-8'))
    if meta_list != []:
        return meta_list
    else:
        return False


def get_js_long(html):
    '''
    判断网页中的script内容是否超过网页总共的50%
    '''
    script_num = 0
    len_html = len(html)
    # 抽取script包含的内容
    re_alert = re.compile(r">\s*alert[\S\s]*</script>")
    alert_content = re_alert.findall(html)
    # 计算script中内容的字符长度
    if alert_content != []:
        for once_alert_content in alert_content:
            script_num += len(once_alert_content)
    # 计算script中字符长度是否超过总字符的50%
    if float(script_num) / float(len_html) >= 0.5:
        return True
    else:
        return False

def cut_sentence_new(words):
    '''
    以标点符号断句，返回分割的子句
    '''
    # words = (words).decode('utf8')
    start = 0
    i = 0
    sents = []
    punt_list = ',.!?:;~，。！？：；～'.decode('utf8')
    for word in words:
        try:
            if word in punt_list and token not in punt_list: #检查标点符号下一个字符是否还是标点
                sents.append(words[start:i+1])
                start = i+1
                i += 1
            else:
                i += 1
                token = list(words[start:i+2]).pop() # 取下一个字符
        except:
            continue
    if start < len(words):
        sents.append(words[start:])
    return sents

def cut_sentence_format(words):
    '''
    # 将输入的文本转换为unicode编码，然后根据标点符号切分
    '''
    words = words.strip()
    words = utf8_transfer(words)
    words = words.decode('utf8')
    return cut_sentence_new(words)


if __name__ == '__main__':
    Html = utf8_open_file('main.html')
    print 'keyword textrank', get_html_keyword(Html)
    print 'keyword tfidf', get_html_keyword_tfidf(Html)
    print 'title', get_title(Html)
    print 'title_keyword', get_title_cut(Html), len(get_title_cut(Html))
    print 'ICP', get_ICP(Html)
    print 'div_num', get_div_num(Html)
    print 'chinese', match_chinese(utf8_transfer(Html))
    page = etree.HTML(Html, parser=etree.HTMLParser(encoding='utf-8'))
    print get_src_links(page, Html)
    