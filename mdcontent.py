#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import misaka
import os
import re
from pygments import highlight
from pygments.lexers import guess_lexer, get_lexer_by_name
from pygments.formatters import HtmlFormatter


def get(maxposts=5, page=None, url=None):
    pages, posts = get_filepaths()
    pages, posts = build_urls(pages, posts)
    pages = get_metadata(pages)
    posts = get_metadata(posts, maxposts)
    if url and url.startswith('/blog'):
        for post in posts:
            if post['url'] == url:
                nposts = get_metadata([post])
                post = nposts[0]
    if page:
        start = page*maxposts
        i = 0
        post_id = start
        for post in posts[start:]:
            nposts = get_metadata([post])
            post = nposts[0]
            i += 1
            if i == maxposts or i >= len(posts):
                break
    pages, posts = parse_legacy_blockquote(pages, posts)
    pages, posts = pygmentize_fenced_code(pages, posts)
    pages, posts = parse_codeblocks(pages, posts)
    pages, posts = get_teaser(pages, posts)
    return pages, posts

def get_filepaths():
    pages = []
    posts = []
    for ctype in ['posts', 'pages']:
        for f in sorted(os.listdir(ctype)):
            if os.path.splitext(f)[1] in ['.md', '.markdown']:
                if ctype == 'posts':
                    posts.append({'filepath': '%s/%s' % (ctype, f)})
                else:
                    pages.append({'filepath': '%s/%s' % (ctype, f)})
    return pages, sorted(posts, reverse=True)

def build_urls(pages, posts):
    combined = {'pages': pages, 'posts': posts}
    for ctype in combined:
        for item in combined[ctype]:
            cf = os.path.split(item['filepath'])[1]
            cf = os.path.splitext(cf)[0]
            if ctype == 'posts':
                url = cf[:10].replace('-', '/')
                item['url'] = '/blog/%s/%s' % (url, cf[11:])
            if ctype == 'pages':
                item['url'] = '/%s' % (cf.replace(' ', '-'))
    return combined['pages'], combined['posts']

def get_metadata(items, maxposts=None):
    i = 0
    for item in items:
        with open(item['filepath'], 'r') as f:
            lines = f.read().splitlines()
        count = 0
        meta = False
        for line in lines:
            count += 1
            if line == '---' and count == 1:
                meta = True
                continue
            if meta and line == '---':
                content = '\n'.join(lines[count:])
                metasection = '\n'.join(lines[:count])
                item['rawbody'] = content
                item['metasection'] = metasection
                meta = False
                continue
            if meta:
                if line.startswith('title: '):
                    title = line.replace('title: ', '')
                    if title[0] == '"':
                        title = title[1:-1]
                    item['title'] = title
                if line.startswith('date: '):
                    item['date'] = line.replace('date: ', '')
                if line.startswith('categories: '):
                    item['categories'] = line.replace('categories: ', '')
        i += 1
        if maxposts and i == maxposts:
            break
    return items

def parse_legacy_blockquote(pages, posts):
    combined = {'pages': pages, 'posts': posts}
    start = '({% blockquote.+?%})'
    startblock = re.compile(start)
    end = '({% endblockquote.+?%})'
    endblock = re.compile(end)
    regexp = '((?s){% blockquote.+?%}.*?\n*{% endblockquote %})'
    codeblock = re.compile(regexp)
    for ctype in combined:
        for item in combined[ctype]:
            if not 'rawbody' in item:
                continue
            contentbody = item['rawbody']
            for block in codeblock.findall(contentbody):
                codebody = block.replace(startblock.match(block).group(), '')
                codebody = endblock.sub('', codebody)
                codebody = codebody.splitlines()
                i = 0
                while i < len(codebody):
                    codebody[i] = '> %s' % (codebody[i])
                    i += 1
                codebody = '\n'.join(codebody)
                contentbody = codeblock.sub(codebody, contentbody, 1)
            item['content'] = contentbody
    return combined['pages'], combined['posts']

def pygmentize_fenced_code(pages, posts):
    regexp = '((?s)```.*?\n*```)'
    fencedblock = re.compile(regexp)
    for ctype in pages, posts:
        for item in ctype:
            if not 'content' in item:
                continue
            rawblocks = fencedblock.findall(item['content'])
            for rawb in rawblocks:
                lines = rawb.splitlines()
                if len(lines[0]) > 4:
                    lang = lines[0][3:]
                lines = '\n'.join(lines[1:-1])
                lexer = None
                if lang is not None:
                    try:
                        lexer = get_lexer_by_name(lang)
                    except:
                        pass
                if not lexer:
                    lexer = guess_lexer(lines)
                hlblock = highlight(lines, lexer, HtmlFormatter())
                item['content'] = fencedblock.sub(hlblock, item['content'], count=1)
    return pages, posts

def parse_codeblocks(pages, posts):
    # PACK IT TIGHT
    combined = {'pages': pages, 'posts': posts}
    # REGEXP SETUP
    start = '({% codeblock.+?%})'
    startblock = re.compile(start)
    end = '({% endcodeblock.+?%})'
    endblock = re.compile(end)
    regexp = '((?s){% codeblock.+?%}.*?\n*{% endcodeblock %})'
    codeblock = re.compile(regexp)
    # NEW STUFF
    for ctype in combined:
        for item in combined[ctype]:
            if not 'content' in item:
                continue
            highlighted_blocks = []
            markdown_blocks = []
            # FOR EACH COMPLETE CODEBLOCK IN CONTENTBODY
            contentbody = item['content']
            for block in codeblock.findall(contentbody):
                # STRIP THE START TAG
                codebody = block.replace(startblock.match(block).group(), '')
                # STRIP THE END TAG
                codebody = endblock.sub('', codebody)
                # GETTING OPTIONS IN THE START TAG (UNUSED?)
                initblock = startblock.match(block).group()
                if len(initblock) > 15:
                    options = initblock.replace('{% codeblock ', '')
                    options = options[0:-3]
                # RUN THE CODE THROUGH PYGMENTS HTML HIGHLIGHTER
                codebody = highlight(codebody, guess_lexer(codebody), HtmlFormatter())
                highlighted_blocks.append(codebody)
                # REPLACE THE CODEBLOCK IN CONTENTBODY WITH A "FLAG"
                contentbody = codeblock.sub('<<<---CB--->>>', contentbody, 1)
            # MARKUP THE NON-CODEBLOCKS
            unformatted_blocks = contentbody.split('<<<---CB--->>>')
            for unformatted_block in unformatted_blocks:
                # MISAKA IS FABULOUS
                unformatted_block = unformatted_block.decode('utf-8')
                markdown_block = misaka.html(unformatted_block, extensions=misaka.EXT_FENCED_CODE | misaka.EXT_NO_INTRA_EMPHASIS)
                markdown_blocks.append(markdown_block)
            # FINALLY, PUT TOGETHER A NEW CONTENTBODY
            newbody = ''
            for markdown_block in markdown_blocks:
                newbody += markdown_block
                if highlighted_blocks:
                    for highlighted_block in highlighted_blocks:
                        newbody += highlighted_block
                        break
                    del highlighted_blocks[0]
            item['content'] = newbody
    return combined['pages'], combined['posts']

def get_teaser(pages, posts):
    combined = {'pages': pages, 'posts': posts}
    for ctype in combined:
        for item in combined[ctype]:
            if not 'content' in item:
                continue
            content = None
            contentbody = item['content']
            contentbody = contentbody.replace('&lt;!-- more --&gt;', '<!-- more -->')
            contentbody = contentbody.replace('&lt;!--more--&gt;', '<!-- more -->')
            if '<!-- more -->' in contentbody:
                content = contentbody.split('<!-- more -->')
            elif '<!--more-->' in contentbody:
                content = contentbody.split('<!--more-->')
            if content and len(content) == 2:
                item['teaser'] = misaka.html(content[0], extensions=misaka.EXT_FENCED_CODE | misaka.EXT_NO_INTRA_EMPHASIS)
                item['content'] = content[1]
            else:
                item['content'] = contentbody
    return combined['pages'], combined['posts']
