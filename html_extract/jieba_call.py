# -*- coding: utf-8 -*-

'''
Name: jieba库调用
Author：XinYi 609610350@qq.com
Time：2016.3
'''

import jieba.analyse
import jieba


def cut_all(data):
    '''
    采用全模式分词，即把句子中所有的可以成词的词语都扫描出来
    来到北京大学-->来到/北京/北京大学/大学
    '''
    temp_result = jieba.cut(data, cut_all=True)
    temp_result = '/'.join(temp_result)
    return temp_result


def cut_accurate(data):
    '''
    采用精准模式分词，试图把句子精确切开
    来到北京大学-->来到/北京大学
    '''
    temp_result = jieba.cut(data, cut_all=False)
    # temp_result = '/'.join(temp_result)
    return temp_result


def cut_search(data):
    '''
    采用搜索引擎模式分词，在精确模式的基础上，对长词再次切分，
    来到北京大学-->来到/北京/大学/北京大学
    '''
    temp_result = jieba.cut_for_search(data)
    temp_result = '/'.join(temp_result)
    return temp_result


def add_word_dict(word, freq=None, tag=None):
    '''
    向词典中添加新单词
    '''
    jieba.add_word(word, freq=None, tag=None)


def del_word_dict(word):
    '''
    向词典中删除单词
    '''
    jieba.del_word(word)


def jieba_textrank(data, topK=20, withWeight=False, allowPOS=('nz', 'nt', 'ns', 'nr', 'n', 'vn')):
    '''
    利用textrank获取文本的关键词，topK设置为返回的关键词个数，默认为20个
    withWeight设置是否按权值由大到小的顺序返回
    allowPOS设置返回的词性
    '''
    keyword_list = []
    for w in jieba.analyse.textrank(data, topK=20, withWeight=True, allowPOS=allowPOS):
        keyword_list.append(w[0])
    keyword = '/'.join(keyword_list)
    return keyword

def jieba_POS_tagging(data, allowPOS=('nz', 'nt', 'ns', 'nr', 'n', 'vn')):
    '''
    对data分词后提取词性，并通过allowPOS过滤词性后返回分词结果
    '''
    segs = jieba.posseg.cut(data)
    temp_result = []
    for w in segs:
        if w.flag[0] in allowPOS:
            temp_result.append(w.word)
    temp_result = '/'.join(temp_result)
    return temp_result

def jieba_tfidf(data, topK=20, withWeight=False, allowPOS=('nz', 'nt', 'ns', 'nr', 'n', 'vn')):
    '''
    使用tfidf获取文本的关键词，topK设置为返回的关键词个数，默认为20个
    withWeight设置是否按权值由大到小的顺序返回
    allowPOS设置返回的词性
    '''
    temp_result = jieba.analyse.extract_tags(
        data, topK, withWeight, allowPOS)
    temp_result = '/'.join(temp_result)
    return temp_result


if __name__ == '__main__':
    # print cut_all('来到北京大学')
    # print cut_search('来到北京大学')
    # print cut_accurate('来到北京大学')
    # print get_keyword('来到北京大学', topK=2, withWeight=True)
    print jieba_POS_tagging('淘宝网 - 淘！我喜欢')