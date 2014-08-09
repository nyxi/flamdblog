flamdBlog
====

A fairly simple blog built with Flask, Misaka and Pygments to gather content from markdown files and display them with the correct markup, including syntax highlighting of code. Post/page editing heavily inspired by [Dillinger](http://dillinger.io/) using the [Ace editor](http://ace.c9.io/), the [marked](https://github.com/chjj/marked) library and some basic jQuery magic.

__Still very much a work in progress, what you see in the screenshots is essentially what you get.__

[Frontpage](http://nyxi.eu/pics/projects/flamdblog.jpg)

[Editing content](http://nyxi.eu/pics/projects/flamdblog-admin.jpg)

Installation
-----
1. pip install -r requirements.txt
2. Edit and save "config.sample" as "config"
3. python flamdblog.py

Recommend you deploy with nginx and uWSGI or something equally robust. Example in my [ebooklibrary repo](https://github.com/nyxi/ebooklibrary).

Usage:
-----
Login with the password you specified in the config file and either edit the existing page/post or create new ones then delete the old ones.
