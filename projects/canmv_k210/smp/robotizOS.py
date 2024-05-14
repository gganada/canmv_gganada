import touchscreen as ts
from machine import I2C
import lcd, image
import time
from maix import GPIO
from fpioa_manager import fm
import gc  # Garbage collection
import math
import sensor


# Initialize peripherals
fm.register(16, fm.fpioa.GPIOHS0)
btn = GPIO(GPIO.GPIOHS0, GPIO.IN)
i2c = I2C(I2C.I2C0, freq=400000, scl=30, sda=31)
lcd.init()
image.font_load(image.UTF8, 16, 16, 0xA00000)
ts.init(i2c)
lcd.clear()
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_windowing((320, 240))
sensor.run(1)
sensor.set_vflip(1)
sensor.set_hmirror(1)

img_origin = image.Image(copy_to_fb=True)
gc.collect()
img_buf = b'\x30\x00\x00'
hueLogo = image.Image(img_buf, from_bytes = True)

breakLoop = 0
btnToggle = 0
btnPress = 0

TnPList = []
QueueIndex = 0

faceTimer = 0





def draw_multiline_text(img, x, y, text, color = (255,255,255), scale = 1.0, plus = 0):
    global language
    lines = text.split('\n')  # 개행 문자를 기준으로 문자열을 분리합니다.
    xpace = 2
    yspace = 0
    if scale == 1:
        xpace = 0
    for i, line in enumerate(lines):
        # 각 줄을 개별적으로 그립니다. y 위치는 줄 번호에 따라 조정됩니다.
        if line == "Setting":
            img.draw_string(x, y + math.ceil((i) * (20+scale + yspace) - (2 - scale) * 10) + plus, line, color = color, scale = scale, x_spacing = 2)
        else:
            img.draw_string(x, y + math.ceil((i) * (20+scale + yspace) - (2 - scale) * 10) + plus, line, color = color, scale = scale, x_spacing = xpace)



class Div:
    def __init__(self, img=None):
        self.view = 0   # 0 - 보이지 않음, 1 - 정적 div, 2 - 동적 div
        self.contents = []
        self.img = img
        self.parent = None
        self.bound = [0, 0, 0, 0]
        self.clickEvent = None
        self.pressEvent = None
        self.tsStatus = 1

    def set(self, view):
        self.view = view

    def setimg(self, img):
        self.img = img

    def getCimg(self):
        return self.img

    def setparent(self, parent):
        parent.boundPlus(self.bound)
        self.parent = parent
        self.img = parent.getCimg()

    def boundPlus(self, bound):
        self.bound[0] = min(self.bound[0], bound[0])
        self.bound[1] = min(self.bound[1], bound[1])
        self.bound[2] = max(self.bound[2], bound[2])
        self.bound[3] = max(self.bound[3], bound[3])

    def put(self, content):
        content.setparent(self)
        self.contents.append(content)

    def viewinit(self):
        if self.view == 1:
            self.draw(self.img)
        for i in self.contents:
            i.viewinit()

    def draw(self, img):
        pass

    def render(self, img):
        if self.view == 2:
            self.draw(img)
        for i in self.contents:
            i.render(img)

    def clickE(self, status, x, y):
        if self.isbound(x, y):
            if self.clickEvent:
                self.clickEvent(x, y)
            for i in self.contents:
                i.clickE(status, x, y)

    def pressE(self, status, x, y):
        if self.isbound(x, y):
            if self.pressEvent:
                self.pressEvent(x, y)
            for i in self.contents:
                i.pressE(status, x, y)

    def clickEMain(self, status, x, y):
        if self.tsStatus != 1 and status == 1 and self.isbound(x, y):
            if self.clickEvent:
                self.clickEvent(x, y)
            for i in self.contents:
                i.clickE(status, x, y)

        elif status == 3:
            if self.pressEvent:
                self.pressEvent(x, y)
            for i in self.contents:
                i.pressE(status, x, y)

        self.tsStatus = status


    def clickEset(self,  event):
        self.clickEvent = event

    def pressEset(self,  event):
        self.pressEvent = event


    def show(self):
        lcd.display(self.img)

    def isbound(self, x, y):
        return self.bound[0] < x < self.bound[2] and self.bound[1] < y < self.bound[3]

    def destroy(self):
        for i in self.contents:
            i.destroy()
        gc.collect()
        del self
        gc.collect()

class ButtonDiv(Div):
    def __init__(self, img=None):
        super().__init__()
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0
        self.color = (255, 255, 255)
        self.fill = False
        if img: self.img = img

    def set(self, view, x, y, w, h, color=(255, 255, 255), fill=False):
        self.view = view
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.bound = [x, y, x + w, y + h]
        self.color = color
        self.fill = fill

        if self.parent:
            self.parent.boundPlus(self.bound)

    def draw(self, img):
        img.draw_rectangle(self.x, self.y, self.w, self.h, self.color, fill=self.fill)

class CircleDiv(Div):
    def __init__(self):
        super().__init__()
        self.x = 0
        self.y = 0
        self.r = 0
        self.color = (255, 255, 255)
        self.fill = False

    def set(self, view, x, y, r, color=(255, 255, 255), fill=False):
        self.view = view
        self.x = x
        self.y = y
        self.r = r
        self.color = color
        self.fill = fill

    def setparent(self, parent):
        self.parent = parent
        self.img = parent.getCimg()

    def setLoc(self,x,y):
        if(x > self.parent.bound[2] - self.r):
            self.x = self.parent.bound[2] - self.r
        elif(x < self.parent.bound[0] + self.r):
            self.x = self.parent.bound[0] + self.r
        else:
            self.x = x

        if(y > self.parent.bound[3] - self.r):
            self.y = self.parent.bound[3] - self.r
        elif(y < self.parent.bound[1] + self.r):
            self.y = self.parent.bound[1] + self.r
        else:
            self.y = y

    def draw(self, img):
        img.draw_circle(self.x, self.y, int(self.r), self.color, fill=self.fill)


class CircleDiv2(Div):
    def __init__(self):
        super().__init__()
        self.x = 0
        self.y = 0
        self.r = 0
        self.color = (255, 255, 255)
        self.fill = False
        self.parentDiv = None

    def set(self, view, x, y, r, color=(255, 255, 255), fill=False):
        self.view = view
        self.x = x
        self.y = y
        self.r = r
        self.color = color
        self.fill = fill

    def setParentDiv(self,parentDiv):
        self.parentDiv = parentDiv        

    def setparent(self, parent):
        self.parent = parent
        self.img = parent.getCimg()

    def setLoc(self,x,y):
        if(x > self.parent.bound[2] - self.r):
            self.x = self.parent.bound[2] - self.r
        elif(x < self.parent.bound[0] + self.r):
            self.x = self.parent.bound[0] + self.r
        else:
            self.x = x

        if(y > self.parent.bound[3] - self.r):
            self.y = self.parent.bound[3] - self.r
        elif(y < self.parent.bound[1] + self.r):
            self.y = self.parent.bound[1] + self.r
        else:
            self.y = y

    def draw(self, img):
        if(self.parentDiv != None):
            (x,y,canDraw) = self.parentDiv.getXYCandraw()
            if(canDraw == True):
                img.draw_circle(135 + x, 10+ y, int(self.r), self.color, fill=self.fill)




class CameraDiv(Div):
    def draw(self, img):
        img.draw_image(sensor.snapshot(),0,0)

class TextDiv(ButtonDiv):
    def __init__(self):
        super().__init__()
        self.text = ''
        self.scale = 1.6
        self.color2 = (64,125,224)
        self.plus = 0

    def set(self, view, x, y, w, h, txt, color=(255,255,255)):
        self.view = view
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.bound = [x, y, x + w, y + h]
        self.color = color
        self.fill = False
        self.text = txt
        self.canDraw = True

    def getXYCandraw(self):
        return (self.x,self.y,self.canDraw)

    def draw(self, img):
        if(self.canDraw):
            img.draw_rectangle(self.x, self.y, self.w, self.h, self.color2, fill=self.fill)
            img.draw_rectangle(self.x, self.y, self.w, self.h, self.color, fill=False)
            draw_multiline_text(img, self.x + 15, self.y + 5, self.text,color = self.color, scale = self.scale, plus = self.plus)

class CustomDiv(Div):
    def __init__(self, img= None):
        super().__init__()
        self.drawFn = None
        self.view =2
    def draw(self, img):
        if(self.drawFn):
            self.drawFn(img)

def extract_floats(text):

    floats = []
    current_number = ""

    for char in text:
        if char.isdigit() or char in ".+-":
            current_number += char
        else:
            if current_number:
                try:
                    floats.append(float(current_number))
                except ValueError:
                    pass  # Ignore invalid format
                current_number = ""

    if current_number:
        try:
            floats.append(float(current_number))
        except ValueError:
            pass

    return floats