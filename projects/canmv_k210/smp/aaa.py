import touchscreen as ts
from machine import I2C
import lcd, image
import time
from maix import GPIO, utils
from fpioa_manager import fm
import gc  # Garbage collection
import math
import sensor
from modules import ws2812


# Initialize peripherals
fm.register(16, fm.fpioa.GPIOHS0)
fm.register(14, fm.fpioa.GPIOHS14) ## new button
## led = 15번
led = ws2812(15, 2)
led.set_led(0,(0,0,0))
led.set_led(1,(0,0,0))
led.display()


btn = GPIO(GPIO.GPIOHS0, GPIO.IN)
btn2 = GPIO(GPIO.GPIOHS14, GPIO.IN)
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
# img_buf = b'\x30\x00\x00'
# hueLogo = image.Image('/flash/huenitLogo.jpeg')
# hueLogo = image.Image(img_buf, from_bytes = True)[]
hueLogo = image.Image('/flash/blk.jpg')


breakLoop = 0
btnToggle = 0
btnToggle2 = 0
btnPress = 0
btnPress2 = 0
btn_tick_hue = time.ticks_ms()
TnPList = []
QueueIndex = 0

faceTimer = 0
whatToSave = None


def find_index(value, lst):
    # # print("value = ",value)
    # # print("lst = ",lst)
    try:
        # 리스트에서 값의 인덱스를 찾습니다.
        
        index = lst.index(value)
        return index
    except ValueError:
        # 값이 리스트에 없는 경우 None을 반환합니다.
        return None

def dataLoadingFunction(loadNum):
    global img_origin
    # print("loading")
    import json
    savetxt = "로 딩 완 료"
    if img_origin:
        img_origin.draw_rectangle(60,70,200,100,color = (0,0,0), fill = True)
        img_origin.draw_rectangle(60,70,200,100,color = (255,255,255), fill = False)
        draw_multiline_text(img_origin,80,90,"로 딩 중 ...",color = (255,255,255), scale=1.6)
        lcd.display(img_origin)
        time.sleep(0.5)
    try:
        with open('aiData'+str(loadNum)+'.json','r') as file:
            data = json.load(file)
        # state_machine.current_state = STATE.CLASSIFY
        # EndTraining = True
        # print("loading success")
    except Exception as e:
        # print(e)
        data = []
        savetxt = "로 딩 실 패"
        # print("loading failed")


    if img_origin:
        img_origin.draw_rectangle(60,70,200,100,color = (0,0,0), fill = True)
        img_origin.draw_rectangle(60,70,200,100,color = (255,255,255), fill = False)
        draw_multiline_text(img_origin,80,90,savetxt,color = (255,255,255), scale=1.6)
        lcd.display(img_origin)
        time.sleep(0.5)
    return data




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



####################################################################################
#main
#main
#main
#main
#main
#main
#main
#main
#main
#main
#main
#main
#main
#main


dpPress = 0
longPressState = 0

mOff = 0

def showing():
    global viewPage
    # # print("viewPage",viewPage)
    if(isinstance(viewPage,Div)):
        # # print("viewPage, img = ",viewPage, viewPage.img)
        im = viewPage.getCimg()
        viewPage.render(im)
        viewPage.show()
    else:
        global prevPage, createMainPage, prevPageVar
        # # print("viewPageError", prevPage)
        if prevPageVar != None:
            switch_view(prevPage, prevPageVar)
        else:
            switch_view(prevPage)
        showing()
    gc.collect()

def switch_view(new_view_function, args = None):
    global viewPage
    gc.collect()
    if viewPage is not None:
        viewPage.destroy()  # Destroy the current view
        gc.collect()  # Explicitly run garbage collection
    if args != None:
        viewPage = new_view_function(args)  # Create the new view
    else:
        viewPage = new_view_function()  # Create the new view
    gc.collect()


def createMainPage():
    global img_origin
    img_origin.draw_rectangle(0,0,320,240,color = (0,0,0), fill = True)
    mainDiv = Div(img_origin)
    mainDiv.set(1)

    def breakNgotoMain(x,y):
        lcd.clear()
        gc.collect()
        import os, sys
        target = os.getcwd() + "/mainScript.py"
        with open(target, "r") as f:
            exec(f.read())
        global breakLoop
        breakLoop = 1

    def b1Event(x, y):
        switch_view(createPage1)

    def b2Event(x, y):
        switch_view(createPage2,False)

    def b3Event(x, y):
        switch_view(createPage3)

    def b4Event(x, y):
        switch_view(createPage4)

    def b5Event(x, y):
        switch_view(createPage5)
            
    def b6Event(x, y):
        switch_view(createPage6)

    mainButton1 = ButtonDiv()
    btn1txt = TextDiv()
    mainButton1.put(btn1txt)

    mainButton2 = ButtonDiv()
    btn2txt = TextDiv()
    mainButton2.put(btn2txt)

    mainButton3 = ButtonDiv()
    btn3txt = TextDiv()
    mainButton3.put(btn3txt)

    mainButton4 = ButtonDiv()
    btn4txt = TextDiv()
    mainButton4.put(btn4txt)

    mainButton5 = ButtonDiv()
    btn5txt = CustomDiv()
    btn5txt2 = CustomDiv()
    btn5txt.drawFn = (lambda img: img.draw_image(hueLogo,215,15))
    btn5txt2.drawFn = (lambda img: img.draw_rectangle(215,15,100,100,(255,255,255), fill = False))
    mainButton5.put(btn5txt)
    mainButton5.put(btn5txt2)
    

    mainButton6 = ButtonDiv()
    btn6txt = CustomDiv()
    btn6txt2 = CustomDiv()
    btn6txt.drawFn = (lambda img: img.draw_image(hueLogo,215,120))
    btn6txt2.drawFn = (lambda img: img.draw_rectangle(215,120,100,100,(255,255,255), fill = False))
    mainButton6.put(btn6txt)
    mainButton6.put(btn6txt2)

    mainButton1.set(2, 5, 15, 100, 100, (159, 123, 255), True)
    btn1txt.set(2, 5, 15, 100, 100, "직 접  학 습\n모 델")
    mainButton2.set(2, 110, 15, 100, 100, (64, 125, 224), True)
    btn2txt.set(2, 110, 15, 100, 100, "인 식  모 델")
    mainButton3.set(2, 5, 120, 100, 100, (64, 125, 224), True)
    btn3txt.set(2, 5, 120, 100, 100, "불 러 오 기")
    mainButton4.set(2, 110, 120, 100, 100, (159, 123, 255), True)
    btn4txt.set(2, 110, 120, 100, 100, "설 정"+ "\nSetting")
    mainButton5.set(2, 215, 15, 100, 100, (159, 123, 255), True)
    mainButton6.set(2, 215, 120, 100, 100, (64, 125, 224), True)

    mainButton1.clickEset(b1Event)
    mainButton2.clickEset(b3Event)
    mainButton3.clickEset(b2Event)
    mainButton5.clickEset(b4Event)
    mainButton4.clickEset(b5Event)
    mainButton6.clickEset(b6Event)

    mainDiv.put(mainButton1)
    mainDiv.put(mainButton2)
    mainDiv.put(mainButton3)
    mainDiv.put(mainButton4)
    mainDiv.put(mainButton5)
    mainDiv.put(mainButton6)


    huenitVerText = CustomDiv()
    huenitVerText.drawFn = (lambda img: img.draw_string(100,223,"Huenit X Robotis v0.1.0", color = (255,255,255), scale = 1))
    mainDiv.put(huenitVerText)

    mainDiv.viewinit()
    gc.collect()
    return mainDiv

def createPage1(): ## 직접 학습 모델
    # print("page1")
    global prevPage
    prevPage = createMainPage

    global img_origin
    img_origin.draw_rectangle(0,0,320,240,color = (0,0,0), fill = True)
    mainDiv = Div(img_origin)
    mainDiv.set(1)


    def b1Event(x, y):
        switch_view(classificationPage, False)

    def b2Event(x, y):
        switch_view(faceRecogPage, False)
        pass

    def b3Event(x, y):
        pass

    def b4Event(x, y):
        pass

    def b5Event(x, y):
        pass
            
    def b6Event(x, y):
        pass

    mainButton1 = ButtonDiv()
    btn1txt = TextDiv()
    mainButton1.put(btn1txt)

    mainButton2 = ButtonDiv()
    btn2txt = TextDiv()
    mainButton2.put(btn2txt)

    mainButton3 = ButtonDiv()
    btn3txt = CustomDiv()
    btn3txt2 = CustomDiv()
    btn3txt.drawFn = (lambda img: img.draw_image(hueLogo,5,120))
    btn3txt2.drawFn = (lambda img: img.draw_rectangle(5,120,100,100,(255,255,255), fill = False))
    mainButton3.put(btn3txt)
    mainButton3.put(btn3txt2)

    mainButton4 = ButtonDiv()
    btn4txt = CustomDiv()
    btn4txt2 = CustomDiv()
    btn4txt.drawFn = (lambda img: img.draw_image(hueLogo,110,120))
    btn4txt2.drawFn = (lambda img: img.draw_rectangle(110,120,100,100,(255,255,255), fill = False))
    mainButton4.put(btn4txt)
    mainButton4.put(btn4txt2)

    mainButton5 = ButtonDiv()
    btn5txt = CustomDiv()
    btn5txt2 = CustomDiv()
    btn5txt.drawFn = (lambda img: img.draw_image(hueLogo,215,15))
    btn5txt2.drawFn = (lambda img: img.draw_rectangle(215,15,100,100,(255,255,255), fill = False))
    mainButton5.put(btn5txt)
    mainButton5.put(btn5txt2)
    

    mainButton6 = ButtonDiv()
    btn6txt = CustomDiv()
    btn6txt2 = CustomDiv()
    btn6txt.drawFn = (lambda img: img.draw_image(hueLogo,215,120))
    btn6txt2.drawFn = (lambda img: img.draw_rectangle(215,120,100,100,(255,255,255), fill = False))
    mainButton6.put(btn6txt)
    mainButton6.put(btn6txt2)

    mainButton1.set(2, 5, 15, 100, 100, (159, 123, 255), True)
    btn1txt.set(2, 5, 15, 100, 100, "분 류  모 델")
    mainButton2.set(2, 110, 15, 100, 100, (64, 125, 224), True)
    btn2txt.set(2, 110, 15, 100, 100, "얼 굴  인 식\n모 델")
    mainButton3.set(2, 5, 120, 100, 100, (64, 125, 224), True)
    mainButton4.set(2, 110, 120, 100, 100, (159, 123, 255), True)
    mainButton5.set(2, 215, 15, 100, 100, (159, 123, 255), True)
    mainButton6.set(2, 215, 120, 100, 100, (64, 125, 224), True)

    mainButton1.clickEset(b1Event)
    mainButton2.clickEset(b2Event)
    mainButton3.clickEset(b3Event)
    mainButton5.clickEset(b4Event)
    mainButton4.clickEset(b5Event)
    mainButton6.clickEset(b6Event)

    mainDiv.put(mainButton1)
    mainDiv.put(mainButton2)
    mainDiv.put(mainButton3)
    mainDiv.put(mainButton4)
    mainDiv.put(mainButton5)
    mainDiv.put(mainButton6)


    huenitVerText = CustomDiv()
    huenitVerText.drawFn = (lambda img: img.draw_string(100,223,"Huenit X Robotis v0.1.0", color = (255,255,255), scale = 1))
    mainDiv.put(huenitVerText)

    mainDiv.viewinit()
    gc.collect()
    return mainDiv



########classification
#classification
#classification
#classification
#classification
#classification
#classification
#classification
#classification
#classification
#classification
#classification
#classification

def classificationPage(isLoad):
    gc.collect()
    from maix import KPU
    from board import board_info


    ####################################################################################################################
    class STATE(object):
        IDLE = 0
        INIT = 1
        TRAIN_CLASS_1 = 2
        TRAIN_CLASS_2 = 3
        TRAIN_CLASS_3 = 4
        TRAIN_CLASS_4 = 5
        CLASSIFY = 6
        STATE_MAX = 7


    class EVENT(object):
        POWER_ON = 0            # virtual event, 用于上电初始化
        BOOT_KEY = 1            # boot键按下
        BOOT_KEY_LONG_PRESS = 2 # boot键长按约3秒
        EVENT_NEXT_MODE = 3     # virtual event, 用于切换到下一个模式
        EVENT_MAX = 4


    class StateMachine(object):
        def __init__(self, state_handlers, event_handlers, transitions):
            self.previous_state = STATE.IDLE
            self.current_state = STATE.IDLE
            self.state_handlers = state_handlers
            self.event_handlers = event_handlers
            self.transitions = transitions

        def reset(self):
            '''
            重置状态机
            :return:
            '''
            self.previous_state = STATE.IDLE
            self.current_state = STATE.IDLE

        def get_next_state(self, cur_state, cur_event):
            '''
            根据当着状态和event, 从transitions表里查找出下一个状态
            :param cur_state:
            :param cur_event:
            :return:
                next_state: 下一状态
                None: 找不到对应状态
            '''
            for cur, next, event in self.transitions:
                if cur == cur_state and event == cur_event:
                    return next
            return None

        # execute action before enter current state
        def enter_state_action(self, state, event):
            '''
            执行当前状态对应的进入action
            :param state: 当前状态
            :param event: 当前event
            :return:
            '''
            try:
                if self.state_handlers[state][0]:
                    self.state_handlers[state][0](self, state, event)
            except Exception as e:
                print(e)

        # execute action of current state
        def execute_state_action(self, state, event):
            '''
            执行当前状态action函数
            :param state:   当前状态
            :param event:   当前event
            :return:
            '''
            try:
                if self.state_handlers[state][1]:
                    self.state_handlers[state][1](self, state, event)
            except Exception as e:
                print(e)

        # execute action when exit state
        def exit_state_action(self, state, event):
            '''
            执行当前状态的退出action
            :param state: 当前状态
            :param event: 当前event
            :return:
            '''
            try:
                if self.state_handlers[state][2]:
                    self.state_handlers[state][2](self, state, event)
            except Exception as e:
                print(e)

        def emit_event(self, event):
            '''
            发送event。根据当前状态和event，查找下一个状态，然后执行对应的action。
            :param event: 要发送的event
            :return:
            '''
            next_state = self.get_next_state(self.current_state, event)

            # execute enter function and exit function when state changed
            if next_state != None and next_state != self.current_state:
                self.exit_state_action(self.previous_state, event)
                self.previous_state = self.current_state
                self.current_state = next_state
                self.enter_state_action(self.current_state, event)
                print("event valid: {}, cur: {}, next: {}".format(event, self.current_state, next_state))

            # call state action for each event
            self.execute_state_action(self.current_state, event)

        def engine(self):
            '''
            状态机引擎，用于执行状态机
            :return:
            '''
            pass

    def restart(self):
        '''
        重新启动状态机程序
        :return:
        '''
        pass
        global features
        self.reset()
        features.clear()
        self.emit_event(EVENT.POWER_ON)


    def enter_state_idle(self, state, event):
        print("enter state: idle")


    def exit_state_idle(self, state, event):
        print("exit state: idle")


    def state_idle(self, state, event):
        global central_msg
        print("current state: idle")
        central_msg = None


    def enter_state_init(self, state, event):
        global img_origin
        print("enter state: init")
        img_origin = image.Image(size=(lcd.width(), lcd.height()))


    def exit_state_init(self, state, event):
        print("exit state: init")



    def state_init(self, state, event):
        print("current state: init, event: {}".format(event))

        # switch to next state when boot key is pressed
        if event == EVENT.BOOT_KEY:
            self.emit_event(EVENT.EVENT_NEXT_MODE)
        elif event == EVENT.BOOT_KEY_LONG_PRESS:
            # restart(self)
            return


    def enter_state_train_class_1(self, state, event):
        print("enter state: train class 1")
        global train_pic_cnt, central_msg, bottom_msg
        train_pic_cnt = 0
        central_msg = "Train class 1"
        bottom_msg = "Take pictures of 1st class"


    def exit_state_train_class_1(self, state, event):
        print("exit state: train class 1")


    def state_train_class_1(self, state, event):
        global kpu, central_msg, bottom_msg, features, train_pic_cnt, TL_msg, TR_msg
        global state_machine, currentID, img_origin
        currentID = 1
        print("current state: class 1")

        if event == EVENT.BOOT_KEY_LONG_PRESS:
            # restart(self)
            return

        if train_pic_cnt == 0:  # 0 is used for prompt only
            features.append([])
            train_pic_cnt += 1
        elif train_pic_cnt <= max_train_pic:
            central_msg = None
            img_origin = sensor.snapshot()
            feature = kpu.run_with_output(img_origin, get_feature=True)
            features[0].append(feature)
            bottom_msg = "Class 1: #P{}".format(train_pic_cnt)
            TL_msg = "ID 1"
            TR_msg = "데 이 터\n{}".format(train_pic_cnt)
            train_pic_cnt += 1
        else:
            state_machine.emit_event(EVENT.EVENT_NEXT_MODE)


    def enter_state_train_class_2(self, state, event):
        print("enter state: train class 2")
        global train_pic_cnt, central_msg, bottom_msg
        train_pic_cnt = 0
        central_msg = "Train class 2"
        bottom_msg = "Change to 2nd class please"


    def exit_state_train_class_2(self, state, event):
        print("exit state: train class 2")


    def state_train_class_2(self, state, event):
        global kpu, central_msg, bottom_msg, features, train_pic_cnt, TL_msg, TR_msg
        global state_machine, currentID, img_origin
        currentID = 2
        print("current state: class 2")

        if event == EVENT.BOOT_KEY_LONG_PRESS:
            # restart(self)
            return

        if train_pic_cnt == 0:
            features.append([])
            train_pic_cnt += 1
        elif train_pic_cnt <= max_train_pic:
            central_msg = None
            img_origin = sensor.snapshot()
            feature = kpu.run_with_output(img_origin, get_feature=True)
            features[1].append(feature)
            bottom_msg = "Class 2: #P{}".format(train_pic_cnt)
            TL_msg = "ID 2"
            TR_msg = "데 이 터\n{}".format(train_pic_cnt)
            train_pic_cnt += 1
        else:
            state_machine.emit_event(EVENT.EVENT_NEXT_MODE)


    def enter_state_train_class_3(self, state, event):
        print("enter state: train class 3")
        global train_pic_cnt, central_msg, bottom_msg
        train_pic_cnt = 0
        central_msg = "Train class 3"
        bottom_msg = "Change to 3rd class please"


    def exit_state_train_class_3(self, state, event):
        print("exit state: train class 3")


    def state_train_class_3(self, state, event):
        global kpu, central_msg, bottom_msg, features, train_pic_cnt, TL_msg, TR_msg
        global state_machine, currentID, img_origin
        currentID = 3
        print("current state: class 3")

        if event == EVENT.BOOT_KEY_LONG_PRESS:
            # restart(self)
            return

        if train_pic_cnt == 0:
            features.append([])
            train_pic_cnt += 1
        elif train_pic_cnt <= max_train_pic:
            central_msg = None
            img_origin = sensor.snapshot()
            feature = kpu.run_with_output(img_origin, get_feature=True)
            features[2].append(feature)
            bottom_msg = "Class 3: #P{}".format(train_pic_cnt)
            TL_msg = "ID 3"
            TR_msg = "데 이 터\n{}".format(train_pic_cnt)
            train_pic_cnt += 1
        else:
            state_machine.emit_event(EVENT.EVENT_NEXT_MODE)

    ########## class 4

    def enter_state_train_class_4(self, state, event):
        print("enter state: train class 4")
        global train_pic_cnt, central_msg, bottom_msg
        train_pic_cnt = 0
        central_msg = "Train class 4"
        bottom_msg = "Change to 4rd class please"


    def exit_state_train_class_4(self, state, event):
        print("exit state: train class 4")


    def state_train_class_4(self, state, event):
        global kpu, central_msg, bottom_msg, features, train_pic_cnt, TL_msg, TR_msg
        global state_machine, currentID, img_origin
        currentID = 4
        print("current state: class 4")

        if event == EVENT.BOOT_KEY_LONG_PRESS:
            # restart(self)
            return

        if train_pic_cnt == 0:
            features.append([])
            train_pic_cnt += 1
        elif train_pic_cnt <= max_train_pic:
            central_msg = None
            img_origin = sensor.snapshot()
            feature = kpu.run_with_output(img_origin, get_feature=True)
            features[3].append(feature)
            bottom_msg = "Class 4: #P{}".format(train_pic_cnt)
            TL_msg = "ID 4"
            TR_msg = "데 이 터\n{}".format(train_pic_cnt)
            train_pic_cnt += 1
        else:
            state_machine.emit_event(EVENT.EVENT_NEXT_MODE)

    ############ class 4 end

    def enter_state_classify(self, state, event):
        global central_msg, bottom_msg
        print("enter state: classify")
        central_msg = "Classification"
        bottom_msg = "Training complete! Start classification"



    def exit_state_classify(self, state, event):
        print("exit state: classify")


    def state_classify(self, state, event):
        global central_msg, bottom_msg
        print("current state: classify, {}, {}".format(state, event))
        if event == EVENT.BOOT_KEY:
            central_msg = None
        if event == EVENT.BOOT_KEY_LONG_PRESS:
            # restart(self)
            return



    def event_power_on(self, value=None):
        print("emit event: power_on")


    def event_press_boot_key(self, value=None):
        global state_machine
        print("emit event: boot_key")


    def event_long_press_boot_key(self, value=None):
        global state_machine
        print("emit event: boot_key_long_press")


    # state action table format:
    #   state: [enter_state_handler, execute_state_handler, exit_state_handler]
    state_handlers = {
        STATE.IDLE: [enter_state_idle, state_idle, exit_state_idle],
        STATE.INIT: [enter_state_init, state_init, exit_state_init],
        STATE.TRAIN_CLASS_1: [enter_state_train_class_1, state_train_class_1, exit_state_train_class_1],
        STATE.TRAIN_CLASS_2: [enter_state_train_class_2, state_train_class_2, exit_state_train_class_2],
        STATE.TRAIN_CLASS_3: [enter_state_train_class_3, state_train_class_3, exit_state_train_class_3],
        STATE.TRAIN_CLASS_4: [enter_state_train_class_4, state_train_class_4, exit_state_train_class_4],
        STATE.CLASSIFY: [enter_state_classify, state_classify, exit_state_classify]
    }

    # event action table, can be enabled while needed
    event_handlers = {
        EVENT.POWER_ON: event_power_on,
        EVENT.BOOT_KEY: event_press_boot_key,
        EVENT.BOOT_KEY_LONG_PRESS: event_long_press_boot_key
    }

    # Transition table
    transitions = [
        [STATE.IDLE, STATE.INIT, EVENT.POWER_ON],
        [STATE.INIT, STATE.TRAIN_CLASS_1, EVENT.EVENT_NEXT_MODE],
        [STATE.TRAIN_CLASS_1, STATE.TRAIN_CLASS_2, EVENT.EVENT_NEXT_MODE],
        [STATE.TRAIN_CLASS_2, STATE.TRAIN_CLASS_3, EVENT.EVENT_NEXT_MODE],
        [STATE.TRAIN_CLASS_3, STATE.TRAIN_CLASS_4, EVENT.EVENT_NEXT_MODE],
        [STATE.TRAIN_CLASS_4, STATE.CLASSIFY, EVENT.EVENT_NEXT_MODE]
        # [STATE.TRAIN_CLASS_3, STATE.CLASSIFY, EVENT.EVENT_NEXT_MODE]
    ]


    ####################################################################################################################
    class Button(object):
        DEBOUNCE_THRESHOLD = 30  # 消抖阈值
        LONG_PRESS_THRESHOLD = 1000  # 长按阈值
        # Internal  key states
        IDLE = 0
        DEBOUNCE = 1
        SHORT_PRESS = 2
        LONG_PRESS = 3

        def __init__(self, state_machine):
            self._state = Button.IDLE
            self._key_ticks = 0
            self._pre_key_state = 1
            self.SHORT_PRESS_BUF = None
            self.st = state_machine

        def reset(self):
            self._state = Button.IDLE
            self._key_ticks = 0
            self._pre_key_state = 1
            self.SHORT_PRESS_BUF = None

        def key_up(self, delta):
            if self.SHORT_PRESS_BUF:
                self.st.emit_event(self.SHORT_PRESS_BUF)
            self.reset()

        def key_down(self, delta):
            if self._state == Button.IDLE:
                self._key_ticks += delta
                if self._key_ticks > Button.DEBOUNCE_THRESHOLD:
                    # main loop period过大时，会直接跳过去抖阶段
                    self._state = Button.SHORT_PRESS
                    self.SHORT_PRESS_BUF = EVENT.BOOT_KEY  # key_up 时发送
                else:
                    self._state = Button.DEBOUNCE
            elif self._state == Button.DEBOUNCE:
                self._key_ticks += delta
                if self._key_ticks > Button.DEBOUNCE_THRESHOLD:
                    self._state = Button.SHORT_PRESS
                    self.SHORT_PRESS_BUF = EVENT.BOOT_KEY  # key_up 时发送
            elif self._state == Button.SHORT_PRESS:
                self._key_ticks += delta
                if self._key_ticks > Button.LONG_PRESS_THRESHOLD:
                    self._state = Button.LONG_PRESS
                    self.SHORT_PRESS_BUF = None  # 检测到长按，将之前可能存在的短按buffer清除，以防发两个key event出去
                    self.st.emit_event(EVENT.BOOT_KEY_LONG_PRESS)
            elif self._state == Button.LONG_PRESS:
                self._key_ticks += delta
                # 最迟 LONG_PRESS 发出信号，再以后就忽略，不需要处理。key_up时再退出状态机。
                pass
            else:
                pass


    ####################################################################################################################
    def loop_init():
        global lcd, img_origin
        if state_machine.current_state != STATE.INIT:
            return

        img_origin.draw_rectangle(0, 0, lcd.width(), lcd.height(), color=(0, 0, 255), fill=True, thickness=2)
        img_origin.draw_string(65, 90, "Self Learning Demo", color=(255, 255, 255), scale=2)
        img_origin.draw_string(5, 210, "short press:   next", color=(255, 255, 255), scale=1)
        img_origin.draw_string(5, 225, "long press:      restart", color=(255, 255, 255), scale=1)
        lcd.display(img_origin)

    def loop_capture():
        global central_msg, bottom_msg, TL_msg, TR_msg, currentID, img_origin
        global MenuEnterState
        if MenuEnterState == True and img_origin != None:
            img_origin.draw_rectangle(0,50,320,140, color = (0,0,0), fill = True)
            
            img_origin.draw_rectangle(50,70,100,100, color = (64,125,224), fill = True)
            img_origin.draw_rectangle(50,70,100,100, color = (255,255,255), fill = False)
            draw_multiline_text(img_origin,70,75,"모 델  학 습\n완 료 하 기", scale = 1.6)

            img_origin.draw_rectangle(170,70,100,100, color = (159,123,255), fill = True)
            img_origin.draw_rectangle(170,70,100,100, color = (255,255,255), fill = False)
            draw_multiline_text(img_origin,190,75,"다 음  모 델 \n학 습 하 기", scale = 1.6)
        
            lcd.display(img_origin)
            return
            
        img_origin = sensor.snapshot()
        boxColor = None    
        if currentID == 1:
            boxColor = (138,60,255)
            pass            
        elif currentID == 2:
            boxColor = (255,255,0)
            pass            
        elif currentID == 3:
            boxColor = (0,255,255)
            pass            
        elif currentID == 4:
            boxColor = (255,51,153)
            pass
        
        if central_msg:
            img_origin.draw_rectangle(0, 90, lcd.width(), 22, color=(0, 0, 255), fill=True, thickness=2)
            img_origin.draw_string(55, 90, central_msg, color=(255, 255, 255), scale=2)
        if bottom_msg:
            pass
            # img_origin.draw_string(5, 208, bottom_msg, color=(0, 0, 255), scale=1)
        if TL_msg and TR_msg:
            draw_multiline_text(img_origin,20, 50, TL_msg, color = boxColor, scale = 1.3)
            draw_multiline_text(img_origin,285, 50, TR_msg, color = boxColor, scale = 1.3)
            # img_origin.draw_string(10, 50, TL_msg, color = (159, 123, 255), scale = 2)
            # img_origin.draw_string(200, 50, TR_msg, color = (159, 123, 255), scale = 2)
            



        img_origin.draw_rectangle(48, 8, 224,224, color = boxColor,fill = False, thickness = 2)
        img_origin.draw_line(160,100, 160, 140, color = boxColor, thickness = 2)
        img_origin.draw_line(140,120, 180, 120, color = boxColor, thickness = 2)

        img_origin.draw_rectangle(0,0, 320, 25, color = (100,100,100), fill = True)
        img_origin.draw_string(10, 3, "뒤 로", color = (0,0,0))
        img_origin.draw_string(130, 3, "분 류  모 델 ", color = (0,0,0), scale = 1.2)
        img_origin.draw_string(300, 3, "학 습", color = (0,0,0))



        lcd.display(img_origin)


    def loop_classify():
        global central_msg, bottom_msg, TL_msg, TR_msg, img_origin
        global MenuEnterState
        if MenuEnterState == True and img_origin != None:
            img_origin.draw_rectangle(0,50,320,140, color = (0,0,0), fill = True)
            
            img_origin.draw_rectangle(50,70,100,100, color = (64,125,224), fill = True)
            img_origin.draw_rectangle(50,70,100,100, color = (255,255,255), fill = False)
            draw_multiline_text(img_origin,70,75,"모 델  삭 제 \n및  재 학 습", scale = 1.6)

            img_origin.draw_rectangle(170,70,100,100, color = (159,123,255), fill = True)
            img_origin.draw_rectangle(170,70,100,100, color = (255,255,255), fill = False)
            draw_multiline_text(img_origin,190,75,"현 재  모 델 \n저 장 하 기", scale = 1.6)
            lcd.display(img_origin)
            return

        img_origin = sensor.snapshot()
        boxColor = (255,255,255)
        
        # gc.collect()
        # print("heap size before", gc.mem_free())
        # del(features)
        # gc.collect()
        # print("heap size after gc.collect", gc.mem_free())
        # features = [0]
        # time.sleep
        scores = []
        feature = kpu.run_with_output(img_origin, get_feature=True)
        high = 0
        index = 0
        for j in range(len(features)):
            # print(len(features[j]))
            for f in features[j]:
                # print(len(f))
                score = kpu.feature_compare(f, feature)
                if score > high:
                    high = score
                    index = j
        if high > THRESHOLD:
            bottom_msg = "class:{},score:{:2.1f}".format(index + 1, high)
            TL_msg = "ID {}".format(index+1)
            TR_msg = "확 률\n{:2.1f}".format(high)
            if(index + 1) == 1:
                boxColor = (138,60,255)
            elif(index + 1) == 2:
                boxColor = (255,255,0)
            elif(index + 1) == 3:
                boxColor = (0,255,255)
            elif(index + 1) == 4:
                boxColor = (255,51,153)
        else:
            bottom_msg = None
            TL_msg = None
            TR_msg = None
            boxColor = (255,255,255)



        # display info
        if central_msg:
            print("central_msg:{}".format(central_msg))
            # img_origin.draw_rectangle(0, 90, lcd.width(), 22, color=(0, 255, 0), fill=True, thickness=2)
            # img_origin.draw_string(55, 90, central_msg, color=(255, 255, 255), scale=2)
        if bottom_msg:
            print("bottom_msg:{}".format(bottom_msg))
            # img_origin.draw_string(5, 208, bottom_msg, color=(0, 255, 0), scale=1)
        if TL_msg and TR_msg:
            draw_multiline_text(img_origin,20, 50, TL_msg, color = boxColor, scale = 1.3)
            draw_multiline_text(img_origin,285, 50, TR_msg, color = boxColor, scale = 1.3)

        img_origin.draw_rectangle(48, 8, 224,224, color = boxColor,fill = False, thickness = 2)
        img_origin.draw_line(160,100, 160, 140, color = boxColor, thickness = 2)
        img_origin.draw_line(140,120, 180, 120, color = boxColor, thickness = 2)

        img_origin.draw_rectangle(0,0, 320, 25, color = (100,100,100), fill = True)
        img_origin.draw_string(10, 3, "뒤 로", color = (0,0,0))
        img_origin.draw_string(130, 3, "분 류  모 델 ", color = (0,0,0), scale = 1.2)
        img_origin.draw_string(300, 3, "학 습", color = (0,0,0))


        lcd.display(img_origin)

    ####################################################################################################################
    # main loop
    global features, THRESHOLD, train_pic_cnt, max_train_pic, central_msg, bottom_msg, boot_gpio, kpu, state_machine, btn_ticks_prev,boot_btn, TL_msg, TR_msg
    global boot_btn, currentID, MenuEnterState, img_origin
    features = []
    THRESHOLD = 98.5    
    train_pic_cnt = 0   
    max_train_pic = 5   

    central_msg = None  
    bottom_msg = None   
    
    TL_msg = None
    TR_msg = None
    currentID = None
    MenuEnterState = False

    boot_gpio = GPIO(GPIO.GPIOHS0, GPIO.IN)
    # sensor.skip_frames(time=500)  # Wait for settings take effect.

    kpu = KPU()
    print("ready load model")
    try:
        kpu.load_kmodel(0x300000,245104)
    except Exception as e:
        print(e)
        return
    

    haveToSave = False
    state_machine = StateMachine(state_handlers, event_handlers, transitions)
    state_machine.emit_event(EVENT.POWER_ON)

    btn_ticks_prev = time.ticks_ms()
    boot_btn = Button(state_machine)


    if isLoad != False:
        global img_origin
        print("loading")
        import json
        savetxt = "로 딩 완 료"
        if img_origin:
            img_origin.draw_rectangle(60,70,200,100,color = (0,0,0), fill = True)
            img_origin.draw_rectangle(60,70,200,100,color = (255,255,255), fill = False)
            draw_multiline_text(img_origin,80,90,"로 딩 중 ...",color = (255,255,255), scale=1.6)
            lcd.display(img_origin)
            time.sleep(0.5)
        try:
            with open('aiData'+str(isLoad)+'.json','r') as file:
                features = json.load(file)
            state_machine.current_state = STATE.CLASSIFY
            print("loading success")
        except Exception as e:
            print(e)
            features = []
            savetxt = "로 딩 실 패"
            print("loading failed")


        if img_origin:
            img_origin.draw_rectangle(60,70,200,100,color = (0,0,0), fill = True)
            img_origin.draw_rectangle(60,70,200,100,color = (255,255,255), fill = False)
            draw_multiline_text(img_origin,80,90,savetxt,color = (255,255,255), scale=1.6)
            lcd.display(img_origin)
            time.sleep(0.5)



    def btn2():
        nonlocal loopEscape

        loopEscape = True

    def btn1s():
        global boot_btn, MenuEnterState
        MenuEnterState = False
        boot_btn.st.emit_event(EVENT.BOOT_KEY)

    
    
    def btn1l():
        global boot_btn, MenuEnterState
        MenuEnterState = True
        boot_btn.st.emit_event(EVENT.BOOT_KEY_LONG_PRESS)
        

    (statusC, xC, yC) = ts.read()
    (statusC2, xC2, yC2) = (None,None,None)
    loopEscape = False
    while True:
        gc.collect()
        buttonEvent(btn1s,btn1l,btn2,btn2)

        if(loopEscape == True):
            break

        # btn_ticks_cur = time.ticks_ms()
        # delta = time.ticks_diff(btn_ticks_cur, btn_ticks_prev)
        # btn_ticks_prev = btn_ticks_cur
        # if boot_gpio.value() == 0:
        #     boot_btn.key_down(delta)
        # else:
        #     boot_btn.key_up(delta)


        (statusC, xC, yC) = ts.read()

        if state_machine.current_state == STATE.INIT:
            loop_init()

        elif state_machine.current_state == STATE.CLASSIFY:
            loop_classify()
            if MenuEnterState == True:
                if statusC == ts.STATUS_RELEASE:
                    if(xC2 != None and yC2 != None):
                        if(50 < xC2 < 150 and 70 < yC2 < 170 ):
                            print("left click")
                            MenuEnterState = False
                            restart(state_machine)
                            # state_machine.current_state = STATE
                            pass
                        elif(170 < xC2 < 270 and 70 < yC2 < 170):
                            print("right click")
                            MenuEnterState = False
                            haveToSave = True
                            break
                            

                        xC2 = None
                        yC2 = None
                elif statusC == ts.STATUS_MOVE or statusC == ts.STATUS_PRESS:
                    (statusC2, xC2, yC2) = (statusC, xC, yC)
                

        elif state_machine.current_state == STATE.TRAIN_CLASS_1 or state_machine.current_state == STATE.TRAIN_CLASS_2 \
                or state_machine.current_state == STATE.TRAIN_CLASS_3 or state_machine.current_state == STATE.TRAIN_CLASS_4:
            loop_capture()
            if MenuEnterState == True:
                if statusC == ts.STATUS_RELEASE:
                    if(xC2 != None and yC2 != None):
                        if(50 < xC2 < 150 and 70 < yC2 < 170 ):
                            state_machine.current_state = STATE.CLASSIFY
                            print("left click")
                            MenuEnterState = False
                            pass
                        elif(170 < xC2 < 270 and 70 < yC2 < 170):
                            global currentID
                            if currentID:
                                state_machine.emit_event(EVENT.EVENT_NEXT_MODE)                     
                                # state_machine.current_state = currentID + 2
                            print("right click")
                            MenuEnterState = False
                            pass

                        xC2 = None
                        yC2 = None
                elif statusC == ts.STATUS_MOVE or statusC == ts.STATUS_PRESS:
                    (statusC2, xC2, yC2) = (statusC, xC, yC)
                    



    KPU.deinit(kpu)
    del(KPU)
    del(THRESHOLD)
    del(train_pic_cnt)
    del(central_msg)
    del(bottom_msg)
    del(boot_gpio)
    del(kpu)
    del(state_machine)
    del(btn_ticks_prev)
    del(boot_btn)
    del(TL_msg)
    del(TR_msg)
    del(currentID)
    del(MenuEnterState)
    del(state_handlers)
    del(event_handlers)
    del(transitions)
    del(Button)
    del(STATE)
    del(EVENT)
    del(StateMachine)

    gc.collect()
    print("break loop")
    global viewPage
    viewPage = None
    global prevPage, prevPageVar, whatToSave
    if isLoad:
        prevPage = createPage2
        if haveToSave:
            prevPageVar = True
            whatToSave = 1
        else:
            prevPageVar = False
            del(features)
    else:
        if haveToSave:
            prevPage = createPage2
            prevPageVar = True
            whatToSave = 1
        else:
            prevPage = createPage1
            prevPageVar = None
            del(features)




############## face recognition
############## face recognition
############## face recognition
############## face recognition
############## face recognition
############## face recognition
############## face recognition
############## face recognition
############## face recognition
############## face recognition
############## face recognition
def faceRecogPage(isLoad):
    # NOTE: make sure the gc heap memory is large enough to run this demo ,  The recommended size is 1M

    from maix import KPU
    from board import board_info
    
    global img_origin
    global clock,start_processing


    # sensor.skip_frames(time = 1000)     # Wait for settings take effect.
                                        # run automatically, call sensor.run(0) to stop
    clock = time.clock()                # Create a clock object to track the FPS.

    feature_img = image.Image(size=(64,64), copy_to_fb=True)
    feature_img.pix_to_ai()

    FACE_PIC_SIZE = 64
    dst_point =[(int(38.2946 * FACE_PIC_SIZE / 112), int(51.6963 * FACE_PIC_SIZE / 112)),
                (int(73.5318 * FACE_PIC_SIZE / 112), int(51.5014 * FACE_PIC_SIZE / 112)),
                (int(56.0252 * FACE_PIC_SIZE / 112), int(71.7366 * FACE_PIC_SIZE / 112)),
                (int(41.5493 * FACE_PIC_SIZE / 112), int(92.3655 * FACE_PIC_SIZE / 112)),
                (int(70.7299 * FACE_PIC_SIZE / 112), int(92.2041 * FACE_PIC_SIZE / 112)) ]

    anchor = (0.1075, 0.126875, 0.126875, 0.175, 0.1465625, 0.2246875, 0.1953125, 0.25375, 0.2440625, 0.351875, 0.341875, 0.4721875, 0.5078125, 0.6696875, 0.8984375, 1.099687, 2.129062, 2.425937)
    kpu = KPU()
    kpu.load_kmodel(0x364000,279592)
    kpu.init_yolo2(anchor, anchor_num=9, img_w=320, img_h=240, net_w=320 , net_h=240 ,layer_w=10 ,layer_h=8, threshold=0.5, nms_value=0.2, classes=1)

    ld5_kpu = KPU()
    print("ready load model")
    ld5_kpu.load_kmodel(0x33C000,159768)

    fea_kpu = KPU()
    print("ready load model")
    fea_kpu.load_kmodel(0x3A9000,1108368)

    start_processing = False
    BOUNCE_PROTECTION = 50

    def set_key_state(*_):
        global start_processing
        start_processing = True
        time.sleep_ms(BOUNCE_PROTECTION)

    # key_gpio.irq(set_key_state, GPIO.IRQ_RISING, GPIO.WAKEUP_NOT_SUPPORT)

    def btn1F():        
        global start_processing
        nonlocal MenuEnterState, EndTraining
        if MenuEnterState:
            MenuEnterState = False
        else:
            if EndTraining == False:
                start_processing = True



    MenuEnterState = False
    def btn1l():
        nonlocal MenuEnterState
        if MenuEnterState:
            MenuEnterState = False
        else:
            MenuEnterState = True    
    
    loopEscape = False
    def btn2F():
        nonlocal loopEscape

        loopEscape = True


    global record_ftrs
    record_ftrs = []
    THRESHOLD = 90.5

    RATIO = 0
    def extend_box(x, y, w, h, scale):
        x1_t = x - scale*w
        x2_t = x + w + scale*w
        y1_t = y - scale*h
        y2_t = y + h + scale*h
        x1 = int(x1_t) if x1_t>1 else 1
        x2 = int(x2_t) if x2_t<320 else 319
        y1 = int(y1_t) if y1_t>1 else 1
        y2 = int(y2_t) if y2_t<240 else 239
        cut_img_w = x2-x1+1
        cut_img_h = y2-y1+1
        return x1, y1, cut_img_w, cut_img_h



    colorList = [
        (148,60,255),
        (255,255,0),
        (0,255,255),
        (255,51,153),
        (0,255,0),
        (255,153,51),
        (51,153,255),
        (255,51,51),
        (0,205,102),
        (255,200,200)
    ]


    EndTraining = False
    recog_flag = False
    haveToSave = False
    (statusC, xC, yC) = ts.read()
    (statusC2, xC2, yC2) = (None,None,None)



    if isLoad != False:
        global img_origin
        print("loading")
        import json
        savetxt = "로 딩 완 료"
        if img_origin:
            img_origin.draw_rectangle(60,70,200,100,color = (0,0,0), fill = True)
            img_origin.draw_rectangle(60,70,200,100,color = (255,255,255), fill = False)
            draw_multiline_text(img_origin,80,90,"로 딩 중 ...",color = (255,255,255), scale=1.6)
            lcd.display(img_origin)
            time.sleep(0.5)
        try:
            with open('aiData'+str(isLoad)+'.json','r') as file:
                record_ftrs = json.load(file)
            # state_machine.current_state = STATE.CLASSIFY
            EndTraining = True
            print("loading success")
        except Exception as e:
            print(e)
            record_ftrs = []
            savetxt = "로 딩 실 패"
            print("loading failed")


        if img_origin:
            img_origin.draw_rectangle(60,70,200,100,color = (0,0,0), fill = True)
            img_origin.draw_rectangle(60,70,200,100,color = (255,255,255), fill = False)
            draw_multiline_text(img_origin,80,90,savetxt,color = (255,255,255), scale=1.6)
            lcd.display(img_origin)
            time.sleep(0.5)




    while 1:
        gc.collect()
        buttonEvent(btn1F, btn1l, btn2F, None)
        #print("mem free:",gc.mem_free())
        #print("heap free:",utils.heap_free())
        if loopEscape == True:
            break

        (statusC, xC, yC) = ts.read()

        if MenuEnterState == True:

            img_origin.draw_rectangle(0,50,320,140, color = (0,0,0), fill = True)
            
            if EndTraining == False:

                img_origin.draw_rectangle(110,70,100,100, color = (64,125,224), fill = True)
                img_origin.draw_rectangle(110,70,100,100, color = (255,255,255), fill = False)
                draw_multiline_text(img_origin,130,75,"모 델  학 습\n완 료 하 기", scale = 1.6)

                if statusC == ts.STATUS_RELEASE:
                    if(xC2 != None and yC2 != None):
                            if(110 < xC2 < 210 and 70 < yC2 < 170 ):
                                print("end click")
                                MenuEnterState = False
                                EndTraining = True
                                # restart(state_machine)
                                # state_machine.current_state = STATE
                    xC2 = None
                    yC2 = None
                elif statusC == ts.STATUS_MOVE or statusC == ts.STATUS_PRESS:
                    (statusC2, xC2, yC2) = (statusC, xC, yC)
            else:
                img_origin.draw_rectangle(0,50,320,140, color = (0,0,0), fill = True)
                
                img_origin.draw_rectangle(50,70,100,100, color = (64,125,224), fill = True)
                img_origin.draw_rectangle(50,70,100,100, color = (255,255,255), fill = False)
                draw_multiline_text(img_origin,70,75,"모 델  삭 제 \n및  재 학 습", scale = 1.6)

                img_origin.draw_rectangle(170,70,100,100, color = (159,123,255), fill = True)
                img_origin.draw_rectangle(170,70,100,100, color = (255,255,255), fill = False)
                draw_multiline_text(img_origin,190,75,"현 재  모 델 \n저 장 하 기", scale = 1.6)

                if statusC == ts.STATUS_RELEASE:
                    if(xC2 != None and yC2 != None):
                        if(50 < xC2 < 150 and 70 < yC2 < 170 ):
                            print("left click")
                            if(record_ftrs):
                                del(record_ftrs)
                                record_ftrs= []
                            EndTraining = False
                            MenuEnterState = False
                            pass

                        elif(170 < xC2 < 270 and 70 < yC2 < 170):
                            print("right click")
                            MenuEnterState = False
                            haveToSave = True
                            break

                        xC2 = None
                        yC2 = None
                elif statusC == ts.STATUS_MOVE or statusC == ts.STATUS_PRESS:
                    (statusC2, xC2, yC2) = (statusC, xC, yC)
            

            lcd.display(img_origin)
            
            continue


        clock.tick()                    # Update the FPS clock.
        img_origin = sensor.snapshot()
        kpu.run_with_output(img_origin)
        dect = kpu.regionlayer_yolo2()
        fps = clock.fps()
        max_index = None
        max_face_match_score = 0
        #print("gganada 1")
        
        if len(dect) > 0:
            #print("gganada 2")
            # print("heap free0:",utils.heap_free())

            for i,l in enumerate(dect) :
                #print("gganada 2.0")

                gc.collect()
                x1, y1, cut_img_w, cut_img_h= extend_box(l[0], l[1], l[2], l[3], scale=RATIO)
                face_cut = img_origin.cut(x1, y1, cut_img_w, cut_img_h)
                #a = img.draw_rectangle(l[0],l[1],l[2],l[3], color=(255, 255, 255))
                # img.draw_image(face_cut, 0,0)
                face_cut_128 = face_cut.resize(128, 128)
                face_cut_128.pix_to_ai()
                out = ld5_kpu.run_with_output(face_cut_128, getlist=True)
                face_key_point = []
                #print("gganada 2.1")

                for j in range(5):
                    x = int(KPU.sigmoid(out[2 * j])*cut_img_w + x1)
                    y = int(KPU.sigmoid(out[2 * j + 1])*cut_img_h + y1)
                    # a = img.draw_cross(x, y, size=5, color=(0, 0, 255))
                    face_key_point.append((x,y))
                del(out)
                del(x)
                del(y)
                T = image.get_affine_transform(face_key_point, dst_point)
                image.warp_affine_ai(img_origin, feature_img, T)
                #print("gganada 2.2")
                del(T)
                del face_key_point
                # feature_img.ai_to_pix()
                # img.draw_image(feature_img, 0,0)
                feature = fea_kpu.run_with_output(feature_img, get_feature = True)
                scores = []
                #print("gganada 2.3")
                # high = 0
                for j in range(len(record_ftrs)):
                    score = kpu.feature_compare(record_ftrs[j], feature)
                    scores.append(score)
                if len(scores):
                    max_score = max(scores)
                    index = scores.index(max_score)
                    if max_score > THRESHOLD:
                        if max_score > max_face_match_score:
                            max_index = index
                            max_face_match_score = max_score

                        # draw_multiline_text(img_origin,20, 50, "얼 굴\n%d"%(index), color = colorList[index], scale = 1.3)
                        # draw_multiline_text(img_origin,285, 50, "확 률\n%2.1f"%(max_score),color = colorList[index], scale = 1.3)
                        # img_origin.draw_string(0, 195, "persion:%d,score:%2.1f" %(index, max_score), color=(0, 255, 0), scale=2)
                        img_origin.draw_rectangle(l[0],l[1],l[2],l[3], color=colorList[index])
                        img_origin.draw_rectangle(l[0],l[1] -20,40,20, color=colorList[index], fill = True)
                        img_origin.draw_string(l[0] + 15,l[1] -20, "ID:{}".format(index), color = (0,0,0))
                        recog_flag = True
                    else:
                        pass
                        # img_origin.draw_string(0, 195, "unregistered,score:%2.1f" %(max_score), color=(255, 0, 0), scale=2)
                # print("heap free1:",utils.heap_free())
                ##print("gganada 2.4")
                del scores
                if recog_flag:
                    recog_flag = False
                else:
                    img_origin.draw_rectangle(l[0],l[1],l[2],l[3], color=(255, 255, 255))
                # print("heap free 2:",utils.heap_free())
                ##print("gganada 2.5")

                if(EndTraining == False): # 트레이닝 할 때는 1개만 뜨게 함
                    break
                
            ##print("gganada 3")
            # print("heap free 3:",utils.heap_free())
                
            if start_processing:
                if len(record_ftrs) >= 10:
                    img_origin.draw_rectangle(60,70,200,100,color = (0,0,0), fill = True)
                    img_origin.draw_rectangle(60,70,200,100,color = (255,255,255), fill = False)
                    draw_multiline_text(img_origin,80,90,"한 도 초 과",color = (255,255,255), scale=1.6)
                    lcd.display(img_origin)
                    time.sleep(1)
                else:
                    record_ftrs.append(feature)
                    print("record_ftrs:%d" % len(record_ftrs))
                start_processing = False
            # ##print("gganada 4")
            
            del (face_cut_128)
            del (face_cut)
            del (feature)
            gc.collect()            

            if max_index != None:
                draw_multiline_text(img_origin,20, 50, "얼 굴\n%d"%(max_index), color = colorList[max_index], scale = 1.3)
                draw_multiline_text(img_origin,285, 50, "확 률\n%2.1f"%(max_face_match_score),color = colorList[max_index], scale = 1.3)
                max_index = None

        # img_origin.draw_string(0, 0, "%2.1ffps" %(fps), color=(0, 60, 255), scale=2.0)
        
        # img_origin.draw_string(0, 215, "press boot key to regist face", color=(255, 100, 0), scale=2.0)
        img_origin.draw_rectangle(0,0, 320, 25, color = (100,100,100), fill = True)
        img_origin.draw_string(10, 3, "뒤 로", color = (0,0,0))
        img_origin.draw_string(100, 3, "얼 굴  인 식  모 델 ", color = (0,0,0), scale = 1.2)
        img_origin.draw_string(300, 3, "학 습", color = (0,0,0))
        lcd.display(img_origin)

    gc.collect()
    
    kpu.deinit()
    ld5_kpu.deinit()
    fea_kpu.deinit()
    del(kpu)
    del(clock)
    del(start_processing)
    del(feature_img)
    del(FACE_PIC_SIZE)
    del(dst_point)
    del(anchor)
    del(BOUNCE_PROTECTION)
    del(THRESHOLD)
    del(RATIO)
    del(recog_flag)

    gc.collect()
    print("break loop")
    global viewPage
    viewPage = None
    global prevPage, prevPageVar, whatToSave
    if isLoad:
        prevPage = createPage2
        if haveToSave:
            prevPageVar = True
            whatToSave = 2
        else:
            prevPageVar = False
            if record_ftrs:
                del(record_ftrs)
    else:
        if haveToSave:
            prevPage = createPage2
            prevPageVar = True
            whatToSave = 2
        else:
            prevPage = createPage1
            prevPageVar = None
            if record_ftrs:
                del(record_ftrs)


#####
#####
#####





def createPage2(isSaving): ## 불러오기
    print("page2")
    global prevPage, prevPageVar
    prevPage = createMainPage
    prevPageVar = None

    global img_origin, datainfo
    img_origin.draw_rectangle(0,0,320,240,color = (0,0,0), fill = True)
    mainDiv = Div(img_origin)
    mainDiv.set(1)
    import json
    import os

    datainfo = [0,0,0,0,0,0]

    try:
        with open('aiDatainfo.json', 'r') as file:
            datainfo = json.load(file)
    except Exception as e:
        print("데이터를 읽는 중 오류 발생:", e)
        # print(f"데이터를 읽는 중 오류 발생: {e}")
        datainfo = [0,0,0,0,0,0]



    def saveFunction(loc, num):
        global datainfo
        savetxt = "저 장 완 료"
        if img_origin:
            img_origin.draw_rectangle(60,70,200,100,color = (0,0,0), fill = True)
            img_origin.draw_rectangle(60,70,200,100,color = (255,255,255), fill = False)
            draw_multiline_text(img_origin,80,90,"저 장 중 ...",color = (255,255,255), scale=1.6)
            lcd.display(img_origin)
        try:
            import json
            with open('aiData'+str(loc)+'.json','w') as file:
                if num == 1:
                    global features
                    file.write(json.dumps(features))
                elif num == 2:
                    global record_ftrs
                    file.write(json.dumps(record_ftrs))
                elif num == 3:
                    global tagIdList
                    file.write(json.dumps(tagIdList))
                elif num == 4:
                    global tagIdList
                    file.write(json.dumps(tagIdList))
                elif num == 5:
                    global tagIdList
                    file.write(json.dumps(tagIdList))
                elif num == 6:
                    global tagIdList
                    file.write(json.dumps(tagIdList))

                datainfo[loc-1] = num   
            with open('aiDatainfo.json','w') as file:
                file.write(json.dumps(datainfo))
            gc.collect()
            
        except Exception as e:
            print("memory error", e)
            gc.collect()
            savetxt = "저 장 실 패 - 메 모 리  초 과"
        if img_origin:
            img_origin.draw_rectangle(60,70,200,100,color = (0,0,0), fill = True)
            img_origin.draw_rectangle(60,70,200,100,color = (255,255,255), fill = False)
            draw_multiline_text(img_origin,80,90,savetxt,color = (255,255,255), scale=1.6)
            lcd.display(img_origin)
            time.sleep(3)
        if num == 1:
            switch_view(classificationPage,loc)
        elif num == 2:
            switch_view(faceRecogPage,loc)
        elif num == 3:
            switch_view(aprilTagPage,loc)
        elif num == 4:
            switch_view(objPage,loc)
        elif num == 5:
            switch_view(qrPage,loc)
        elif num == 6:
            switch_view(colorPage,loc)

    def load_switch(num):
            global datainfo
            if datainfo[num-1] == 1:
                switch_view(classificationPage, num)
            elif datainfo[num-1] == 2:
                switch_view(faceRecogPage,num)
            elif datainfo[num-1] == 3:
                switch_view(aprilTagPage, num)
            elif datainfo[num-1] == 4:
                switch_view(objPage, num)
            elif datainfo[num-1] == 5:
                switch_view(qrPage, num)
            elif datainfo[num-1] == 6:
                switch_view(colorPage, num)
            else:
                print("모듈이 없습니다")



    def b1Event(x, y):
        load_switch(1)

    def b2Event(x, y):
        load_switch(2)
        
    def b3Event(x, y):
        load_switch(3)

    def b4Event(x, y):
        load_switch(4)
        
    def b5Event(x, y):
        load_switch(5)

    def b6Event(x, y):
        load_switch(6)


    def b1Event2(x, y):
        global whatToSave
        saveFunction(1, whatToSave)
        whatToSave = None

    def b2Event2(x, y):
        global whatToSave
        saveFunction(2, whatToSave)
        whatToSave = None

    def b3Event2(x, y):
        global whatToSave
        saveFunction(3, whatToSave)
        whatToSave = None

    def b4Event2(x, y):
        global whatToSave
        saveFunction(4, whatToSave)
        whatToSave = None
    
    def b5Event2(x, y):
        global whatToSave
        saveFunction(5, whatToSave)
        whatToSave = None

    def b6Event2(x, y):
        global whatToSave
        saveFunction(6, whatToSave)
        whatToSave = None

    mainButton1 = ButtonDiv()
    btn1txt = TextDiv()
    mainButton1.put(btn1txt)

    mainButton2 = ButtonDiv()
    btn2txt = TextDiv()
    mainButton2.put(btn2txt)

    mainButton3 = ButtonDiv()
    btn3txt = TextDiv()
    mainButton3.put(btn3txt)

    mainButton4 = ButtonDiv()
    btn4txt = TextDiv()
    mainButton4.put(btn4txt)

    mainButton5 = ButtonDiv()
    btn5txt = TextDiv()
    mainButton5.put(btn5txt)
    

    mainButton6 = ButtonDiv()
    btn6txt = TextDiv()
    mainButton6.put(btn6txt)


    def getAiInfo(modelNum):
        if modelNum == 0:
            return "모 델  없 음"
        if modelNum == 1:
            return "얼 굴  인 식\n모 델"
        if modelNum == 2:
            return "분 류 모 델"
        if modelNum == 3:
            return "태 그  인 식"
        if modelNum == 4:
            return "객 체  인 식"
        if modelNum == 5:
            return "Q R  인 식"
        if modelNum == 6:
            return "색 상  인 식"
        return "에 러"
        

    mainButton1.set(2, 5, 15, 100, 100, (159, 123, 255), True)      # 1
    btn1txt.set(2, 5, 15, 100, 100, "모 델 1\n{}".format(getAiInfo(datainfo[0])))
    mainButton2.set(2, 110, 15, 100, 100, (64, 125, 224), True)     # 3
    btn2txt.set(2, 110, 15, 100, 100, "모 델 2\n{}".format(getAiInfo(datainfo[2])))
    mainButton3.set(2, 5, 120, 100, 100, (64, 125, 224), True)      # 2
    btn3txt.set(2, 5, 120, 100, 100, "모 델 4\n{}".format(getAiInfo(datainfo[1])))
    mainButton4.set(2, 110, 120, 100, 100, (159, 123, 255), True)   # 5
    btn4txt.set(2, 110, 120, 100, 100, "모 델 5\n{}".format(getAiInfo(datainfo[4])))
    mainButton5.set(2, 215, 15, 100, 100, (159, 123, 255), True)    # 4
    btn5txt.set(2, 215, 15, 100, 100, "모 델 3\n{}".format(getAiInfo(datainfo[3])))
    mainButton6.set(2, 215, 120, 100, 100, (64, 125, 224), True)    # 6
    btn6txt.set(2, 215, 120, 100, 100, "모 델 6\n{}".format(getAiInfo(datainfo[5])))


    if isSaving:
        mainButton1.clickEset(b1Event2)
        mainButton2.clickEset(b3Event2)
        mainButton3.clickEset(b2Event2)
        mainButton4.clickEset(b5Event2)
        mainButton5.clickEset(b4Event2)
        mainButton6.clickEset(b6Event2)
    else:
        mainButton1.clickEset(b1Event)
        mainButton2.clickEset(b3Event)
        mainButton3.clickEset(b2Event)
        mainButton4.clickEset(b5Event)
        mainButton5.clickEset(b4Event)
        mainButton6.clickEset(b6Event)
        


    mainDiv.put(mainButton1)
    mainDiv.put(mainButton2)
    mainDiv.put(mainButton3)
    mainDiv.put(mainButton4)
    mainDiv.put(mainButton5)
    mainDiv.put(mainButton6)


    if isSaving:
        huenitVerText2 = CustomDiv()
        huenitVerText2.drawFn = (lambda img: img.draw_string(100,5,"Select save point", color = (255,255,255), scale = 1))
        mainDiv.put(huenitVerText2)
    huenitVerText = CustomDiv()
    huenitVerText.drawFn = (lambda img: img.draw_string(100,223,"Huenit X Robotis v0.1.0", color = (255,255,255), scale = 1))
    mainDiv.put(huenitVerText)

    mainDiv.viewinit()
    gc.collect()
    return mainDiv


def createPage3(): ## 인식 모델
    print("page3")
    global prevPage
    prevPage = createMainPage

    global img_origin
    img_origin.draw_rectangle(0,0,320,240,color = (0,0,0), fill = True)
    mainDiv = Div(img_origin)
    mainDiv.set(1)


    def b1Event(x, y):
        switch_view(lineTracePage, False)
        # switch_view(createPage1)
        pass

    def b2Event(x, y):
        switch_view(aprilTagPage, False)
        pass

    def b3Event(x, y):
        switch_view(qrPage, False)
        pass
        # switch_view(createPage3)

    def b4Event(x, y): # 색 상 인 식
        switch_view(colorPage,False)
        pass
        # switch_view(createPage4)

    def b5Event(x, y):  # 객체인식
        switch_view(objPage, False)
        pass
        # switch_view(createPage5)
            
    def b6Event(x, y):
        pass
        # switch_view(createPage6)

    mainButton1 = ButtonDiv()
    btn1txt = TextDiv()
    mainButton1.put(btn1txt)

    mainButton2 = ButtonDiv()
    btn2txt = TextDiv()
    mainButton2.put(btn2txt)

    mainButton3 = ButtonDiv()
    btn3txt = TextDiv()
    mainButton3.put(btn3txt)

    mainButton4 = ButtonDiv()
    btn4txt = TextDiv()
    # btn4txt2 = CustomDiv()
    # btn4txt.drawFn = (lambda img: img.draw_image(hueLogo,110,120))
    # btn4txt2.drawFn = (lambda img: img.draw_rectangle(110,120,100,100,(255,255,255), fill = False))
    mainButton4.put(btn4txt)
    # mainButton4.put(btn4txt2)

    mainButton5 = ButtonDiv()
    btn5txt = TextDiv()
    mainButton5.put(btn5txt)
    

    mainButton6 = ButtonDiv()
    btn6txt = CustomDiv()
    btn6txt2 = CustomDiv()
    btn6txt.drawFn = (lambda img: img.draw_image(hueLogo,215,120))
    btn6txt2.drawFn = (lambda img: img.draw_rectangle(215,120,100,100,(255,255,255), fill = False))
    mainButton6.put(btn6txt)
    mainButton6.put(btn6txt2)

    mainButton1.set(2, 5, 15, 100, 100, (159, 123, 255), True)
    btn1txt.set(2, 5, 15, 100, 100, "라 인  인 식")
    mainButton2.set(2, 110, 15, 100, 100, (64, 125, 224), True)
    btn2txt.set(2, 110, 15, 100, 100, "태 그  인 식")
    mainButton3.set(2, 5, 120, 100, 100, (64, 125, 224), True)
    btn3txt.set(2, 5, 120, 100, 100, "QR 인 식")
    mainButton4.set(2, 110, 120, 100, 100, (159, 123, 255), True)
    btn4txt.set(2, 110, 120, 100, 100, "객 체  인 식")
    mainButton5.set(2, 215, 15, 100, 100, (159, 123, 255), True)
    btn5txt.set(2, 215, 15, 100, 100, "색 상  인 식")
    mainButton6.set(2, 215, 120, 100, 100, (64, 125, 224), True)

    mainButton1.clickEset(b1Event)
    mainButton2.clickEset(b2Event)
    mainButton3.clickEset(b3Event)
    mainButton5.clickEset(b4Event)
    mainButton4.clickEset(b5Event)
    mainButton6.clickEset(b6Event)

    mainDiv.put(mainButton1)
    mainDiv.put(mainButton2)
    mainDiv.put(mainButton3)
    mainDiv.put(mainButton4)
    mainDiv.put(mainButton5)
    mainDiv.put(mainButton6)


    huenitVerText = CustomDiv()
    huenitVerText.drawFn = (lambda img: img.draw_string(100,223,"Huenit X Robotis v0.1.0", color = (255,255,255), scale = 1))
    mainDiv.put(huenitVerText)

    mainDiv.viewinit()
    gc.collect()
    return mainDiv


def aprilTagPage(isLoad):

    sensor.set_auto_gain(False)  # must turn this off to prevent image washout...
    sensor.set_auto_whitebal(False)  # must turn this off to prevent image washout...
    # sensor.skip_frames(time = 2000)
    clock = time.clock()


    tag_families = 0
    tag_families |= image.TAG16H5 # comment out to disable this family
    tag_families |= image.TAG25H7 # comment out to disable this family
    tag_families |= image.TAG25H9 # comment out to disable this family
    tag_families |= image.TAG36H10 # comment out to disable this family
    tag_families |= image.TAG36H11 # comment out to disable this family (default family)
    tag_families |= image.ARTOOLKIT # comment out to disable this family

    colorList = [
        (148,60,255),
        (255,255,0),
        (0,255,255),
        (255,51,153),
        (0,255,0),
        (255,153,51),
        (51,153,255),
        (255,51,51),
        (0,205,102),
        (255,200,200)
    ]


    EndTraining = False
    global tagIdList
    if isLoad != False:
        tagIdList = dataLoadingFunction(isLoad)
        EndTraining = True

    else:
        tagIdList = []
        EndTraining = False




    def family_name(tag):
        if(tag.family() == image.TAG16H5):
            return "TAG16H5"
        if(tag.family() == image.TAG25H7):
            return "TAG25H7"
        if(tag.family() == image.TAG25H9):
            return "TAG25H9"
        if(tag.family() == image.TAG36H10):
            return "TAG36H10"
        if(tag.family() == image.TAG36H11):
            return "TAG36H11"
        if(tag.family() == image.ARTOOLKIT):
            return "ARTOOLKIT"

    def btn2():
        nonlocal loopEscape

        loopEscape = True

    def btn1s():
        global tagSave
        tagSave = True
        pass
        # global boot_btn, MenuEnterState
        # MenuEnterState = False
        # boot_btn.st.emit_event(EVENT.BOOT_KEY)
    
    def btn1l():
        nonlocal MenuEnterState
        MenuEnterState = True
        pass
        # global boot_btn, MenuEnterState
        # MenuEnterState = True
        # boot_btn.st.emit_event(EVENT.BOOT_KEY_LONG_PRESS)
    global tagSave
    tagSave = False
    loopEscape = False
    MenuEnterState = False
    haveToSave = False
    (statusC, xC, yC) = ts.read()
    (statusC2, xC2, yC2) = (None,None,None)
    global img_origin
    while(True):
        gc.collect()
        buttonEvent(btn1s,btn1l,btn2,None)
        if loopEscape:
            break

        
        (statusC, xC, yC) = ts.read()

        if MenuEnterState == True:

            img_origin.draw_rectangle(0,50,320,140, color = (0,0,0), fill = True)
            
            if EndTraining == False:

                img_origin.draw_rectangle(110,70,100,100, color = (64,125,224), fill = True)
                img_origin.draw_rectangle(110,70,100,100, color = (255,255,255), fill = False)
                draw_multiline_text(img_origin,130,75,"모 델  학 습\n완 료 하 기", scale = 1.6)

                if statusC == ts.STATUS_RELEASE:
                    if(xC2 != None and yC2 != None):
                            if(110 < xC2 < 210 and 70 < yC2 < 170 ):
                                print("end click")
                                MenuEnterState = False
                                EndTraining = True
                                # restart(state_machine)
                                # state_machine.current_state = STATE
                    xC2 = None
                    yC2 = None
                elif statusC == ts.STATUS_MOVE or statusC == ts.STATUS_PRESS:
                    (statusC2, xC2, yC2) = (statusC, xC, yC)
            else:
                img_origin.draw_rectangle(0,50,320,140, color = (0,0,0), fill = True)
                
                img_origin.draw_rectangle(50,70,100,100, color = (64,125,224), fill = True)
                img_origin.draw_rectangle(50,70,100,100, color = (255,255,255), fill = False)
                draw_multiline_text(img_origin,70,75,"모 델  삭 제 \n및  재 학 습", scale = 1.6)

                img_origin.draw_rectangle(170,70,100,100, color = (159,123,255), fill = True)
                img_origin.draw_rectangle(170,70,100,100, color = (255,255,255), fill = False)
                draw_multiline_text(img_origin,190,75,"현 재  모 델 \n저 장 하 기", scale = 1.6)

                if statusC == ts.STATUS_RELEASE:
                    if(xC2 != None and yC2 != None):
                        if(50 < xC2 < 150 and 70 < yC2 < 170 ):
                            print("left click")
                            if(tagIdList):
                                del(tagIdList)
                                tagIdList= []
                            EndTraining = False
                            MenuEnterState = False
                            pass

                        elif(170 < xC2 < 270 and 70 < yC2 < 170):
                            print("right click")
                            MenuEnterState = False
                            haveToSave = True
                            break

                        xC2 = None
                        yC2 = None
                elif statusC == ts.STATUS_MOVE or statusC == ts.STATUS_PRESS:
                    (statusC2, xC2, yC2) = (statusC, xC, yC)
            

            lcd.display(img_origin)
            
            continue

        clock.tick()
        img_origin = sensor.snapshot()
        img_origin.draw_image(img_origin,0,0,x_scale= 0.5, y_scale = 0.5)
        # for s in  startLoc:
        apt = img_origin.copy(roi = (0,0,160,120)).find_apriltags(families = tag_families)
        img_origin = sensor.snapshot()
        # apt = img.copy(roi = (s[0],s[1],160,120)).find_apriltags(families = tag_families)
        # img.draw_image(img,0,0,x_scale = 2.0, y_scale = 2.0)
        for tag in apt: # defaults to TAG36H11 without "families".
            if tagSave == True and EndTraining == False:
                if len(tagIdList) < len(colorList):
                    tagIdList.append(tag.id())
                tagSave = False
            
            index = find_index(tag.id(),tagIdList)
            if index == None:
                img_origin.draw_rectangle(2*tag.rect()[0],2*tag.rect()[1],2*tag.rect()[2],2*tag.rect()[3], color = (255, 255, 255))
            else:
                img_origin.draw_rectangle(2*tag.rect()[0],2*tag.rect()[1],2*tag.rect()[2],2*tag.rect()[3], color = colorList[index], thickness = 2)
                img_origin.draw_rectangle(2*tag.rect()[0],2*tag.rect()[1] - 20, 40, 20,color = colorList[index], fill = True)
                img_origin.draw_string(2*tag.rect()[0] + 20,2*tag.rect()[1] - 20, "ID: {}".format(index+1), color = (0,0,0))
                                
            img_origin.draw_cross(2*tag.cx(), 2*tag.cy(), color = (0, 255, 0))
            print_args = (family_name(tag), tag.id(), (180 * tag.rotation()) / math.pi)
            print("Tag Family %s, Tag ID %d, rotation %f (degrees)" % print_args)
            if EndTraining == False:
                # draw_multiline_text(img_origin,285, 50, TR_msg, color = colorList[len(tagIdList)], scale = 1.3)
                break
        print(clock.fps())

        if EndTraining == False:
            draw_multiline_text(img_origin,20, 50, "태 그\n{}".format(len(tagIdList)), color = colorList[len(tagIdList)], scale = 1.3)

        # img.draw_rectangle(80,60,160,120, color = (255,255,255), ticknesse = 2, fill = False)
        img_origin.draw_rectangle(0,0, 320, 25, color = (100,100,100), fill = True)
        img_origin.draw_string(10, 3, "뒤 로", color = (0,0,0))
        img_origin.draw_string(130, 3, "태 그  인 식 ", color = (0,0,0), scale = 1.2)
        img_origin.draw_string(300, 3, "학 습", color = (0,0,0))
        lcd.display(img_origin)


    sensor.set_auto_gain(True)  # must turn this off to prevent image washout...
    sensor.set_auto_whitebal(True)  # must turn this off to prevent image washout...
    gc.collect()


    gc.collect()
    print("break loop")
    global viewPage
    viewPage = None
    global prevPage, prevPageVar, whatToSave
    if isLoad:
        prevPage = createPage2
        if haveToSave:
            prevPageVar = True
            whatToSave = 3
        else:
            prevPageVar = False
            if tagIdList:
                del(tagIdList)
    else:
        if haveToSave:
            prevPage = createPage2
            prevPageVar = True
            whatToSave = 3
        else:
            prevPage = createPage3
            prevPageVar = None
            if tagIdList:
                del(tagIdList)


def lineTracePage(isLoad):
    import math

    sensor.set_auto_gain(False, gain_db = -1) 
    sensor.set_auto_whitebal(False, rgb_gain_db = (0,0,0)) 



    colorList = [
        (148,60,255),
        (255,255,0),
        (0,255,255),
        (255,51,153),
        (0,255,0),
        (255,153,51),
        (51,153,255),
        (255,51,51),
        (0,205,102),
        (255,200,200)
    ]


    def btn2():
        nonlocal loopEscape

        loopEscape = True

    def btn1s():
        global tagSave
        tagSave = True
        pass
        # global boot_btn, MenuEnterState
        # MenuEnterState = False
        # boot_btn.st.emit_event(EVENT.BOOT_KEY)

    
    
    def btn1l():
        nonlocal MenuEnterState
        MenuEnterState = True
        pass
        # global boot_btn, MenuEnterState
        # MenuEnterState = True
        # boot_btn.st.emit_event(EVENT.BOOT_KEY_LONG_PRESS)

    loopEscape = False
    EndTraining = False
    global tagIdList
    if isLoad != False:
        tagIdList = dataLoadingFunction(isLoad)
        EndTraining = True
    else:
        tagIdList = []
        EndTraining = False

    global tagSave
    tagSave = False
    loopEscape = False
    MenuEnterState = False
    haveToSave = False
    (statusC, xC, yC) = ts.read()
    (statusC2, xC2, yC2) = (None,None,None)
    global img_origin
    
    while True:
        gc.collect()
        buttonEvent(btn1s,btn1l,btn2,None)
        if loopEscape:
            break

        (statusC, xC, yC) = ts.read()

        if MenuEnterState == True:

            img_origin.draw_rectangle(0,50,320,140, color = (0,0,0), fill = True)
            
            if EndTraining == False:

                img_origin.draw_rectangle(110,70,100,100, color = (64,125,224), fill = True)
                img_origin.draw_rectangle(110,70,100,100, color = (255,255,255), fill = False)
                draw_multiline_text(img_origin,130,75,"모 델  학 습\n완 료 하 기", scale = 1.6)

                if statusC == ts.STATUS_RELEASE:
                    if(xC2 != None and yC2 != None):
                            if(110 < xC2 < 210 and 70 < yC2 < 170 ):
                                print("end click")
                                MenuEnterState = False
                                EndTraining = True
                                # restart(state_machine)
                                # state_machine.current_state = STATE
                    xC2 = None
                    yC2 = None
                elif statusC == ts.STATUS_MOVE or statusC == ts.STATUS_PRESS:
                    (statusC2, xC2, yC2) = (statusC, xC, yC)
            else:
                img_origin.draw_rectangle(0,50,320,140, color = (0,0,0), fill = True)
                
                img_origin.draw_rectangle(50,70,100,100, color = (64,125,224), fill = True)
                img_origin.draw_rectangle(50,70,100,100, color = (255,255,255), fill = False)
                draw_multiline_text(img_origin,70,75,"모 델  삭 제 \n및  재 학 습", scale = 1.6)

                img_origin.draw_rectangle(170,70,100,100, color = (159,123,255), fill = True)
                img_origin.draw_rectangle(170,70,100,100, color = (255,255,255), fill = False)
                draw_multiline_text(img_origin,190,75,"현 재  모 델 \n저 장 하 기", scale = 1.6)

                if statusC == ts.STATUS_RELEASE:
                    if(xC2 != None and yC2 != None):
                        if(50 < xC2 < 150 and 70 < yC2 < 170 ):
                            print("left click")
                            if(tagIdList):
                                del(tagIdList)
                                tagIdList= []
                            EndTraining = False
                            MenuEnterState = False
                            pass

                        elif(170 < xC2 < 270 and 70 < yC2 < 170):
                            print("right click")
                            MenuEnterState = False
                            haveToSave = True
                            break

                        xC2 = None
                        yC2 = None
                elif statusC == ts.STATUS_MOVE or statusC == ts.STATUS_PRESS:
                    (statusC2, xC2, yC2) = (statusC, xC, yC)
            

            lcd.display(img_origin)
            
            continue

        img_origin = sensor.snapshot()

        lines = img_origin.find_lines(threshold = 1000)
        # lines = img.find_line_segments(merge_distance = 20)
        if len(lines) <1:
            print("no line detected")
            img_origin.draw_string(100,100,"no line detected", scale = 2)
        else:
            max_element = max(lines, key=lambda item: item.magnitude())
            if tagSave == True and EndTraining == False:
                if len(tagIdList) < len(colorList):
                    tagIdList.append(max_element.theta())
                tagSave = False
            
            isLineExist = False
            for index, l in enumerate(tagIdList):
                if math.fabs(l - max_element.theta()) <= 10:
                    img_origin.draw_line(max_element.x1(), max_element.y1(), max_element.x2(), max_element.y2(), colorList[index], 2)
                    img_origin.draw_rectangle(math.ceil((max_element.x1() +max_element.x2())/2), math.ceil((max_element.y1() +max_element.y2())/2), 40, 20, color = (255,255,255), fill = True)
                    img_origin.draw_string(math.ceil((max_element.x1() +max_element.x2())/2)+10, math.ceil((max_element.y1() +max_element.y2())/2), "ID: {}".format(index), color = (0,0,0))
                    isLineExist = True
            if isLineExist == False:
                img_origin.draw_line(max_element.x1(), max_element.y1(), max_element.x2(), max_element.y2(), (255,255,255), 2)


        if EndTraining == False:
            draw_multiline_text(img_origin,20, 50, "태 그\n{}".format(len(tagIdList)), color = colorList[len(tagIdList)], scale = 1.3)

        img_origin.draw_rectangle(0,0, 320, 25, color = (100,100,100), fill = True)
        img_origin.draw_string(10, 3, "뒤 로", color = (0,0,0))
        img_origin.draw_string(130, 3, "라 인  인 식", color = (0,0,0), scale = 1.2)
        img_origin.draw_string(300, 3, "학 습", color = (0,0,0))
        # for a in lines:

        #     img.draw_line(a.x1(), a.y1(), a.x2(), a.y2(), (255,0,0), 2)
        #     theta = a.theta()
        #     rho = a.rho()
        #     angle_in_radians = math.radians(theta)
        #     x = int(math.cos(angle_in_radians) * rho)
        #     y = int(math.sin(angle_in_radians) * rho)
        #     img.draw_line(0, 0, x, y, (0,255,255), 2)
        #     img.draw_string(x, y, "theta: " + str(theta) + "," + "rho: " + str(rho), (0,255,0))

        lcd.display(img_origin)    

    sensor.set_auto_gain(True)  # must turn this off to prevent image washout...
    sensor.set_auto_whitebal(True)  # must turn this off to prevent image washout...
    gc.collect()

    print("break loop")
    global viewPage
    viewPage = None
    global prevPage, prevPageVar, whatToSave
    if isLoad:
        prevPage = createPage2
        if haveToSave:
            prevPageVar = True
            whatToSave = 5
        else:
            prevPageVar = False
            if tagIdList:
                del(tagIdList)
    else:
        if haveToSave:
            prevPage = createPage2
            prevPageVar = True
            whatToSave = 5
        else:
            prevPage = createPage3
            prevPageVar = None
            if tagIdList:
                del(tagIdList)




def objPage(isLoad):
    # import sensor, image, time, lcd
    from maix import KPU
    # import gc
    
    # lcd.init()
    # sensor.reset()                      # Reset and initialize the sensor. It will
                                        # run automatically, call sensor.run(0) to stop
    # sensor.set_pixformat(sensor.RGB565) # Set pixel format to RGB565 (or GRAYSCALE)
    # sensor.set_framesize(sensor.QVGA)   # Set frame size to QVGA (320x240)
    # sensor.set_vflip(1)
    # sensor.skip_frames(time = 1000)     # Wait for settings take effect.
    clock = time.clock()                # Create a clock object to track the FPS.
    
    od_img = image.Image(size=(320,256), copy_to_fb = True)
    
    obj_name = ("aeroplane","bicycle", "bird","boat","bottle","bus","car","cat","chair","cow","diningtable", "dog","horse", "motorbike","person","pottedplant", "sheep","sofa", "train", "tvmonitor")
    anchor = (1.3221, 1.73145, 3.19275, 4.00944, 5.05587, 8.09892, 9.47112, 4.84053, 11.2364, 10.0071)
    kpu = KPU()
    print("ready load model")
    kpu.load_kmodel(0x62f000, 1536936)
    #kpu.load_kmodel("/sd/KPU/voc20_object_detect/voc20_detect.kmodel")
    kpu.init_yolo2(anchor, anchor_num=5, img_w=320, img_h=240, net_w=320 , net_h=256 ,layer_w=10 ,layer_h=8, threshold=0.5, nms_value=0.2, classes=20)
    
    i = 0
    def btn2():
        nonlocal loopEscape

        loopEscape = True

    def btn1s():
        global tagSave
        tagSave = True
        pass
        # global boot_btn, MenuEnterState
        # MenuEnterState = False
        # boot_btn.st.emit_event(EVENT.BOOT_KEY)

    
    
    def btn1l():
        nonlocal MenuEnterState
        MenuEnterState = True
        pass
        # global boot_btn, MenuEnterState
        # MenuEnterState = True
        # boot_btn.st.emit_event(EVENT.BOOT_KEY_LONG_PRESS)


    colorList = [
        (148,60,255),
        (255,255,0),
        (0,255,255),
        (255,51,153),
        (0,255,0),
        (255,153,51),
        (51,153,255),
        (255,51,51),
        (0,205,102),
        (255,200,200)
    ]
    global tagSave
    tagSave = False
    loopEscape = False
    MenuEnterState = False
    haveToSave = False

    EndTraining = False
    global tagIdList
    if isLoad != False:
        tagIdList = dataLoadingFunction(isLoad)
        EndTraining = True

    else:
        tagIdList = []
        EndTraining = False


    global img_origin
    (statusC, xC, yC) = ts.read()
    (statusC2, xC2, yC2) = (None,None,None)
    while True:
        gc.collect()
        buttonEvent(btn1s,btn1l,btn2,None)
        if loopEscape:
            break

        (statusC, xC, yC) = ts.read()

        if MenuEnterState == True:

            img_origin.draw_rectangle(0,50,320,140, color = (0,0,0), fill = True)
            
            if EndTraining == False:

                img_origin.draw_rectangle(110,70,100,100, color = (64,125,224), fill = True)
                img_origin.draw_rectangle(110,70,100,100, color = (255,255,255), fill = False)
                draw_multiline_text(img_origin,130,75,"모 델  학 습\n완 료 하 기", scale = 1.6)

                if statusC == ts.STATUS_RELEASE:
                    if(xC2 != None and yC2 != None):
                            if(110 < xC2 < 210 and 70 < yC2 < 170 ):
                                print("end click")
                                MenuEnterState = False
                                EndTraining = True
                                # restart(state_machine)
                                # state_machine.current_state = STATE
                    xC2 = None
                    yC2 = None
                elif statusC == ts.STATUS_MOVE or statusC == ts.STATUS_PRESS:
                    (statusC2, xC2, yC2) = (statusC, xC, yC)
            else:
                img_origin.draw_rectangle(0,50,320,140, color = (0,0,0), fill = True)
                
                img_origin.draw_rectangle(50,70,100,100, color = (64,125,224), fill = True)
                img_origin.draw_rectangle(50,70,100,100, color = (255,255,255), fill = False)
                draw_multiline_text(img_origin,70,75,"모 델  삭 제 \n및  재 학 습", scale = 1.6)

                img_origin.draw_rectangle(170,70,100,100, color = (159,123,255), fill = True)
                img_origin.draw_rectangle(170,70,100,100, color = (255,255,255), fill = False)
                draw_multiline_text(img_origin,190,75,"현 재  모 델 \n저 장 하 기", scale = 1.6)

                if statusC == ts.STATUS_RELEASE:
                    if(xC2 != None and yC2 != None):
                        if(50 < xC2 < 150 and 70 < yC2 < 170 ):
                            print("left click")
                            if(tagIdList):
                                del(tagIdList)
                                tagIdList= []
                            EndTraining = False
                            MenuEnterState = False
                            pass

                        elif(170 < xC2 < 270 and 70 < yC2 < 170):
                            print("right click")
                            MenuEnterState = False
                            haveToSave = True
                            break

                        xC2 = None
                        yC2 = None
                elif statusC == ts.STATUS_MOVE or statusC == ts.STATUS_PRESS:
                    (statusC2, xC2, yC2) = (statusC, xC, yC)
            

            lcd.display(img_origin)
            
            continue
        # i += 1
        # print("cnt :", i)
        clock.tick()                    # Update the FPS clock.
        img_origin = sensor.snapshot()
        od_img.draw_image(img_origin, 0,0)
        od_img.pix_to_ai()
        kpu.run_with_output(od_img)
        dect = kpu.regionlayer_yolo2()
        fps = clock.fps()
        if len(dect) > 0:
            print("dect:",dect)
            for l in dect :
                if tagSave == True and EndTraining == False:
                    if len(tagIdList) < len(colorList):
                        tagIdList.append(l[4])
                    tagSave = False
                
                index = find_index(l[4], tagIdList)
                if index == None:
                    img_origin.draw_rectangle(l[0],l[1],l[2],l[3], color=(255, 255, 255))
                    img_origin.draw_rectangle(l[0],l[1] - 20, 40, 20, color = (255,255,255), fill = True)
                    img_origin.draw_string(l[0] + 20,l[1] - 20 , obj_name[l[4]], color=(0,0,0), scale=1)
                else:
                    img_origin.draw_rectangle(l[0],l[1],l[2],l[3], color=colorList[index])
                    img_origin.draw_rectangle(l[0],l[1] - 20, 40, 20, color = colorList[index], fill = True, thickness = 2 )
                    img_origin.draw_string(l[0] + 20,l[1] - 20 , obj_name[l[4]], color=(0,0,0), scale=1)

                if EndTraining == False:
                    break
    
        # img_origin.draw_string(0, 0, "%2.1ffps" %(fps), color=(0, 60, 128), scale=1.0)
        if EndTraining == False:
            draw_multiline_text(img_origin,20, 50, "태 그\n{}".format(len(tagIdList)), color = colorList[len(tagIdList)], scale = 1.3)
        gc.collect()
        img_origin.draw_rectangle(0,0, 320, 25, color = (100,100,100), fill = True)
        img_origin.draw_string(10, 3, "뒤 로", color = (0,0,0))
        img_origin.draw_string(130, 3, "객 체  인 식 ", color = (0,0,0), scale = 1.2)
        img_origin.draw_string(300, 3, "학 습", color = (0,0,0))    
        lcd.display(img_origin)
    
    kpu.deinit()    
    gc.collect()

    print("break loop")
    global viewPage
    viewPage = None
    global prevPage, prevPageVar, whatToSave
    if isLoad:
        prevPage = createPage2
        if haveToSave:
            prevPageVar = True
            whatToSave = 4
        else:
            prevPageVar = False
            if tagIdList:
                del(tagIdList)
    else:
        if haveToSave:
            prevPage = createPage2
            prevPageVar = True
            whatToSave = 4
        else:
            prevPage = createPage3
            prevPageVar = None
            if tagIdList:
                del(tagIdList)


def qrPage(isLoad):

    #sensor.set_windowing((240, 240)) # look at center 240x240 pixels of the VGA resolution.
    #sensor.set_hmirror(True)
    #sensor.set_vflip(True)
    # sensor.skip_frames(time = 2000)
    sensor.set_auto_gain(False, gain_db = -1) 
    sensor.set_auto_whitebal(False, rgb_gain_db = (0,0,0)) 

    clock = time.clock()

    colorList = [
        (148,60,255),
        (255,255,0),
        (0,255,255),
        (255,51,153),
        (0,255,0),
        (255,153,51),
        (51,153,255),
        (255,51,51),
        (0,205,102),
        (255,200,200)
    ]


    def btn2():
        nonlocal loopEscape

        loopEscape = True

    def btn1s():
        global tagSave
        tagSave = True
        pass
        # global boot_btn, MenuEnterState
        # MenuEnterState = False
        # boot_btn.st.emit_event(EVENT.BOOT_KEY)

    
    
    def btn1l():
        nonlocal MenuEnterState
        MenuEnterState = True
        pass
        # global boot_btn, MenuEnterState
        # MenuEnterState = True
        # boot_btn.st.emit_event(EVENT.BOOT_KEY_LONG_PRESS)

    loopEscape = False
    EndTraining = False
    global tagIdList
    if isLoad != False:
        tagIdList = dataLoadingFunction(isLoad)
        EndTraining = True
    else:
        tagIdList = []
        EndTraining = False

    global tagSave
    tagSave = False
    loopEscape = False
    MenuEnterState = False
    haveToSave = False
    (statusC, xC, yC) = ts.read()
    (statusC2, xC2, yC2) = (None,None,None)
    global img_origin
    
    while True:
        gc.collect()
        buttonEvent(btn1s,btn1l,btn2,None)
        if loopEscape:
            break

        (statusC, xC, yC) = ts.read()

        if MenuEnterState == True:

            img_origin.draw_rectangle(0,50,320,140, color = (0,0,0), fill = True)
            
            if EndTraining == False:

                img_origin.draw_rectangle(110,70,100,100, color = (64,125,224), fill = True)
                img_origin.draw_rectangle(110,70,100,100, color = (255,255,255), fill = False)
                draw_multiline_text(img_origin,130,75,"모 델  학 습\n완 료 하 기", scale = 1.6)

                if statusC == ts.STATUS_RELEASE:
                    if(xC2 != None and yC2 != None):
                            if(110 < xC2 < 210 and 70 < yC2 < 170 ):
                                print("end click")
                                MenuEnterState = False
                                EndTraining = True
                                # restart(state_machine)
                                # state_machine.current_state = STATE
                    xC2 = None
                    yC2 = None
                elif statusC == ts.STATUS_MOVE or statusC == ts.STATUS_PRESS:
                    (statusC2, xC2, yC2) = (statusC, xC, yC)
            else:
                img_origin.draw_rectangle(0,50,320,140, color = (0,0,0), fill = True)
                
                img_origin.draw_rectangle(50,70,100,100, color = (64,125,224), fill = True)
                img_origin.draw_rectangle(50,70,100,100, color = (255,255,255), fill = False)
                draw_multiline_text(img_origin,70,75,"모 델  삭 제 \n및  재 학 습", scale = 1.6)

                img_origin.draw_rectangle(170,70,100,100, color = (159,123,255), fill = True)
                img_origin.draw_rectangle(170,70,100,100, color = (255,255,255), fill = False)
                draw_multiline_text(img_origin,190,75,"현 재  모 델 \n저 장 하 기", scale = 1.6)

                if statusC == ts.STATUS_RELEASE:
                    if(xC2 != None and yC2 != None):
                        if(50 < xC2 < 150 and 70 < yC2 < 170 ):
                            print("left click")
                            if(tagIdList):
                                del(tagIdList)
                                tagIdList= []
                            EndTraining = False
                            MenuEnterState = False
                            pass

                        elif(170 < xC2 < 270 and 70 < yC2 < 170):
                            print("right click")
                            MenuEnterState = False
                            haveToSave = True
                            break

                        xC2 = None
                        yC2 = None
                elif statusC == ts.STATUS_MOVE or statusC == ts.STATUS_PRESS:
                    (statusC2, xC2, yC2) = (statusC, xC, yC)
            

            lcd.display(img_origin)
            
            continue





        clock.tick()
        img_origin = sensor.snapshot()
        qrCodes = img_origin.find_qrcodes()
        for code in qrCodes:
            if tagSave == True and EndTraining == False:
                if len(tagIdList) < len(colorList):
                    tagIdList.append(code.payload())
                tagSave = False

            index = find_index(code.payload(),tagIdList)
            if index == None:
                img_origin.draw_rectangle(code.rect(), color = (255,255,255))
            else:
                img_origin.draw_rectangle(code.rect(), color = colorList[index])
                img_origin.draw_rectangle(code.rect()[0],code.rect()[1] - 20, 40, 20,color = colorList[index], fill = True)
                img_origin.draw_string(code.rect()[0] + 20,code.rect()[1] - 20, "ID: {}".format(index+1), color = (0,0,0))
            # print(code)
            if EndTraining == False:
                break

        if EndTraining == False:
            draw_multiline_text(img_origin,20, 50, "태 그\n{}".format(len(tagIdList)), color = colorList[len(tagIdList)], scale = 1.3)

        # print(clock.fps())
        img_origin.draw_rectangle(0,0, 320, 25, color = (100,100,100), fill = True)
        img_origin.draw_string(10, 3, "뒤 로", color = (0,0,0))
        img_origin.draw_string(130, 3, "QR  인 식 ", color = (0,0,0), scale = 1.2)
        img_origin.draw_string(300, 3, "학 습", color = (0,0,0))

        lcd.display(img_origin)

    gc.collect()
    print("break loop")
    global viewPage
    viewPage = None
    global prevPage, prevPageVar, whatToSave
    if isLoad:
        prevPage = createPage2
        if haveToSave:
            prevPageVar = True
            whatToSave = 5
        else:
            prevPageVar = False
            if tagIdList:
                del(tagIdList)
    else:
        if haveToSave:
            prevPage = createPage2
            prevPageVar = True
            whatToSave = 5
        else:
            prevPage = createPage3
            prevPageVar = None
            if tagIdList:
                del(tagIdList)
    sensor.set_auto_gain(True) # must turn this off to prevent image washout...
    sensor.set_auto_whitebal(True)

def colorPage(isLoad):

    # sensor.reset()
    sensor.set_auto_gain(False, gain_db = -1) 
    sensor.set_auto_whitebal(False, rgb_gain_db = (0,0,0)) 
    clock = time.clock()

    r = [(320//2)-(50//2), (240//2)-(50//2), 50, 50] # 50x50 center of QVGA.

    threshold = [50, 50, 0, 0, 0, 0] # Middle L, A, B values.

    colorList = [
        (148,60,255),
        (255,255,0),
        (0,255,255),
        (255,51,153),
        (0,255,0),
        (255,153,51),
        (51,153,255),
        (255,51,51),
        (0,205,102),
        (255,200,200)
    ]


    def btn2():
        nonlocal loopEscape

        loopEscape = True

    def btn1s():
        global tagSave
        tagSave = True
        pass
        # global boot_btn, MenuEnterState
        # MenuEnterState = False
        # boot_btn.st.emit_event(EVENT.BOOT_KEY)

    
    
    def btn1l():
        nonlocal MenuEnterState
        MenuEnterState = True
        pass
        # global boot_btn, MenuEnterState
        # MenuEnterState = True
        # boot_btn.st.emit_event(EVENT.BOOT_KEY_LONG_PRESS)

    loopEscape = False
    EndTraining = False
    global tagIdList
    if isLoad != False:
        tagIdList = dataLoadingFunction(isLoad)
        EndTraining = True
    else:
        tagIdList = []
        EndTraining = False

    global tagSave
    tagSave = False
    loopEscape = False
    MenuEnterState = False
    haveToSave = False
    (statusC, xC, yC) = ts.read()
    (statusC2, xC2, yC2) = (None,None,None)
    global img_origin
    
    while True:
        gc.collect()
        buttonEvent(btn1s,btn1l,btn2,None)
        if loopEscape:
            break

        (statusC, xC, yC) = ts.read()

        if MenuEnterState == True:

            img_origin.draw_rectangle(0,50,320,140, color = (0,0,0), fill = True)
            
            if EndTraining == False:

                img_origin.draw_rectangle(110,70,100,100, color = (64,125,224), fill = True)
                img_origin.draw_rectangle(110,70,100,100, color = (255,255,255), fill = False)
                draw_multiline_text(img_origin,130,75,"모 델  학 습\n완 료 하 기", scale = 1.6)

                if statusC == ts.STATUS_RELEASE:
                    if(xC2 != None and yC2 != None):
                            if(110 < xC2 < 210 and 70 < yC2 < 170 ):
                                print("end click")
                                MenuEnterState = False
                                EndTraining = True
                                # restart(state_machine)
                                # state_machine.current_state = STATE
                    xC2 = None
                    yC2 = None
                elif statusC == ts.STATUS_MOVE or statusC == ts.STATUS_PRESS:
                    (statusC2, xC2, yC2) = (statusC, xC, yC)
            else:
                img_origin.draw_rectangle(0,50,320,140, color = (0,0,0), fill = True)
                
                img_origin.draw_rectangle(50,70,100,100, color = (64,125,224), fill = True)
                img_origin.draw_rectangle(50,70,100,100, color = (255,255,255), fill = False)
                draw_multiline_text(img_origin,70,75,"모 델  삭 제 \n및  재 학 습", scale = 1.6)

                img_origin.draw_rectangle(170,70,100,100, color = (159,123,255), fill = True)
                img_origin.draw_rectangle(170,70,100,100, color = (255,255,255), fill = False)
                draw_multiline_text(img_origin,190,75,"현 재  모 델 \n저 장 하 기", scale = 1.6)

                if statusC == ts.STATUS_RELEASE:
                    if(xC2 != None and yC2 != None):
                        if(50 < xC2 < 150 and 70 < yC2 < 170 ):
                            print("left click")
                            if(tagIdList):
                                del(tagIdList)
                                tagIdList= []
                            EndTraining = False
                            MenuEnterState = False
                            
                            pass

                        elif(170 < xC2 < 270 and 70 < yC2 < 170):
                            print("right click")
                            MenuEnterState = False
                            haveToSave = True
                            break

                        xC2 = None
                        yC2 = None
                elif statusC == ts.STATUS_MOVE or statusC == ts.STATUS_PRESS:
                    (statusC2, xC2, yC2) = (statusC, xC, yC)
            

            lcd.display(img_origin)
            
            continue

        if(EndTraining == False):
            if tagSave == True:

                for i in range(60):
                    img_origin = sensor.snapshot()
                    hist = img_origin.get_histogram(roi=r)
                    lo = hist.get_percentile(0.01) # Get the CDF of the histogram at the 1% range (ADJUST AS NECESSARY)!
                    hi = hist.get_percentile(0.99) # Get the CDF of the histogram at the 99% range (ADJUST AS NECESSARY)!
                    # Average in percentile values.
                    threshold[0] = (threshold[0] + lo.l_value()) // 2
                    threshold[1] = (threshold[1] + hi.l_value()) // 2
                    threshold[2] = (threshold[2] + lo.a_value()) // 2
                    threshold[3] = (threshold[3] + hi.a_value()) // 2
                    threshold[4] = (threshold[4] + lo.b_value()) // 2
                    threshold[5] = (threshold[5] + hi.b_value()) // 2
                    for blob in img_origin.find_blobs([threshold], pixels_threshold=100, area_threshold=100, merge=True, margin=10):
                        img_origin.draw_rectangle(blob.rect())
                        img_origin.draw_cross(blob.cx(), blob.cy())
                        img_origin.draw_rectangle(r)

                    draw_multiline_text(img_origin,20, 50, "태 그\n{}".format(len(tagIdList)), color = colorList[len(tagIdList)], scale = 1.3)

                    img_origin.draw_rectangle(40,50,200,20,(150,150,150),thickness = 0, fill = True)
                    img_origin.draw_rectangle(40,50,(i*2),20,(255,0,0),thickness = 0, fill = True)
                    img_origin.draw_rectangle(40,50,120,20,(255,255,255),thickness = 1, fill = False)
                    img_origin.draw_string(180, 50, "%2.1f 완 료"%(100*i/60))
                    img_origin.draw_rectangle(0,0, 320, 25, color = (100,100,100), fill = True)
                    img_origin.draw_string(10, 3, "뒤 로", color = (0,0,0))
                    img_origin.draw_string(130, 3, "색 상  인 식 ", color = (0,0,0), scale = 1.2)
                    img_origin.draw_string(300, 3, "학 습", color = (0,0,0))
                    lcd.display(img_origin)
                tagIdList.append(threshold)
                tagSave = False
                threshold = [50, 50, 0, 0, 0, 0] # Middle L, A, B values.
            else:
                img_origin = sensor.snapshot()
                img_origin.draw_rectangle(r)
                # for blob in img_origin.find_blobs([threshold], pixels_threshold=100, area_threshold=100, merge=True, margin=10):
                #     img_origin.draw_rectangle(blob.rect())
                #     img_origin.draw_cross(blob.cx(), blob.cy())
                draw_multiline_text(img_origin,20, 50, "태 그\n{}".format(len(tagIdList)), color = colorList[len(tagIdList)], scale = 1.3)
                # print(clock.fps())
                img_origin.draw_rectangle(0,0, 320, 25, color = (100,100,100), fill = True)
                img_origin.draw_string(10, 3, "뒤 로", color = (0,0,0))
                img_origin.draw_string(130, 3, "색 상  인 식 ", color = (0,0,0), scale = 1.2)
                img_origin.draw_string(300, 3, "학 습", color = (0,0,0))
                lcd.display(img_origin)
        else:
                            
            clock.tick()
            img_origin = sensor.snapshot()
            for i, thr in enumerate(tagIdList):
                for blob in img_origin.find_blobs([thr], pixels_threshold=100, area_threshold=100, merge=True, margin=10):
                    img_origin.draw_rectangle(blob.rect(), color = colorList[i], thickness = 2)
                    img_origin.draw_cross(blob.cx(), blob.cy())
            # print(clock.fps())
            img_origin.draw_rectangle(0,0, 320, 25, color = (100,100,100), fill = True)
            img_origin.draw_string(10, 3, "뒤 로", color = (0,0,0))
            img_origin.draw_string(130, 3, "색 상  인 식 ", color = (0,0,0), scale = 1.2)
            img_origin.draw_string(300, 3, "학 습", color = (0,0,0))
            lcd.display(img_origin)


    sensor.set_auto_gain(True) # must be turned off for color tracking
    sensor.set_auto_whitebal(True) # must be turned off for color tracking

    gc.collect()
    print("break loop")
    global viewPage
    viewPage = None
    global prevPage, prevPageVar, whatToSave
    if isLoad:
        prevPage = createPage2
        if haveToSave:
            prevPageVar = True
            whatToSave = 6
        else:
            prevPageVar = False
            if tagIdList:
                del(tagIdList)
    else:
        if haveToSave:
            prevPage = createPage2
            prevPageVar = True
            whatToSave = 6
        else:
            prevPage = createPage3
            prevPageVar = None
            if tagIdList:
                del(tagIdList)


def createPage4(): ## 설정
    # Initialize page4Div with background color
    global img_origin
    img_origin.draw_rectangle(0,0,320,240,color = (0,0,0), fill = True)

    page4Div = ButtonDiv(img_origin)
    page4Div.set(2, 0, 0, 320, 240, (0, 0, 0), True)


    # Initialize view
    page4Div.viewinit()
    return page4Div


def createPage5(): ## Teach & Play
    # Initialize variables

    # Initialize page4Div with background color
    global img_origin
    img_origin.draw_rectangle(0,0,320,240,color = (0,0,0), fill = True)

    page4Div = ButtonDiv(img_origin)
    page4Div.set(2, 0, 0, 320, 240, (0, 0, 0), True)


    # Initialize view
    page4Div.viewinit()
    return page4Div

def createPage6(): ## language["language" setting
    # Initialize variables

        
    # Initialize page4Div with background color
    global img_origin
    img_origin.draw_rectangle(0,0,320,240,color = (0,0,0), fill = True)

    page4Div = ButtonDiv(img_origin)
    page4Div.set(2, 0, 0, 320, 240, (0, 0, 0), True)


    # Initialize view
    page4Div.viewinit()
    return page4Div

def onClickEvent1():
    pass
    # global mOff, longPressState
    # global prevPage, prevPageVar

    # switch_view(prevPage)

def onClickEvent2():
    global mOff, longPressState
    global prevPage, prevPageVar
    if prevPageVar !=None:
        
        switch_view(prevPage, prevPageVar)
        prevPageVar = None
    else:
        switch_view(prevPage)

def onLongClickEvent1():
    pass
    # global mOff, longPressState
    # global prevPage

    # switch_view(prevPage)

def onLongClickEvent2():
    pass
    # global mOff, longPressState
    # global prevPage

    # switch_view(prevPage)


def buttonEvent(btn1F, btn1LF, btn2F, btn2LF):
    global btn, btn2, viewPage, prevPage, btn1LongPressed,btn2LongPressed, btnPress,btnPress2,led,btnToggle,btnToggle2, btn_tick_hue
    btnV = btn.value()
    btnV2 = btn2.value()
    btnTimer = time.ticks_ms()
    if(btnV == 0 and btn1LongPressed == 0):
        btnToggle = 1
        btnPress += time.ticks_diff(btnTimer, btn_tick_hue)
        # print(btnPress, btnTimer, btn_tick_hue)
        if(btnPress > 800):
            btnToggle = 0
            btnPress = 0
            btn1LongPressed = 1
            if(btn1LF!=None):
                btn1LF()
            led.set_led(0,(10,0,0))
            led.display()
    elif(btnV == 1 and btnToggle == 1):
        btnToggle = 0
        btnPress = 0
        if(btn1F!=None):
            btn1F()
        led.set_led(0,(10,10,10))
        led.display()
    elif(btnV == 1):
        btn1LongPressed = 0

    if(btnV2 == 1 and btn2LongPressed == 0):
        btnToggle2 = 1
        btnPress2 += time.ticks_diff(btnTimer, btn_tick_hue)
        if(btnPress2 > 800):
            btnToggle2 = 0
            btnPress2 = 0
            btn2LongPressed = 1
            # if(btn2F!=None):
            #     btn2LF()
            import machine
            machine.reset()
            
            led.set_led(1,(0,10,0))
            led.display()
    elif(btnV2 == 0 and btnToggle2 == 1):
        btnToggle2 = 0
        btnPress2 = 0        
        if(btn2F!=None):
            btn2F()
        led.set_led(1,(0,0,10))
        led.display()
    elif(btnV2 == 0):
        btn2LongPressed = 0

    btn_tick_hue = btnTimer




viewPage = None
switch_view(createMainPage)
prevPage = createMainPage
prevPageVar = None
btn1LongPressed = 0
btn2LongPressed = 0
while True:
    # # print("startLoop")
    showing()
    (status, x, y) = ts.read()
    if dpPress == 1 and status == ts.STATUS_RELEASE:
        dpPress = 0
        if(longPressState == 1):
            longPressState = 0
    viewPage.clickEMain(status, x, y)
    gc.collect()
    # # print("endLoop")
    

    buttonEvent(onClickEvent1,onLongClickEvent1,onClickEvent2,onLongClickEvent2)
    time.sleep(0.0000001)
    