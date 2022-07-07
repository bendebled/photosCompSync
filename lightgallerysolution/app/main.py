from fastapi import FastAPI, HTTPException, File, UploadFile, Request, Form, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse, StreamingResponse, RedirectResponse
import os
import glob
import subprocess    # for video thumbnails
from wand.image import Image   # sudo apt-get install libmagickwand-dev        pip3 install Wand
import time

resizing_file_counter = 0
resizing_file_len = 0
ORIG_PATH='./static/data/orig/'
MEDIA_PATH='./static/data/media/'
THUMBS_PATH='./static/data/thumbs/'


###########################################################
## Helper functions #######################################
###########################################################


###########################################################
## MAIN  ##################################################
###########################################################

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
print("###")

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

@app.get('/gen_media')
def gen_media(request: Request):
    global resizing_media_file_counter
    global resizing_media_file_len
    files_to_resize = gen_files_to_resize(ORIG_PATH, MEDIA_PATH)
    resizing_media_file_len = len(files_to_resize)
    for file in files_to_resize:
        resizing_media_file_counter += 1
        if '.jpg' in file:
            ny = Image(filename =file)
            with ny.clone() as r:
                pct = (720/max(r.size))
                new_width = int(r.size[0]*pct)
                new_height = int(r.size[1]*pct)
                r.resize(new_width, new_height)
                r.compression_quality = 30
                r.save(filename=file.replace("orig", "media"))
        elif '.mp4' in file:
            pass
    resizing_media_file_counter = 0
    resizing_media_file_len = 0

@app.get('/gen_thumbs')
def gen_thumbs(request: Request):
    global resizing_file_counter
    global resizing_file_len
    files_to_resize = gen_files_to_resize(MEDIA_PATH, THUMBS_PATH)
    resizing_file_len = len(files_to_resize)
    for file in files_to_resize:
        resizing_file_counter += 1
        if '.jpg' in file:
            ny = Image(filename =file)
            with ny.clone() as r:
                s = min(r.size)
                r.crop(width=s, height=s, gravity='center')
                r.sample(240,240)
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

def gen_files_to_resize(rootdir_a, rootdir_b):
    files_to_resize = []

    files_a = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(rootdir_a):
        for file in f:
            if '.jpg' in file or '.mp4' in file:
                files_a.append(os.path.join(r, file))

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
    thumbs_to_generate = gen_files_to_resize(MEDIA_PATH, THUMBS_PATH)
    media_to_generate = gen_files_to_resize(ORIG_PATH, MEDIA_PATH)
    return {"thumbs_yet_to_resize": len(thumbs_to_generate), 
            "currently resizing thumbs": "%d/%d" % (resizing_file_counter, resizing_file_len)
            "media_yet_to_resize": len(media_to_generate), 
            "currently resizing media": "%d/%d" % (resizing_file_counter, resizing_file_len)}

            

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