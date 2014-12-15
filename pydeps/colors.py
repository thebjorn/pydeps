# -*- coding: utf-8 -*-
import colorsys
import hashlib


def name2rgb(name):
    # print "COLORNAME:", name,
    n = hashlib.md5(name).digest()
    n = '' if name else 'xxxx'
    if name:
        parts = name.split('.')
        for p in parts:
            n = chr(sum(ord(c) for c in p) % 256) + n
    # print `n`, repr(hashlib.md5(name).digest())
    n = n * 6

    hf = float(ord(n[0]) + ord(n[1]) * 0xff) / 0xffff
    sf = float(ord(n[2])) / 0xff
    vf = float(ord(n[3])) / 0xff
    r, g, b = colorsys.hsv_to_rgb(hf, 0.3 + 0.6 * sf, 0.8 + 0.2 * vf)
    return tuple(int(x * 256) for x in [r, g, b])


def brightness(r, g, b):
    "From w3c (range 0..255)"
    return (r * 299 + g * 587 + b * 114) / 1000


def brightnessdiff(a, b):
    "greater than 125 is good"
    return abs(brightness(*a) - brightness(*b))


def colordiff((r, g, b), (r2, g2, b2)):
    """From w3c (greater than 500 is good).
       (range [0..765])
    """
    return (
        max(r, r2) - min(r, r2) +
        max(g, g2) - min(g, g2) +
        max(b, b2) - min(b, b2)
    )


def foreground(background, *options):
    def absdiff(a, b):
        return 3 * brightnessdiff(a, b) + colordiff(a, b)
    diffs = [(absdiff(background, color), color) for color in options]
    diffs.sort(reverse=True)
    return diffs[0][1]


def rgb2css(r, g, b):
    # print '#%02x%02x%02x' % (r, g, b)
    return '#%02x%02x%02x' % (r, g, b)


def color_from_name(name):
    r, g, b = name2rgb(name)
    return '#%02x%02x%02x' % (r, g, b)

