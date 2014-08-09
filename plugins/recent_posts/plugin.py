#!/usr/bin/env python2
# -*- coding: utf-8 -*-

def output(pages, posts):
    text = ''
    for post in posts:
        if 'title' in post:
            text += '<a href="%s">%s</a><br />' % (post['url'], post['title'])
    return text
