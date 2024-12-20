from fastapi import FastAPI, HTTPException, File, UploadFile, Request, Response, Form, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Header
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse, StreamingResponse, RedirectResponse
from pathlib import Path
import os
import glob
import subprocess    # for video thumbnails
from wand.image import Image   # sudo apt-get install libmagickwand-dev        pip3 install Wand
import time

resizing_media_file_counter = 0
resizing_media_file_len = 0
resizing_file_counter = 0
resizing_file_len = 0
ORIG_NAME="orig"
MEDIA_NAME="media"
THUMBS_NAME="thumbs"
ORIG_PATH='./static/data/%s/' % ORIG_NAME
MEDIA_PATH='./static/data/%s/' % MEDIA_NAME
THUMBS_PATH='./static/data/%s/' % THUMBS_NAME
THUMBS_QUALITY=30
MEDIA_SIZE=720

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

# https://evilmartians.com/chronicles/better-web-video-with-av1-codec

# https://stribny.name/blog/fastapi-video/
@app.get('/{file_path:path}.mp4')
def show_subpathpng(file_path: str, request: Request):
    f = open("./static/"+file_path+".mp4", "rb")
    return StreamingResponse(f, media_type="image/jpeg")

@app.get('/{file_path:path}.MP4')
def show_subpathpng(file_path: str, request: Request):
    f = open("./static/"+file_path+".MP4", "rb")
    return StreamingResponse(f, media_type="image/jpeg")

CHUNK_SIZE = 1024*1024
@app.get('/video')
async def video_endpoint(range: str = Header(None)):
    video_path = Path("./static/data/media/Stream1_AV1_720p_1.5mbps.webm")
    start, end = range.replace("bytes=", "").split("-")
    start = int(start)
    end = int(end) if end else start + CHUNK_SIZE
    with open(video_path, "rb") as video:
        video.seek(start)
        data = video.read(end - start)
        filesize = str(video_path.stat().st_size)
        headers = {
            'Content-Range': f'bytes {str(start)}-{str(end)}/{filesize}',
            'Accept-Ranges': 'bytes'
        }
        return Response(data, status_code=206, headers=headers, media_type="video/mp4")

def show_subpathpng(file_path: str, request: Request):
    f = open("./static/"+file_path+".mp4", "rb")
    return StreamingResponse(f, media_type="image/jpeg")

def createDirIfNotExist(filenameordirectoryname):
    newfoldername=os.path.dirname(filenameordirectoryname)
    if not os.path.exists(newfoldername): os.makedirs(newfoldername)

@app.get('/gen_media')
def gen_media(request: Request, photo: bool = False, video: bool = False):
    global resizing_media_file_counter
    global resizing_media_file_len
    files_to_resize = gen_files_to_resize(ORIG_PATH, ORIG_NAME, MEDIA_PATH, MEDIA_NAME)
    resizing_media_file_len = len(files_to_resize)
    for file in files_to_resize:
        resizing_media_file_counter += 1
        newfilename=file.replace(ORIG_NAME, MEDIA_NAME)
        createDirIfNotExist(newfilename)
        if '.jpg' in file and photo:
            ny = Image(filename =file)
            with ny.clone() as r:
                pct = (MEDIA_SIZE/max(r.size))
                new_width = int(r.size[0]*pct)
                new_height = int(r.size[1]*pct)
                r.resize(new_width, new_height)
                r.save(filename=newfilename)
        elif '.mp4' in file and video:
            # https://en.wikipedia.org/wiki/HTML5_video
            # https://trac.ffmpeg.org/wiki/Encode/AV1
            subprocess.run(["ffmpeg", "-i", file, "-c:v", "libaom-av1" ,"-crf", "32", "-b:v", "0", newfilename])

    resizing_media_file_counter = 0
    resizing_media_file_len = 0

@app.get('/gen_thumbs')
def gen_thumbs(request: Request):
    global resizing_file_counter
    global resizing_file_len
    files_to_resize = gen_files_to_resize(MEDIA_PATH, MEDIA_NAME, THUMBS_PATH, THUMBS_NAME)
    resizing_file_len = len(files_to_resize)
    for file in files_to_resize:
        resizing_file_counter += 1
        newfilename=file.replace(MEDIA_NAME, THUMBS_NAME)
        createDirIfNotExist(newfilename)
        if '.jpg' in file:
            ny = Image(filename =file)
            with ny.clone() as r:
                s = min(r.size)
                r.crop(width=s, height=s, gravity='center')
                r.sample(240,240)
                r.compression_quality = THUMBS_QUALITY
                r.save(filename=newfilename)
        elif '.mp4' in file:
            video_input_path = file
            subprocess.call(['ffmpeg', '-i', video_input_path, '-ss', '00:00:00.000', '-vframes', '1', '-f', 'image2', newfilename])
            os.rename(newfilename, newfilename.replace(".mp4", ".jpg"))
            ny = Image(filename =newfilename.replace(".mp4", ".jpg"))
            with ny.clone() as r:
                r.resize(240,240)
                r.compression_quality = THUMBS_QUALITY
                r.save(filename=newfilename.replace(".mp4", ".jpg"))
                os.rename(newfilename.replace(".mp4", ".jpg"), newfilename)

    resizing_file_counter = 0
    resizing_file_len = 0

def gen_files_to_resize(rootdir_a, name_a, rootdir_b, name_b):
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
        if file.replace(name_a, name_b) not in files_b:
            files_to_resize.append(file)

    return files_to_resize

@app.get('/sync_status')
def synced(request: Request,  full_log: bool = False):
    res = {}
    if full_log:
        thumbs_to_generate = gen_files_to_resize(MEDIA_PATH, MEDIA_NAME, THUMBS_PATH, THUMBS_NAME)
        media_to_generate = gen_files_to_resize(ORIG_PATH, ORIG_NAME, MEDIA_PATH, MEDIA_NAME)
        res["thumbs_yet_to_resize"] = len(thumbs_to_generate)
        res["media_yet_to_resize"] = len(media_to_generate)
    res["currently resizing thumbs"] = "%d/%d" % (resizing_file_counter, resizing_file_len)
    res["currently resizing media"] = "%d/%d" % (resizing_media_file_counter, resizing_media_file_len)
    return res

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
            exif = {}
            with Image(filename=d) as image:
                exif.update((k[5:], v) for k, v in image.metadata.items() if k.startswith('exif:'))
            html += """
            <a data-lg-size="1400-1400" class="gallery-item" data-src="./data/media/%s" data-sub-html="<div id='toto'>%s</div>">
            <img class="img-fluid" src="./data/thumbs/%s" />
            </a>
            """ % ("%s/%s" % (file_path,file), "%s, %s" % (file, str(exif)), "%s/%s" % (file_path,file))
        if ".webm" in d:
            html += """
            <a data-lg-size=1280-720 
               data-pinterest-text="Pin it3" 
               data-tweet-text="lightGallery slide  4" 
               data-video='{"source": [{"src":"%s", "type":"video/mp4"}], "attributes": {"preload": false, "controls": true}}' 
               data-poster=./data/thumbs/%s
               data-sub-html="<h4>ROLLIN' SAFARI - 'Meerkats' - what if animals were round?</h4>">
                  <img class=img-fluid src=./data/thumbs/%s>
            </a>""" % ("video", "%s/%s" % (file_path,file), "%s/%s" % (file_path,file))

    return templates.TemplateResponse("index.html", {"request": request, "html": html, "html_folder":html_folder})