#!/usr/bin/env python
# encoding: utf-8
"""
picture.py

Created by geng xinyue on 2011-03-16.
Copyright (c) 2011 douban.com. All rights reserved.
"""

import math
from cStringIO import StringIO
import sys

import Image
import ImageEnhance


def pic_rect(content, x, y, w, h, max_length=120, min_length=70, quality=88):
    im = open_pic(content)
    try:
        #cannot less than min_length
        w = max(w, min_length)
        h = max(h, min_length)
        max_l = max(w, h)
        #crop a rect
        new = im.crop((x, y, x+w, y+h))
        #zoom_out
        if max_l > max_length:
            ww = w
            hh = h
            # w > h
            if max_l > h:
                hh = hh * max_length // ww
                ww = max_length
            # h > w
            elif max_l > w:
                ww = ww * max_l // hh
                hh = max_length
            else:
                ww = hh = max_length
            new = new.resize((ww, hh), Image.ANTIALIAS)

        ie = ImageEnhance.Sharpness(new)
        new = ie.enhance(1.2)
        f = StringIO()
        new.save(f, 'JPEG', quality=quality)
        return f.getvalue()
    except IOError, e:
        if e.message == "cannot read interlaced PNG files":
            raise UnknownPictureError()
        else:
            raise
    del im

def open_pic(image):
    """open a picture, and normalize

    image: a PIL Image object, image content string or file-like object
    """

    if hasattr(image, 'getim'): # a PIL Image object
        im = image
    else:
        if not hasattr(image, 'read'): # image content string
            image = StringIO(image)
        try:
            im = Image.open(image) # file-like object
        except IOError, e:
            if e.message == "cannot identify image file":
                raise UnknownPictureError()
            else:
                raise

    # use a white background for transparency effects
    # (alpha band as paste mask).
    if im.mode == 'RGBA':
        p = Image.new('RGBA', im.size, 'white')
        try:
            x, y = im.size
            p.paste(im, (0, 0, x, y), im)
            im = p
        except:
            pass
        del p

    if im.mode == 'P':
        need_rgb = True
    elif im.mode == 'L':
        # grey bitmap, fix fog cover
        need_rgb = True
    elif im.mode == 'CMYK':
        # fix the dark background
        need_rgb = True
    else:
        need_rgb = False

    if need_rgb:
        im = im.convert('RGB', dither=Image.NONE)

    return im

pic_open = open_pic


class PictureError(Exception): message = 'Picture Error'
class UnknownPictureError(PictureError): message = 'Unknown Picture'

### 图片处理算法框架函数

def _pic(box_size, quality, sharp, image, sizer, crop=False):
    """sub-picture in the box

    box_size: size of sub-picture's box, (width, height), or (x, y)
    quality: sub-picture's quality, int
    image: original image's content, string or file
    sizer: compute the new picture's size, function(box_size, orig_size)
    return: new sub-picture's content, string
    """
    im = open_pic(image)

    # new size
    x, y = sizer(box_size, im.size)
    try:
        new = im.resize((x, y), Image.ANTIALIAS)
    except IOError, e:
        if e.message == "cannot read interlaced PNG files":
            raise UnknownPictureError()
        else:
            raise
    del im

    if crop:
        hx, hy = box_size[0]/2, box_size[1]/2
        new = new.crop((x/2-hx, y/2-hy, x/2+hx, y/2+hy))

    # adjust the blurred image after resize operation
    if sharp is not None:
        ie = ImageEnhance.Sharpness(new)
        new = ie.enhance(sharp)

    f = StringIO()
    new.save(f, 'JPEG', quality=quality)
    return f.getvalue()

### 计算新图片的尺寸，所有函数均以sizer_开头

def sizer_inner(box_size, original_size):
    """sub-picture innerconnect the box, same ratio as the original image

    box_size: (x, y), size of box
    original_size: (x, y), size of original picture
    return: (x, y), size of new picture
    """
    boxx, boxy = box_size
    ox, oy = original_size

    y = boxx*oy/ox
    if y > boxy:
        y = boxy
        x = boxy*ox/oy
    else:
        x = boxx

    return x, y

def sizer_inner_zoom_in(box_size, original_size):
    """innerconnect the box or small then the box(zoom in only), same ratio
    """
    x, y = sizer_inner(box_size, original_size)
    ox, oy = original_size
    if x > ox or y > oy:
        return original_size
    else:
        return (x, y)

def sizer_inner_square(box_size, original_size):
    """User Icon, zoom in only
    """
    assert box_size[0] == box_size[1]
    bx, by = box_size
    ox, oy = original_size

    if ox == bx and oy >= by or oy == by and ox >= bx:
        return original_size
    else:
        if ox > oy:
            x, y = ox*bx/oy, by
        else:
            x, y = bx, oy*by/ox
        return (x, y)

### 图片处理的算法，所有函数均以pic_开头

def pic_inner(width, height, quality, sharp, image):
    """sub-picture innerconnect the box, have same ratio as original image
    """
    return _pic((width, height), quality, sharp, image, sizer_inner)

def pic_inner_zoom_in(width, height, quality, sharp, image):
    """sub-picture innerconnect the box, zoom in only
    """
    return _pic((width, height), quality, sharp, image, sizer_inner_zoom_in)

def pic_width_zoom_cut(width, height, quality, sharp, image):
    image = pic_open(image)
    x, y = image.size
    #x/y = width/height
    #缩放到width,剪裁掉height
    cuted_height = x*height//width
    if cuted_height < y:
        width_begin = 0
        height_begin = (y-cuted_height)//2
        image = image.crop((width_begin, height_begin, width_begin+x, height_begin+cuted_height))
    else:
        height = y*width//x
    image = image.resize((width, height), Image.ANTIALIAS)
    f = StringIO()
    image.save(f, 'JPEG', quality=95)
    return f.getvalue()


def pic_inner_square(width, height, quality, sharp, image):
    """generate small cover of subject
    """
    return _pic((width, height), quality, sharp, image,
            sizer_inner_square, crop=True)


class ConfigError(Exception):
    pass

class SubPicture:
    def __init__(self, domain, config, picture):
        """根据原始照片生成指定规格图片

        domain: string
        config: dict
        - "domain": str -> dict
          - "catetgory" ('s name): str -> dict
            - (category's) short_name: string
            - (box's) width: int
            - (box's) height: int
            - (jpeg's) quality: int
            - algorithm ('s name, or function's name): string
        picture: string, content of original picture
        """
        self.domain = domain
        if config is None:
            raise ConfigError('no config for domain(%s)' % domain)
        else:
            self.config = config
        self.content = picture

        # 如果可能，用中间图生成其他小图，用来提高运算速度
        self._middle_cate = ''
        mw = mh = 0
        if len(self.config) > 1:
            heights = []
            widths = []
            algorithms = []
            for category, conf in self.config.items():
                heights.append([conf['height'], category])
                widths.append([conf['width'], category])
                algorithms.append(conf['algorithm'])
            # 只有所有小图使用同一算法的才能使用中间图
            if len(set(algorithms)) == 1:
                max_height = sorted(heights)[-1]
                max_width = sorted(widths)[-1]
                max_height_category = max_height[1]
                max_width_category = max_width[1]
                # 只有在所有小图里宽和高都是最大值的，才能作为中间图
                if max_height_category == max_width_category:
                    self._middle_cate = max_height_category
                    mw = max_width[0]
                    mh = max_height[0]


    def generate(self, category, content=None):
        config = self.config.get(category)
        if not config:
            raise ConfigError('no config for domain(%s).category(%s)' % (
                self.domain, category))

        width = config['width']
        height = config['height']
        quality = config['quality']
        sharp = config['sharp']
        algorithm = globals()['pic_%s' % config['algorithm']]

        return algorithm(width, height, quality, sharp,
                content or self.content)

    def generate_all(self):
        all = []
        if self._middle_cate:
            # 用中间图生成其他小图
            middle = self.generate(self._middle_cate)
            all.append([self._middle_cate, middle])
            for category in self.config.keys():
                if category != self._middle_cate:
                    all.append([category, self.generate(category, middle)])
        else:
            for category in self.config.keys():
                all.append([category, self.generate(category)])
        return all

def open_file(filename, mode='r'):
    f = filename
    if not hasattr(f, 'read'):
        f = open(f, mode=mode)
    return f

def album_square(source_file, new_file, width, top_left=None, size=0):
    new_content = pic_square(open_file(source_file).read(), width,
            top_left=top_left, size=size, zoom_out=False)
    open_file(new_file, 'w').write(new_content)

def pic_album_square(width, height, quality, sharp, image):
    assert width == height
    return pic_square(image, width, top_left=None, size=0, zoom_out=False)

def pic_square(content, width, top_left=None, size=0, zoom_out=False):
    im = open_pic(content)

    x, y = im.size
    zoom_out, resize, crop, zoom_in, background, paste =      \
            _calc_square(x, y, width, top_left, size, zoom_out)

    if zoom_out and resize:
        im = im.resize(resize, Image.ANTIALIAS)

    (ax, ay, bx, by) = crop
    if not ((ax, ay) == (0, 0) and (bx, by) == im.size):
        im = im.crop(crop)

    if not (zoom_out and resize):
        if zoom_in:
            try:
                im = im.resize((width, width), Image.ANTIALIAS)
            except:
                raise PictureError
        if background:
            p = Image.new('RGBA', (width, width), 'white')
            p.paste(im, paste)
            im = p
            del p

    f = StringIO()
    im.save(f, 'JPEG', quality=95)
    return f.getvalue()

def pic_inner_cut(width, height, quality, sharp, image):
    image = pic_open(image)
    x, y = image.size
    #x*height > width*y 缩放到height,剪裁掉width
    is_cut_width = (x*height > width*y)
    if is_cut_width:
        cuted_height = height
        cuted_width = x*height//y
    else:
        cuted_height = y*width//x
        cuted_width = width

    image = image.resize((cuted_width, cuted_height), Image.ANTIALIAS)
    x, y = image.size
    if is_cut_width:
        width_begin = (x-width)//4
        height_begin = 0
    else:
        width_begin = 0
        height_begin = (y-height)//4
    image = image.crop((width_begin, height_begin, width_begin+width, height_begin+height))
    f = StringIO()
    image.save(f, 'JPEG', quality=95)
    return f.getvalue()

def _calc_square(x, y, width, top_left, size, zoom_out):
    height_delta = width
    default = True # 是否使用默认缩放策略
    if top_left is not None:
        try:
            ax, ay = top_left
            if ax < 0 or ay < 0:
                default = True
            elif size <= 0:
                default = True
            elif ax + size > x:
                default = True
            elif ay + size > y:
                default = True
            else:
                # 用户指定了合法的参数，则使用用户指定缩放策略
                default = False
        except:
            pass

    resize = None
    if default:
        zoom_in = (x > width and y > width)
        background = (x < width or y < width)

        # 如果图过小，需要粘贴在一个白色背景的图片上
        px, py = (width-x)/2, (width-y)/2
        if px < 0:
            px = 0
        if py < 0:
            py = 0
        paste = (px, py)

        # 如果允许放大，就不再需要往白色背景图片上粘贴
        if zoom_out and background:
            zoom_out = x < y and 'x' or 'y'
            if zoom_out == 'x':
                nx = width
                ny = width*y/x
            else:
                nx = width*x/y
                ny = width
            resize = (nx, ny)

            x, y = resize
            ax, ay = (x-width)/2, (y-width)/2
            if ax < 0:
                ax = 0
            if ay < 0:
                ay = 0
            bx = ax + width
            by = ay + width
        else:
            # 计算如何缩小
            if x > width and y > width:
                if x > y:
                    ax, bx = (x-y)/2, (x+y)/2
                    ay, by = 0, y
                else:
                    ax, bx = 0, x
                    ay, by = (y-x)/2, (y+x)/2
                    height_delta = x
            else:
                ax, ay, bx, by = (x-width)/2, (y-width)/2, (x+width)/2, (y+width)/2
                if ax < 0:
                    bx += ax
                    ax = 0
                if ay < 0:
                    by += ay
                    ay = 0

        # 高 > 宽时，需要调整，上方、下方切掉的区域高度比例要是 1:3。
        if y > x and y > width:
            ay -= (y - height_delta) / 4
            by -= (y - height_delta) / 4
        if bx > x:
            bx = x
        if by > y:
            by = y
        crop = [ax, ay, bx, by]
    else:
        zoom_in = (size != width)
        crop = [ax, ay, ax + size, ay + size]
        background = False
        paste = (0, 0)
    return zoom_out, resize, crop, zoom_in, background, paste




