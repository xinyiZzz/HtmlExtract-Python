# -*- coding: utf-8 -*-
'''
Name: TF-IDF 算法实现 更新
Author：XuBing/XinYi 609610350@qq.com
Time：2015.4.20

更新idf值，对idf值采用周期性更新时，调用该文件中的updateidf函数，
传递的参数分别为存有计算idf值的大量文本的文件夹，默认为D:/test，
输出计算出的idf值的文件，默认为D:/idf.txt
'''
import jieba
import os
import math

def GetFileList(dir, fileList):
    newDir = dir
    if os.path.isfile(dir):
        fileList.append(dir.decode('gbk'))
    elif os.path.isdir(dir): 
        for s in os.listdir(dir):
            newDir=os.path.join(dir,s)
            GetFileList(newDir, fileList)
    return fileList

'''
接收一个待处理文本filename
下面为处理一个文本，得到该文本中出现过的单词，并累加上去，
最后循环完所有文本，则word_doc[i]存储i词在所有已处理文本中出现的文本数
'''
def get_word_count(filename):
    data_source=open(filename,'r')
    data=data_source.read()
    if(data!=''):
        temp_result = jieba.cut(data,cut_all=True)
        temp_result = '/'.join(temp_result)
        word_result=temp_result.split('/')
        word_view={}#word_view[i]标记针对正在处理的文本之前是否处理i词
        for i in word_result:
            word_view[i]=0
            if(i not in word_doc):
                word_doc[i]=0
        for i in word_result:
            if(word_view[i]==0):
                word_view[i]=1;
                word_doc[i]=word_doc[i]+1

'''
循环处理完所有文本后，word_doc[i]为i词出现过的所有文本数，file_num为总的文本数，
此时计算idf值，并存储在文件中
'''
def updateidf(file_textin='D:\\test',file_out="D://idf.txt"):
    list = GetFileList(file_textin, [])
    word_doc={}
    file_num=0
    global word_doc
    for filename in list:
        file_num = file_num+1
        get_word_count(filename)
    idffile=open(file_out,'w')
    for i in word_doc:
        if(i==''):
            continue
        idffile.write(i.encode('gbk'))
        if(word_doc[i]==0):
            continue
        idf = math.log(float(file_num)/float(word_doc[i]))
        idffile.write('\t'+str(idf))
        idffile.write('\n')
    idffile.close()
