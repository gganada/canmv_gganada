import time
import math
import robot

import sensor
import image
import lcd
import KPU as kpu

import led

led.init()
import _thread

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_vflip(1)
sensor.run(1)
lcd.init(freq=15000000)
task = kpu.load(0x300000)
kpu.set_outputs(task, 0, 20, 15, 30)
anchor = (1.08, 1.19, 3.42, 4.41, 6.63, 11.38, 9.42, 5.11, 16.62, 10.52)
kpu.init_yolo2(task, 0.5, 0.3, 5, anchor)

pos = [0,300,0]
turnrate =0
uppos = 0
lent = 300

faceState = 0

class FaceThreadgoin(object):
    def __init__(self):
        self._stop = True
        self.nt = threadNN()
        pass
    def start(self):
        if self._stop is True:
            self.nt.start()
    def stop(self):
        self._stop = True
        self.nt.stop()


class threadNN(object):
    def __init__(self):
        self.st = faceState
    def start(self):
        _thread.start_new_thread(self._loop,())
    def stop(self):
        _thread.exit()
    def _loop(self):
        while True:
            varChange = 0
            crnState = faceState
            for i in range(10):
                if crnState != faceState:
                    break
                if i == 0:
                    if crnState == 0:
                        normalFace()
                    else:
                        smile()
                if i == 7:
                    if crnState == 0:
                        nnFace()
                    else:
                        nnFace1()
                time.sleep(0.1)




#tt = _thread.start_new_thread(faceThreadNormal,())
tt = FaceThreadgoin()
tt.start()
def nnFace():
    for i in range(50):
        led.setColor(i,0,0,0)
    led.setColorList([10,11,12,13,14],30,0,0)
    led.setColorList([35,36,37,38,39],30,0,0)
    led.show()

def nnFace1():
    for i in range(50):
        led.setColor(i,0,0,0)
    led.setColorList([10,11,12,13,14],0,30,0)
    led.setColorList([35,36,37,38,39],0,30,0)
    led.show()

def smile():
    for i in range(50):
        led.setColor(i,0,0,0)
    led.setColorList([2,6,7,8,10,11,13,14],0,30,0)
    led.setColorList([2+25,6+25,7+25,8+25,10+25,11+25,13+25,14+25],0,30,0)
    led.show()

def normalFace():
    for i in range(50):
        led.setColor(i,0,0,0)
    led.setColorList([1,2,3,5,9,10,14,15,19,21,22,23],30,0,0)
    led.setColorList([1+25,2+25,3+25,5+25,9+25,10+25,14+25,15+25,19+25,21+25,22+25,23+25],30,0,0)
    led.show()

#robot.moveG0(0,300,0,wait = True)
while True:
    time.sleep(0.002)
    img = sensor.snapshot()
    fmap = kpu.run_yolo2(task, img)
    output = fmap
    if output != None:
        maxSize = 0
        maxSizeIndex = 0
        for i in output:
            faceSize = i.w() * i.h()
            if maxSize < faceSize:
                maxSize = faceSize
                maxSizeIndex = i.index()
        i = output[maxSizeIndex]
        t = robot.isMoving()
        if(t==0):

            if(i.x()+i.w() > 260):
                turnrate = turnrate + 0.1

            if(i.x() < 60):
                turnrate = turnrate - 0.1
            if(i.y() < 40):
                if(robot.checkXYZ(pos[0],pos[1],uppos+10)==1):
                    uppos = uppos + 10

            elif(i.y()+i.h() > 200):
                if(robot.checkXYZ(pos[0],pos[1],uppos-10)==1):
                    uppos = uppos - 10
            x = lent * math.sin(turnrate)
            y = lent*math.cos(turnrate)
            z = uppos
            if(robot.checkXYZ(x,y,z)==1):
                pos[0] = lent * math.sin(turnrate)
                pos[1] = lent*math.cos(turnrate)
                pos[2] = uppos
                #print("x: "+str(pos[0])+"y: "+str(pos[1])+"z: "+str(pos[2]))

            robot.moveG0(pos[0],pos[1],pos[2], wait = False)

        img.draw_rectangle(i.x(), i.y(), i.w(), i.h())

        img.draw_string(i.x(),i.y(), str(t), scale = 3)
        #img.draw_string(i.x(),i.y(), str(xpos), scale = 3)
        lcd.display(img)
        if faceState == 0:

            faceState =1
            #tt.stop()
            #tt.start()

    else:
        img.draw_string(10,10,"nothing found", scale =3)
        lcd.display(img)

        if faceState == 1:
            faceState = 0
            #tt.stop()
            #tt.start()