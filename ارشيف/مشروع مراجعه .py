from turtle import *
from colorsys import*
setup (800,725)
speed(0.6)
tracer (10)
bgcolor("black")
h=0
for i in range (360):
    c = hsv_to_rgb(h, 1, 1)
    color(c)
    h += 0.005
    circle(150)
    left(2)
done()