# -*- coding: utf-8 -*-
from pydeps.colors import rgb2css, brightness, brightnessdiff, colordiff, name2rgb, foreground

red = (255, 0, 0)
green = (0, 255, 0)
yellow = (0, 255, 255)
blue = (0, 0, 255)
black = (0, 0, 0)
white = (255, 255, 255)


def test_rgb2css():
    assert rgb2css(*red) == '#ff0000'
    assert rgb2css(*green) == '#00ff00'
    assert rgb2css(*yellow) == '#00ffff'
    assert rgb2css(*blue) == '#0000ff'
    assert rgb2css(*black) == '#000000'
    assert rgb2css(*white) == '#ffffff'


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
        return foreground(name2rgb(name), black, white)

    assert fg('hello') == fg('hello.world')


# def visualize():
#     pass
#     #
#     # module = 'being.blue'
#     # t = name2rgb(module)
#     # bgcolor = rgb2css(*t)
#     # black = (0,0,0)
#     # white = (255, 255, 255)
#     # blackdiff = colordiff(t, black)
#     # whitediff = colordiff(t, white)
#     # whitebright = abs(brightness(*t) - brightness(*white))
#     # blackbright = abs(brightness(*t) - brightness(*black))
#     # print t
#     # print '      diff:           bright:'
#     # print 'white       %3d (%d)           %3d (%d) %3d' % (whitediff, whitediff > 500, whitebright, whitebright > 125, whitediff + whitebright)
#     # print 'black       %3d (%d)           %3d (%d) %3d' % (blackdiff, blackdiff > 500, blackbright, blackbright > 125, blackdiff + blackbright)
#     #
#     # open('tmp.html', 'w').write("""
#     # <html>
#     # <head>
#     # <style>
#     # html { background-color: %(bgcolor)s; }
#     # </style>
#     # <body>
#     #   <h1 style="color:white">%(module)s %(whitebright)s %(whitediff)s</h1>
#     #   <h1 style="color:black">%(module)s %(blackbright)s %(blackdiff)s</h1>
#     # </body>
#     # </html>
#     # """ % globals())
#     #
#     # os.system("firefox tmp.html")
