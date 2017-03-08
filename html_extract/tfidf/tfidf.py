# -*- coding: utf-8 -*-
'''
Name: TF-IDF 算法实现
Author：XuBing/XinYi 609610350@qq.com
Time：2015.4.20

计算一个给定文本的关键词，返回字典，为按tfidf排序好的词及对应tfidf值
调用tfidf，传入的参数为待处理文本，默认位置为"D://test.txt"
idf值文本，默认存在"D://idf.txt"
'''
import jieba

def getidf(str,idffile):
    idf_source=open(idffile,'r')
    idf=idf_source.readline()
    idf = idf.split('\t')
    while(idf[0].decode('gbk')!=str and idf[0]!=''and idf[0]!='\n'):
        idf=idf_source.readline()
        idf = idf.split('\t')
    idf_source.close()
    if(idf[0]==''or idf[0]=='\n'):
        return -1
    else:
        return float(idf[1].split('\n')[0])

def tfidf(textfile="D://test.txt",idffile="D://idf.txt"):
    data_source=open(textfile,'r')
    data=data_source.read()
    data_source.close()
    if(data!=''):
        temp_result = jieba.cut(data,cut_all=True)
        temp_result = '/'.join(temp_result)
        word_result=temp_result.split('/')
        word_num = len(word_result)
        word_count={}
        word_idf = {}
        word_tfidf={}
        for i in word_result:
            word_count[i] = 0
        for i in word_result:
            word_count[i]=word_count[i]+1
        for i in word_count:
            if(i==''):
                continue
            word_count[i]=float(word_count[i])/word_num
            idf = getidf(i,idffile)
            if(idf==-1):
                continue;
            else:
                word_idf[i]=idf
                word_tfidf[i]=word_count[i]*word_idf[i]
        sorted(word_tfidf.iteritems(),lambda d:d[1],reverse=True)
        num=0;
        return word_tfidf

if __name__ == '__main__':
    tfidf()