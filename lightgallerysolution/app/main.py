from fastapi import FastAPI, HTTPException, File, UploadFile, Request, Form, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse, StreamingResponse, RedirectResponse
import markdown
from markupsafe import escape 
import os
import errno
from markdown.inlinepatterns import Pattern
import xml.etree.ElementTree as etree
from markdown.extensions import Extension
from markdown.extensions.toc import TocExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.tables import TableExtension
# from myextension import MyExtension
import glob
import git
import html
import subprocess    # for video thumbnails
import asyncio
from pydantic import BaseModel
import json
from time import localtime, strftime
import threading
from weasyprint import HTML, CSS
from bs4 import BeautifulSoup
import re
import base64
from wand.image import Image   # sudo apt-get install libmagickwand-dev        pip3 install Wand
import time

class MdgsStatus(BaseModel):
    pulling: str
    message: str
    commitID: str


baseURL="/mdgs"
resizing_file_counter = 0
resizing_file_len = 0

###########################################################
## Helper functions #######################################
###########################################################

def getFilenameFromPath(path):
    return ".".join(path.split(".")[0:-1])

def getListFromFolderAsList(folder):
    # List all files in a directory using scandir()
    res = []
    with os.scandir(folder) as entries:
        blah = entries
        if blah:
            blah.sort()
        for entry in blah:
            if entry.is_file():
                if entry.name.split(".")[-1] == "md":
                    res.append({"fullpath": "/"+folder+"/"+getFilenameFromPath(entry.name) , "folder" : folder.split("/")[-1], "filename" : getFilenameFromPath(entry.name)})
    return res

def getListFromFolder(folder):
    # List all files in a directory using scandir()
    res = []
    with os.scandir(folder) as entries:
        blah = entries
        if blah:
            blah.sort()
        for entry in blah:
            if entry.is_file():
                if entry.name.split(".")[-1] == "md":
                    res.append({"fullpath": "/"+folder+"/"+getFilenameFromPath(entry.name) , "folder" : folder.split("/")[-1], "filename" : getFilenameFromPath(entry.name)})
            else:
                res.append(getListFromFolder(folder+"/"+entry.name))
    return res

def path_contains_md(path):
    print(path)
    print(glob.glob(path+"/**/*.md", recursive=True))
    if len(glob.glob(path+"/**/*.md", recursive=True)) == 0:
        print ("false")
        return False
    else:
        print("True")
        return True

def path_hierarchy(path):
    hierarchy = {
        'type': 'folder',
        'name': os.path.basename(path).replace(".md", ""),
        'path': path,
    }

    try:
        if(len(os.listdir(path)) > 0):
            hierarchy['children'] = []
            blah = os.listdir(path)
            if blah:
                blah.sort()
            for contents in blah:
                fullpath = os.path.join(path, contents)
                if (os.path.isdir(fullpath) and path_contains_md(fullpath)) or (os.path.isfile(fullpath) and fullpath.split(".")[-1] == "md"):
                    hierarchy['children'].append(path_hierarchy(os.path.join(path, contents)))
    except OSError as e:
        if e.errno != errno.ENOTDIR:
            raise
        hierarchy['type'] = 'file'

    return hierarchy

def updateFileTree():
    basepath = 'FWGenDoc'
    filesa = path_hierarchy(basepath)
    print(filesa)
    
    f = open("/tmp/filesa", "w")
    f.write(str(filesa))
    f.close()

def cloneRepo():
    cloneSuccess = False
    if(not os.path.exists("gitLock")):
        while(not cloneSuccess):
            try:
                open("gitLock", 'a').close()
                print("Trying to clone repo")
                subprocess.run(["rm", "-R", "FWGenDoc"], timeout=90)
                subprocess.run(["git", "clone", "git.dev.ewon.biz:fwr/doc/general", "FWGenDoc"], timeout=20)
                print("Successfully cloned repo")
                cloneSuccess = True

                updateFileTree()
                generate_search_page()

            except subprocess.TimeoutExpired:
                print("Timeout...Retrying")

def getFilesa():
    if os.path.isfile("/tmp/filesa"):
        f = open("/tmp/filesa", "r")
        res = f.read()
        f.close()
        return eval(res)
    else:
        return ""

def writeStatus(status):
    f = open("/tmp/status", "w")
    f.write(str(status))
    f.close()


def getStatus():
    if os.path.isfile("/tmp/status"):
        f = open("/tmp/status", "r")
        res = f.read()
        f.close()
        return eval(res)
    else:
        return ""

def changeStatus(key, value):
    status = getStatus()
    status[key] = value
    writeStatus(status)

def getCommitID():
    repo = git.Repo('./FWGenDoc')
    return repo.head.object.hexsha

def _get_leaves_helper(tree, leaves):
    if tree['type'] == "folder":
        for child in tree['children']:
            _get_leaves_helper(child, leaves)
    else:
        leaves.append(tree)

def get_leaves(tree):
    leaves = []
    _get_leaves_helper(tree, leaves)
    return leaves


def url_can_be_converted_to_data(tag):
    return tag.name.lower() == "img" and tag.has_attr('src') and not re.match('^data:', tag['src'])


def beautifulsoup_action(html, context_path, set_image_to_base64):
    soup = BeautifulSoup(html, 'html.parser')
    allp = soup.find_all('p')
    for p in allp:
        if str(p.contents[0]) == "<strong>Note:</strong>" or str(p.contents[0]) == "<b>Note:</b>": 
            p['class'] = "note"
        if str(p.contents[0]) == "<strong>Warning:</strong>" or str(p.contents[0]) == "<b>Warning:</b>": 
            p['class'] = "warning"
        m = re.search('(.*)(==)([^\s].*[^\s])(==)(.*)', p.getText())
        if m:
            tag = soup.new_tag("p")
            tagem = soup.new_tag("em")
            tagem.string = m.group(1)
            tag.append(tagem)
            tagem = soup.new_tag("em")
            tagem['class'] = "highlight"
            tagem.string = m.group(3)
            tag.append(tagem)
            tagem = soup.new_tag("em")
            tagem.string = m.group(5)
            tag.append(tagem)
            p.replace_with(tag)
    allli = soup.find_all('li')
    for li in allli:
        m = re.search('(.*)(==)([^\s].*[^\s])(==)(.*)', li.getText())
        if m:
            tag = soup.new_tag("li")
            tagem = soup.new_tag("em")
            tagem.string = m.group(1)
            tag.append(tagem)
            tagem = soup.new_tag("em")
            tagem['class'] = "highlight"
            tagem.string = m.group(3)
            tag.append(tagem)
            tagem = soup.new_tag("em")
            tagem.string = m.group(5)
            tag.append(tagem)
            p.replace_with(tag)
    if set_image_to_base64:
        for link in soup.findAll(url_can_be_converted_to_data):
            image_url = context_path + "/" + link['src']
            print(image_url)
            image = open(image_url, "rb").read()
            encoded = base64.b64encode(image).decode('ascii')

            mime="image/jpeg"
            if ".svg" in image_url.lower():
                mime="image/svg+xml"
            elif ".png" in image_url.lower():
                mime="image/png"
            link['src'] = "data:"+mime+";base64," + str(encoded)
    return soup.prettify()

def beautifulsoup_action_remove_iamges(html):
    soup = BeautifulSoup(html, 'html.parser')
    allimg = soup.find_all('img')
    for img in allimg:
        img.decompose()
    return soup.prettify()

def generate_search_page():
    searchhtml=""
    basepath = 'FWGenDoc'
    filesa = getFilesa()
    leaves = get_leaves(filesa)
    print("---------------leaves")
    print(leaves)

    for f in leaves:
        print(f)
        path = f['path']
        path = path.replace("FWGenDoc/", "", 1)
        path = path.replace("/"," • ")

        searchhtml+="<a style=\"color:white;\" id=\"file\" class=\"fileclass\" href=\"/mdgs/view/"+ f['path'] +"\">"+path+"</a>"

        if os.path.isfile(f['path']):
            f = open(f['path'], "r")
            # https://github.com/Python-Markdown/markdown/tree/master/markdown/extensions
            md = markdown.Markdown(extensions=[TocExtension(), FencedCodeExtension(), CodeHiliteExtension(guess_lang= False, linenums=True), TableExtension()])
            #md = markdown.Markdown(extensions=[MyExtension(), TocExtension(), FencedCodeExtension(), CodeHiliteExtension(linenums=True)])
            mdHTMLed = md.convert(f.read())
            mdHTMLed = beautifulsoup_action(mdHTMLed, None, False)
            mdHTMLed = beautifulsoup_action_remove_iamges(mdHTMLed)
        searchhtml+=mdHTMLed

        searchhtml+="</br>"
    
    f = open("/tmp/search", "w")
    f.write(str(searchhtml))
    f.close()
    print(strftime("%d %b %Y %H:%M:%S", localtime()))


def periodicAction():
    threading.Timer(300.0, periodicAction).start()

###########################################################
## MAIN  ##################################################
###########################################################

app = FastAPI()
app.mount(baseURL+"/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
print("a############################################################")


periodicAction()

print("b############################################################")

###########################################################
## Endpoints ##############################################
###########################################################

@app.get("/favicon.ico")
def favicon():
    raise HTTPException(status_code=404, detail="Item not found")

@app.get('/{file_path:path}.jpg')
def show_subpathpng(file_path: str, request: Request):
    f = open("./static/"+file_path+".jpg", "rb")
    return StreamingResponse(f, media_type="image/jpeg")

@app.get('/{file_path:path}.JPG')
def show_subpathpng(file_path: str, request: Request):
    f = open("./static/"+file_path+".JPG", "rb")
    return StreamingResponse(f, media_type="image/jpeg")

@app.get('/{file_path:path}.mp4')
def show_subpathpng(file_path: str, request: Request):
    f = open("./static/"+file_path+".mp4", "rb")
    return StreamingResponse(f, media_type="image/jpeg")

@app.get('/{file_path:path}.MP4')
def show_subpathpng(file_path: str, request: Request):
    f = open("./static/"+file_path+".MP4", "rb")
    return StreamingResponse(f, media_type="image/jpeg")

@app.get('/sync')
def op(request: Request):
    global resizing_file_counter
    global resizing_file_len
    files_to_resize = gen_files_to_resize()
    resizing_file_len = len(files_to_resize)
    for file in files_to_resize:
        resizing_file_counter += 1
        if '.jpg' in file:
            ny = Image(filename =file)
            with ny.clone() as r:
                r.resize(240,240)
                r.save(filename=file.replace("media", "thumbs"))
        elif '.mp4' in file:
            print(file)
            video_input_path = file
            img_output_path = file.replace("media", "thumbs")
            subprocess.call(['ffmpeg', '-i', video_input_path, '-ss', '00:00:00.000', '-vframes', '1', '-f', 'image2', img_output_path])
            os.rename(img_output_path, img_output_path.replace(".mp4", ".jpg"))
            ny = Image(filename =img_output_path.replace(".mp4", ".jpg"))
            with ny.clone() as r:
                r.resize(240,240)
                r.save(filename=img_output_path.replace(".mp4", ".jpg"))
                os.rename(img_output_path.replace(".mp4", ".jpg"), img_output_path)

    resizing_file_counter = 0
    resizing_file_len = 0

def gen_files_to_resize():
    files_to_resize = []

    rootdir_a = './static/data/media/'
    files_a = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(rootdir_a):
        for file in f:
            if '.jpg' in file or '.mp4' in file:
                files_a.append(os.path.join(r, file))

    rootdir_b = './static/data/thumbs/'
    files_b = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(rootdir_b):
        for file in f:
            if '.jpg' in file or '.mp4' in file:
                files_b.append(os.path.join(r, file))

    for file in files_a:
        if file.replace("media", "thumbs") not in files_b:
            files_to_resize.append(file)

    return files_to_resize

@app.get('/sync_status')
def synced(request: Request):
    files_to_resize = gen_files_to_resize()
    return {"yet_to_resize": len(files_to_resize), "currently resizing": "%d/%d" % (resizing_file_counter, resizing_file_len)}

            

@app.get('/{file_path:path}', response_class=HTMLResponse)
def show_subpath(file_path: str, request: Request):
    html_folder = ""
    html = ""
    rootdir = './static/data/media/%s' % file_path
    for file in sorted(os.listdir(rootdir)):
        d = os.path.join(rootdir, file)
        if os.path.isdir(d):
            print(d)
            html_folder += "<a href=%s>%s</a></br>" % ("%s/%s" % (file_path,file), file)
        if ".jpg" in d:
            print("a")
            exif = {}
            with Image(filename=d) as image:
                exif.update((k[5:], v) for k, v in image.metadata.items() if k.startswith('exif:'))
            print("b")
            html += """
            <a data-lg-size="1400-1400" class="gallery-item" data-src="./data/media/%s" data-sub-html="<div id='toto'>%s</div>">
            <img class="img-fluid" src="./data/thumbs/%s" />
            </a>
            """ % ("%s/%s" % (file_path,file), "%s, %s" % (file, str(exif)), "%s/%s" % (file_path,file))
        if ".mp4" in d:
            html += """
            <a data-lg-size=1280-720 
               data-pinterest-text="Pin it3" 
               data-tweet-text="lightGallery slide  4" 
               data-video='{"source": [{"src":"./data/media/%s", "type":"video/mp4"}], "attributes": {"preload": false, "controls": true}}' 
               data-poster=./data/thumbs/%s
               data-sub-html="<h4>ROLLIN' SAFARI - 'Meerkats' - what if animals were round?</h4>">
                  <img class=img-fluid src=./data/thumbs/%s>
            </a>""" % ("%s/%s" % (file_path,file), "%s/%s" % (file_path,file), "%s/%s" % (file_path,file))

    return templates.TemplateResponse("index.html", {"request": request, "html": html, "html_folder":html_folder})

