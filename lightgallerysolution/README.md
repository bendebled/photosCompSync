# MDGS

## Installation

**From dev env:**
```
cd /opt/ewondev/flaskmdgs
docker-compose build
docker-compose push
```

**From mdgs server:**
```
cd /home/bede/mdgs
docker-compose pull
docker-compose up #interactive
docker-compose start # as a deamon
```

**Note:**
The following `docker-compose.yml` should be on the server:

```
version: "3"
services:
  signing-server:
    build: .
    image: docker.dev.ewon.biz/doc/mdgs:latest
    restart: always
    volumes:
      - /root/.git:/git
    environment:
      - MAX_WORKERS=1
      - USER=svc-niv-git-mdgs
    ports:
```

## References

* Masonary Layout
* https://css-tricks.com/piecing-together-approaches-for-a-css-masonry-layout/
* https://codeburst.io/how-to-the-masonry-layout-56f0fe0b19df 