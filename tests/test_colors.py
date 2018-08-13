# -*- coding: utf-8 -*-
import os

from pydeps.colors import rgb2css, brightness, brightnessdiff, colordiff, name2rgb, foreground

red = (255, 0, 0)
green = (0, 255, 0)
yellow = (0, 255, 255)
blue = (0, 0, 255)
black = (0, 0, 0)
white = (255, 255, 255)


def test_rgb2css():
    assert rgb2css(red) == '#ff0000'
    assert rgb2css(green) == '#00ff00'
    assert rgb2css(yellow) == '#00ffff'
    assert rgb2css(blue) == '#0000ff'
    assert rgb2css(black) == '#000000'
    assert rgb2css(white) == '#ffffff'


def test_brightness():
    assert brightnessdiff(yellow, white) < brightnessdiff(yellow, black)


def test_colordiff():
    assert colordiff(blue, yellow) < colordiff(blue, red)


def test_foreground():
    assert foreground(black, red, green, yellow, blue, black, white) == white
    assert foreground(black, red, green, yellow, blue, black) == yellow
    assert foreground(black, red, green, blue, black) == green
    assert foreground(black, red, blue, black) == red
    assert foreground(black, blue, black) == blue


def test_name2rgb():
    def fg(name):
        return foreground(
            name2rgb(13),
            black, white)

    assert fg('hello') == fg('hello.world')
