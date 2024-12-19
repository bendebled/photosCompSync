from wand.image import Image   # sudo apt-get install libmagickwand-dev        pip3 install Wand

#ny = Image(filename='5.jpg')
#with ny.clone() as r:
#    s = min(r.size)
#    r.crop(width=s, height=s, gravity='center')
#    r.sample(240,240)
#    r.save(filename='thumb.jpg')

ny = Image(filename='5.jpg')
with ny.clone() as r:
    pct = (720/max(r.size))
    new_width = int(r.size[0]*pct)
    new_height = int(r.size[1]*pct)
    #r.transform("%f%%" % s)
    r.resize(new_width, new_height)
    r.compression_quality = 30
    r.save(filename='media.jpg')
