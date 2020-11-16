import os.path
import math
from urllib.parse import quote as urlencode
from PIL import Image
from jinja2 import Markup


def make_imagefilters(millionpages):

    basepath = millionpages.exportpath
    image_cache = {}

    def rounddown(f):
        return (int)(math.floor(f) + 0.00001)

    def generate_image(rgbimg, outputmode, imgtimestamp, filepath, width, height):
        target = os.path.join(basepath, filepath[1:])

        if millionpages.destination_needs_writing(target, imgtimestamp):
            img = rgbimg.copy()
            imgwidth, imgheight = img.size
            imgratio = 1.0 * imgwidth / imgheight

            targetratio = 1.0 * width / height
            if imgratio < targetratio:  # width bound
                w = width
                h = rounddown((1.0 * w / imgwidth) * imgheight)
                yoffset = rounddown((h - height) / 2.0)
                xoffset = 0
                destsize = (w, h)
            else:  # height bound
                h = height
                w = rounddown((1.0 * h / imgheight) * imgwidth)
                xoffset = rounddown((w - width) / 2.0)
                yoffset = 0
                destsize = (w, h)
            img.thumbnail(destsize, Image.ANTIALIAS)  # right scale
            box = (xoffset, yoffset, width + xoffset, height + yoffset)
            img = img.crop(box)

            img.convert(outputmode)
            img.save(target)

    def generate_images(rgbimg, outputmode, imgtimestamp, srcset):
        for entry in srcset:
            generate_image(rgbimg, outputmode, imgtimestamp, *entry)

    def imageurl(filepath, width, height=0):
        source = os.path.join(basepath, filepath[1:])

        safe = "/@"
        if not os.path.isfile(source):
            return Markup(f"{urlencode(filepath, safe=safe)}")

        imgtimestamp = os.path.getmtime(source)

        cached_imginfo = image_cache.get(filepath, (None, None))
        if cached_imginfo and cached_imginfo[1] and cached_imginfo[1] >= imgtimestamp:
            img = cached_imginfo[0]
            imgmode = img.mode
        else:
            img = Image.open(source)
            imgmode = img.mode
            if img.mode == "1":
                img = img.convert("L")
            elif img.mode == "L":
                pass
            img = img.convert("RGB")
            image_cache[filepath] = (img, imgtimestamp)

        imgwidth, imgheight = img.size
        imgratio = 1.0 * imgwidth / imgheight
        if not height:
            reqratio = imgratio
        else:
            reqratio = width / height

        def srcsetentry(filepath, width, height=0):
            if not height:
                height = rounddown(width / imgratio)
            name, ext = os.path.splitext(filepath)
            srcpath = f"{name}@{width}w{height}h{ext}"
            return (srcpath, width, height)

        srcinfo = srcsetentry(filepath, width, height)

        if not height:
            generate_image(img, imgmode, imgtimestamp, *srcinfo)
        else:
            generate_image(img, imgmode, imgtimestamp, *srcinfo)

        safe = "/@"
        return Markup(f"{urlencode(srcinfo[0], safe=safe)}")

    def imageattrs(filepath, width, height=0):
        source = os.path.join(basepath, filepath[1:])

        if not os.path.isfile(source):
            return Markup(f' src="{filepath}" ')

        imgtimestamp = os.path.getmtime(source)

        cached_imginfo = image_cache.get(filepath, (None, None))
        if cached_imginfo and cached_imginfo[1] and cached_imginfo[1] >= imgtimestamp:
            img = cached_imginfo[0]
            imgmode = img.mode
        else:
            img = Image.open(source)
            imgmode = img.mode
            if img.mode == "1":
                img = img.convert("L")
            elif img.mode == "L":
                pass
            img = img.convert("RGB")
            image_cache[filepath] = (img, imgtimestamp)

        imgwidth, imgheight = img.size
        imgratio = 1.0 * imgwidth / imgheight
        if not height:
            reqratio = imgratio
        else:
            reqratio = width / height

        def srcsetentry(filepath, width, height=0):
            if not height:
                height = rounddown(width / imgratio)
            name, ext = os.path.splitext(filepath)
            srcpath = f"{name}@{width}w{height}h{ext}"
            return (srcpath, width, height)

        srcset = []
        for multiplier in (1, 2, 3):  # @1x, @2x, @3x
            if multiplier * width < imgwidth and (
                not height or multiplier * height < imgheight
            ):
                srcset.append(
                    srcsetentry(filepath, multiplier * width, multiplier * height)
                )

        if not height:
            generate_images(
                img, imgmode, imgtimestamp, srcset
            )  # no need to generate original
            srcset.append((filepath, imgwidth, imgheight))
        else:
            if imgratio > reqratio:  # image wider than requested, so crop width
                srcwidth = rounddown(reqratio * imgheight)
                srcheight = imgheight
            else:
                srcwidth = imgwidth
                srcheight = rounddown(imgwidth / reqratio)
            srcset.append(srcsetentry(filepath, srcwidth, srcheight))
            generate_images(img, imgmode, imgtimestamp, srcset)

        src = srcset[-1]

        safe = "/@"
        srcsetentries = ", ".join(
            [f"{urlencode(src[0], safe=safe)} {src[1]}w" for src in srcset]
        )
        return Markup(
            f' src="{urlencode(src[0], safe=safe)}" srcset="{srcsetentries}" '
        )

    return {"imageurl": imageurl, "imageattrs": imageattrs}
