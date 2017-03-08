## March 1 2017 10:48 AM

# HtmlExtract-Python

Extract all the text in the text, Chinese, keywords, Title, ICP, link and inside and outside the chain ratio, form form, alert, meta, jump, sensitive words and other information

抽取HTML中所有文本、中文、关键词、Title、ICP、链接及内外链比例、form表单、alert、meta、跳转、敏感词等信息

* * *


## function/系统功能

Extract all the text in the text, Chinese, keywords, Title, ICP, link and inside and outside the chain ratio, form form, alert, meta, jump, sensitive words and other information

抽取HTML中所有文本、中文、关键词、Title、ICP、链接及内外链比例、form表单、alert、meta、跳转、敏感词等信息

## examples/使用范例

```
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
```

## contact/联系方式


609610350@qq.com
