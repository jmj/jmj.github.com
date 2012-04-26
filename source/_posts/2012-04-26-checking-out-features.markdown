---
layout: post
title: "checking out features"
date: 2012-04-26 10:47
comments: true
categories: [octopress, testing, plugins]
---

## Just playing around with octopress features and plugins

### codeblock plugin
{% codeblock [lang:python] %}
# do not need this.  )(s)ead info from cfg.xt
def portlist(ser):
    data = ''
    escalatepriv(ser)
    ser.flushInput()
    ser.write('file dir settings\r\n')
    data = readdata(ser)
    dl = [x[5:6] for x in
            [y.strip() for y in data.split('\r\n')]
            if x.startswith('SET_P')]
    return dl
{% endcodeblock %}

### Include code
{% include_code lang:python pywork.py %}


