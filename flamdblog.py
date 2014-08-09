#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import arrow
import ConfigParser
from flask import Flask, redirect, render_template
from flask import request, session
import imp
import math
import mdcontent
import os


#Get settings from the config file
config = ConfigParser.SafeConfigParser()
config.read('config')
TITLE = config.get('core', 'title')
THEME = config.get('cosmetic', 'theme')
PASSWORD = config.get('core', 'password')
PORT = int(config.get('core', 'port'))
POSTS_PER_PAGE = int(config.get('cosmetic', 'posts_per_page'))
#Configure Flask
app = Flask(__name__)
app.secret_key = os.urandom(64)


#####################################################################
# PLUGINS BLOCK
#####################################################################
def get_plugins():
    plugdirs = []
    for d in os.listdir('plugins'):
        if os.path.isdir('plugins/%s' % (d)):
            for f in os.listdir('plugins/%s' % (d)):
                if f == 'plugin.py':
                    plugdirs.append('plugins/%s' % (d))
    plugins = {}
    for pdir in plugdirs:
        pluginname = os.path.split(pdir)[1]
        plugins[pluginname] = imp.load_source(pluginname, '%s/plugin.py' % (pdir))
    return plugins

def execute_plugins(pages, posts):
    plugins = get_plugins()
    output = {}
    for plugin in plugins:
        output[plugin] = plugins[plugin].output(pages, posts)
    return output

#####################################################################
# VALIDATE NEW POSTS/PAGES
#####################################################################
@app.route('/admin/', methods=['POST'])
def postadmin():
    if not 'logon' in session:
        return redirect('/login/')
    for key in ['title', 'categories', 'content']:
        if not key in request.form:
            error = '<strong>Error: </strong>Missing required field %s in form data' % (key)
            return index(error=error)
    now = arrow.utcnow()
    date = now.format('YYYY-MM-DD')
    filename = '%s.markdown' % (request.form['title'].replace(' ', '-').lower())
    categories = request.form['categories'].split(',')
    categories = ', '.join(categories)
    metadata = '---\ntitle: "%s"\ncategories: %s\ndate: %s\n---\n' % (request.form['title'], categories, now.format('YYYY-MM-DD HH:mm'))
    filedata = metadata + request.form['content']
    if 'is_page' in request.form:
        with open('pages/%s' % (filename), 'w') as f:
            f.write(filedata.encode('utf-8'))
    else:
        with open('posts/%s-%s' % (date, filename), 'w') as f:
            f.write(filedata.encode('utf-8'))
    return redirect('/')

#####################################################################
# SHOW THE EDIT PAGE FOR POSTS/PAGES
#####################################################################
@app.route('/edit/<path:item>')
def edititem(item):
    if not 'logon' in session:
        return redirect('/login/')
    url = '/%s' % (item)
    pages, posts = mdcontent.get(url=url)
    for ctype in pages, posts:
        for content in ctype:
            if content['url'] == url:
                single = content
    if not url.startswith('/blog/'):
        is_page = True
    template = 'admin.jinja2'
    sitetitle = TITLE
    return render_template('%s/%s' % (THEME, template), **locals())

#####################################################################
# VALIDATE EDITS AND UPDATE FILES
#####################################################################
@app.route('/edit/', methods=['POST'])
def updateitem():
    if not 'logon' in session:
        return redirect('/login/')
    valid = False
    for item in ['content', 'title', 'categories', 'filename', 'date']:
        if not item in request.form:
            error = '<strong>Error: </strong> Missing form data for: %s' % (item)
            return index(error=error)
    pages, posts = mdcontent.get()
    for ctype in pages, posts:
        for content in ctype:
            if content['filepath'] == request.form['filename']:
                valid = True
                break
        if valid:
            break
    if valid:
        categories = request.form['categories'].split(',')
        categories = ', '.join(categories)
        metadata = '---\ntitle: "%s"\ncategories: %s\ndate: %s\n---\n' % (request.form['title'], categories, request.form['date'])
        filedata = metadata + request.form['content']
        newpath = request.form['title'].replace(' ', '-').lower()
        newpath = newpath + '.markdown'
        if not 'is_page' in request.form:
            newpath = request.form['filename'][:17] + newpath
        else:
            newpath = 'pages/' + newpath
        with open(request.form['filename'], 'w') as f:
            f.write(filedata.encode('utf-8'))
        os.rename(request.form['filename'], newpath)
        return redirect(content['url'])

#####################################################################
# DELETE POST/PAGE
#####################################################################
@app.route('/delete/<path:url>')
def deleteitem(url):
    if not 'logon' in session:
        return redirect('/')
    url = '/%s' % (url)
    pages, posts = mdcontent.get()
    valid = False
    for ctype in pages, posts:
        for content in ctype:
            if content['url'] == url:
                os.remove(content['filepath'])
                valid = True
                break
        if valid:
            break
    return redirect('/')

#####################################################################
# LOGIN PAGE
#####################################################################
@app.route('/login/', methods=['GET'])
def viewlogin():
    pages, posts = mdcontent.get()
    if 'logon' in session:
        admin = True
    sitetitle = TITLE
    return render_template('%s/login.jinja2' % (THEME), **locals())

#####################################################################
# VALIDATE LOGIN
#####################################################################
@app.route('/login/', methods=['POST'])
def login():
    if 'password' in request.form:
        if request.form['password'] == PASSWORD:
            session['logon'] = True
            return redirect('/')
        else:
            error = '<strong>Error:</strong> Incorrect password'
            return viewlogin(error=error)
    else:
        error = '<strong>Error:</strong> No password in form data?'
        return viewlogin(error=error)

#####################################################################
# CONTENT SECTION
#####################################################################
@app.route('/', methods=['GET'])
@app.route('/admin/', methods=['GET'])
@app.route('/<path:url>')
def index(error=None, page=None, success=None, url=None, template='index.jinja2'):
    # Max number of posts per page
    maxposts = POSTS_PER_PAGE
    # Is a specific posts page requested?
    if 'p' in request.args:
        page = int(request.args['p'])
    # Is a single page/post requested?
    if url:
        url = '/%s' % (url)
        pages, posts = mdcontent.get(url=url)
        for ctype in pages, posts:
            for content in ctype:
                if content['url'] == url:
                    single = content
    else: 
        pages, posts = mdcontent.get(page=page, maxposts=maxposts)
    # Calc how many pages of posts there are
    postpages = float(len(posts))/float(maxposts)
    postpages = int(math.ceil(postpages))
    # Build front page posts
    frontposts = []
    for post in posts[:maxposts]:
        frontposts.append(post)
    # Build archive posts
    oldpage = '/?p=1'
    newpage = None
    if page:
        archive = []
        for post in posts[maxposts:]:
            if 'content' in post:
                archive.append(post)
        oldpage = '/?p=%s' % (page+1)
        if page-1 > 1:
            newpage = '/?p=%s' % (page-1)
        else:
            newpage = '/'
    # If admin page, use admin template etc
    if request.url_rule.rule.startswith('/admin'):
        template = 'admin.jinja2'
        if 'page' in request.args:
            is_page = True
    # Is the user logged in?
    if 'logon' in session:
        admin = True
    # Title
    sitetitle = TITLE
    # Get plugins
    plugins = execute_plugins(pages, posts)
    return render_template('%s/%s' % (THEME, template), **locals())


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT, debug=True)
