'''
MiniFRC driver station 2017
By Squidfairy/Goosefairy/ddthj/michael/Terrorbytes/FRC4561/a couple goblins/you get the idea

TODO:
comment
better line wrapping
multiple config files support
support for naming outputs in package
fix console dissappears when alt+tabbing bug
'''
version = 4.0

import pygame, time, serial, random,os

WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,0,255)

pygame.init()
resolution = (1280,720) #Resolution of the screen opened    If using fullscreen use the resolution of your monitor
baudrate = 9600
screen = pygame.display.set_mode(resolution,pygame.HWSURFACE|pygame.DOUBLEBUF|pygame.FULLSCREEN) #pygame.RESIZEABLE for windowed mode, pygame.FULLSCREEN for fullscreen, HWSURFACE and DOUBLEBUF are only used if in fullscreen mode
pygame.display.set_caption("MiniFRC Driver Station 2018 V%s" % (str(version)))
Text = pygame.font.SysFont("courier",20)
screen.fill(WHITE)
pygame.display.update()

class Console(): #Console class is the left most section of the screen that displays any messages logged
    def __init__(self):
        self.stack = []             #List of all messages logge
        self.width = 500            #The width of the console window in pixels. The UI is dynamic and so changing this shouldn't break anything
        self.running = False        #If False the window will be updated after every message logged, if True it will only be updated when the render() method is called
        self.NeedUpdate = True      #Variable to track if there has been an update made that needs rendering, improves performance to only render the console when it's updated
        self.scroll = 0
        self.ScrollLimit = 0
        
    def log(self,text="",color=None,display=True): # method used to add a messages to the console
        text=str(text)
        print(text)
       
        if display: #Display specifies whether to show the message on the UI. It will be printed to the python window regardless
            if(color == None):
                if(text[:6] == "[INFO]") or (text[:8] == "[NOTICE]"):
                    color = BLUE
                elif(text[:7] == "[ERROR]") or (text[:9] == "[WARNING]"):
                    color = RED
                elif(text[:1] == '/'):
                    color = BLUE
                    text = text[1:]
                else:
                    color = BLACK

            #If the message is too long to display on one line this will break it into multiple
            #Needs to be made better but it works
            self.stack.append([str(text)[:70],color])
            for i in range(1,int(len(text)/70+1)):
                self.stack.append([str(text)[i*70:(i+1)*70],color])

            #If not running this re-renders the console
            if not self.running:
                screen.fill(WHITE)
                self.render()
                pygame.display.update((0,20,self.width,resolution[1]-70))

            #Deals with scrolling and the limiting how far you can scroll in either direction
            self.ScrollLimit = len(self.stack)*14-resolution[1]+70
            if (self.ScrollLimit < 0):
                self.ScrollLimit = 0
            if(self.scroll <= -self.ScrollLimit+14):
                self.scroll = -self.ScrollLimit
            
            self.NeedUpdate = True      #Marks the console in need of re-rendering
        
    def render(self):       #Method that renders the console and updates that portion of the screen
        if self.NeedUpdate:
            #Rendering text
            for i in range(len(self.stack)):
                rendertext(12,self.stack[i][0],1,i*14 + 20 + self.scroll,self.stack[i][1])

            #Drawing the border
            #pygame.draw.rect(screen,WHITE,(0,0,self.width,20))     #Not sure if this is strictly necessary, if the FPS counter startings displaying weird uncomment this
            pygame.draw.rect(screen,BLACK,(0,20,self.width,resolution[1]-70), 1)

            pygame.display.update((0,20,self.width,resolution[1]-70))   #Updates only the portion of the screen with the console

        self.NeedUpdate = False     #Marks the console not in need of re-rendering

    def clear(self): #Method to clear the console of all messages, I made it and then never used it but it seems potentially useful
        self.stack = []
        self.scroll = 0
        self.render()
      
    def bail(self):     #Method to log all messages in a logfile if something goes wrong
        f = open('LOGFILE.txt',"w")
        for item in self.stack:
            f.write(item[0] + '\n')
        f.close()

class Readout():        #Class that handles all of the instrument readouts
    def __init__(self):
        self.AxisWidth = 500        #Width of the Axes portion
        self.ButtonWidth = 150      #Width of the Buttons portion
        self.HatWidth = 75          #Width of the Hats portion
        self.AxisRange = [console.width + 10, console.width + self.AxisWidth + 10]              #Stores the left and right bounds of the Axes portion
        self.ButtonRange = [self.AxisRange[1] + 10,self.AxisRange[1] + self.ButtonWidth + 10]   #Stores the left and right bounds of the buttions portion
        self.HatRange = [self.ButtonRange[1] + 10,self.ButtonRange[1] + self.HatWidth + 10]     #Stores the left and right bounds of the hats portion
        self.AxisRange.append((self.AxisRange[0]+self.AxisRange[1])/2)              #Adds the midpoint between left and right bound to the list 
        self.HatRange.insert(1,(self.HatRange[0]+self.HatRange[1])/3)               #Inserts the one third point between left and right bounds
        self.HatRange.insert(2,2*(self.HatRange[0]+self.HatRange[1])/3)             #Inserts the two thirds point between left and right bounds, the HatRange list will be [LeftBound, 1/3 value, 2/3 value, RightBound]

    def render(self):   #Method that renders the readout
        for i in range(len(Axes)):      #Axes
            vertPos = i * 75 + 10
            rendertext(15,Axes[i].Name,self.AxisRange[0], vertPos)
            pygame.draw.line(screen, BLACK,(self.AxisRange[0],vertPos+20),(self.AxisRange[1],vertPos+20))
            pygame.draw.line(screen, BLACK,(self.AxisRange[0],vertPos+25),(self.AxisRange[0],vertPos+15))
            pygame.draw.line(screen, BLACK,(self.AxisRange[1],vertPos+25),(self.AxisRange[1],vertPos+15))
            pygame.draw.rect(screen, RED, (self.AxisRange[2],vertPos+17,Axes[i].getValue()*self.AxisWidth/2,7))

        for i in range(len(Buttons)):   #Buttons
            vertPos = i * 25 + 10
            if Buttons[i].getValue() == 1:
                pygame.draw.rect(screen, RED, (self.ButtonRange[0],vertPos,self.ButtonWidth,25))
            pygame.draw.rect(screen, BLACK, (self.ButtonRange[0],vertPos,self.ButtonWidth,25), 1)
            rendertext(15,Buttons[i].Name,self.ButtonRange[0]+5,vertPos+5)

        for i in range(len(Hats)):      #Hats
            vertPos = i * self.HatWidth + 10
            hatValue = Hats[i].getValue()
            width = self.HatWidth/3
            pygame.draw.rect(screen,BLACK, (self.HatRange[0],vertPos,self.HatWidth,self.HatWidth),1)
            pygame.draw.rect(screen,RED, (self.HatRange[0]+(hatValue[0]+1)*width,vertPos + (1-hatValue[1])*width,width,width))

        #Drawing the Live Package Readout
        pygame.draw.rect(screen, GREEN, (0,resolution[1]-50,resolution[0],50))
        rendertext(20,"Live Package Readout:",10,resolution[1]-50)
        rendertext(20,package,10,resolution[1]-30)
            
class joystick():
    def __init__(self,Object):
        self.Object = Object
        self.Object.init()
        self.AxesCount = Object.get_numaxes()
        self.ButtonsCount = Object.get_numbuttons()
        self.HatsCount = Object.get_numhats()
        #self.JoyInputs = [[0 for i in range(self.AxesCount)], [0 for i in range(self.ButtonsCount)], [0 for i in range(self.HatsCount)]]

class axis():       #Class used to store info about and axis
    def __init__(self,name,inputtype,data):
        self.Name = name
        self.Type = inputtype #type is a boolean representing the input source 0/False is button, 1/True is Joystick
        self.DeadZone = 0 

        if self.Type:   #If joystick
            self.cache = 0
            self.joystickNum = int(data[0])
            self.joystickAxis = int(data[1])
            Inputs[self.joystickNum,self.joystickAxis,0] = self

        else:           #If keyboard
            self.cache = [0,0]
            self.axis = [str(data[0]),str(data[1])]
            Inputs[self.axis[0],0] = self
            Inputs[self.axis[1],0] = self
        
        #Add this object to the inputs list and to the Axes list
        Axes.append(self)
        Controls.append(self)
        
    def deaden(self,value):
        if abs(value) > self.DeadZone:
            return round(value,axisPresicion)
        else:
            return 0

    def UpdateCache(self,value,key=''):
        if self.Type:
            self.cache = Joysticks[self.joystickNum].Object.get_axis(self.joystickAxis)
        else:
            self.cache[self.axis.index(key)] = value
        return self.cache
            
    def getValue(self):
        if self.Type:
            return float(self.deaden(self.cache))
            #return round(Joysticks[self.joystickNum].Object.get_axis(self.joystickAxis),axisPresicion)
        else:
            return float(self.cache[0]-self.cache[1])

    def getPack(self):
        return self.getValue()

class button():
    def __init__(self,name,inputtype,data):
        self.Name = name
        self.Type = inputtype
        self.cache = 0
        
        if self.Type:
            self.joystickNum = int(data[0])
            self.joystickButton = int(data[1])
            Inputs[self.joystickNum,self.joystickButton,1] = self
        else:
            self.keyboardButton = str(data[0])
            Inputs[self.keyboardButton,1] = self
            
        Buttons.append(self)
        Controls.append(self)
        
    def UpdateCache(self,value):
        self.cache = value
        return self.cache
            
    def getValue(self):
        return float(self.cache)

    def getPack(self):
        return self.getValue()

class hat():
    def __init__(self,name,data):
        self.Name = name
        self.joystickNum = int(data[0])
        self.joystickHat = int(data[1])
        self.cache = [0,0]
        
        Hats.append(self)
        Controls.append(self)
        Inputs[self.joystickNum,self.joystickHat,2] = self
    
    def UpdateCache(self,value):
        self.cache = value
        return self.cache
            
    def getValue(self):
        return self.cache
        #return Joysticks[self.joystickNum].Object.get_hat(self.joystickHat)

    def getPack(self):
        return "%s;%s" % (float(self.cache[0]),float(self.cache[1]))

def rendertext(scale,text,x,y,color=BLACK):     #General purpose method for rendering text        
    font = pygame.font.SysFont("courier",scale)
    thing = font.render(text,1,color)
    screen.blit(thing,(x,y))        #Pygame is stupid in that you can't render text directly on an existing surface (screen), you have to create it on a new surface and copy(blit) it over to an existing one

def connect(default,baudrate):
    try:
        s = serial.Serial(str(default),9600,writeTimeout = 1)
        return s
    except:
        console.log("[WARNING] Couldn't connect to robot with specified COM port in config file")
            
    for i in range(50):
        com = "COM" + str(i)
        try:
            s = serial.Serial(com,9600,writeTimeout = 1)
            return s
        except:
            console.log("[WARNING] Couldn't connect to robot with port " + com)
    console.log()
    console.log("[WARNING] Couldn't connect to robot on ANY ports")
    flag = True
    return False


 
flag = False
test_mode = False
joystick_test_mode = False
console = Console()
com = ""
package = "z"
Inputs, Controls, Joysticks, Axes, Buttons, Hats = {},[],[],[],[],[]
axisPresicion = 2 
console.log("MiniFRC Driver Station 2018 V%s" % (str(version)))
console.log("Booting...")

#Initialise Joysticks
for i in range(pygame.joystick.get_count()):
    Joysticks.append(joystick(pygame.joystick.Joystick(i)))
console.log("[INFO] %s joystick(s) loaded: " % (pygame.joystick.get_count()) + str([Joysticks[i].Object.get_name() for i in range(len(Joysticks))]))

#Find config.txt
try:
    f = open("config.txt","r")
    console.log("[INFO] Found config.txt, reading...")
    configRaw = f.read().split('\n')
    f.close()
except Exception as e:
    console.log('[WARNING] Could not find/open "config.txt"')
    console.log("[WARNING] Error logged as: %s"%(e))
    if test_mode == False:
        flag = True

#Read and interpret config.txt
for line in configRaw:
    if len(line)>0:
        if line.find("COM")!= -1:
            if line.find("test") != -1:
                test_mode = True
                console.log("[INFO] Driver Station in Test Mode, not connecting to robot")
            else:
                com = line.strip('\n')       
        elif line.find("joysticktest") != -1:
            joystick_test_mode = True
            console.log("[INFO] Joystick test mode enabled, all joystick input devices will be initialised")

            for i in range(pygame.joystick.get_count()):
                for j in range(Joysticks[i].Object.get_numaxes()):
                    axis("J%s Axis%s" % (i+1,j+1),True,[i,j])
                for j in range(Joysticks[i].Object.get_numbuttons()):
                    button("J%s Button%s" % (i+1,j+1),True,[i,j])
                for j in range(Joysticks[i].Object.get_numhats()):
                    hat("J%s Hat%s" % (i+1,j+1),[i,j])
                        
        elif line.find("BAUD")!=-1:
            baudrate = int(line.split(",")[1])
            console.log("[NOTICE] Changed default Baudrate from 9600 to %s"%(str(baudrate)))

        if not joystick_test_mode:
            if line.find("axis") != -1:
                v = line.split(",")
                try:
                    axis(v[1],v[2]=='j',v[3:])
                except Exception as e:
                    console.log("[ERROR] Config file not formated properly")
                    console.log("[ERROR] Initialising axis %s failed" % v[1])
                    console.log("[ERROR] Error logged as: %s"%(e))
            elif line.find("button") != -1:
                v = line.split(",")
                try:
                    button(v[1],v[2]=='j',v[3:])
                except Exception as e:
                    console.log("[ERROR] Config file not formated properly")
                    console.log("[ERROR] Initialising button %s failed" % v[1])
                    console.log("[ERROR] Error logged as: %s"%(e))
            elif line.find("hat") != -1:
                v = line.split(",")
                try:
                    hat(v[1],v[2:])
                except Exception as e:
                    console.log("[ERROR] Config file not formated properly")
                    console.log("[ERROR] Initialising hat %s failed" % v[1])
                    console.log("[ERROR] Error logged as: %s"%(e))           
console.log("[NOTICE] Config file read successfully")


if not test_mode:
    console.log("[INFO] Attempting connection with robot")
    s = connect(com,baudrate)
    if s != False:
        console.log("[INFO] Connected to robot!")
    else:
        flag = True

          

readout = Readout()
#console.clear()
console.running = True
Exit = False
Clock = pygame.time.Clock()
if not flag:
    console.log("[INFO] Driver station is now ACTIVE")
    console.log("[INFO] Press escape to exit driver station")
while (not Exit) and (not flag):
    Clock.tick(60)
    
    try:
        #Event handling
        events = pygame.event.get()
        #keys = pygame.key.get_pressed()
        for event in events:
            if event.type == pygame.JOYAXISMOTION:
                if ((event.joy,event.axis,0) in Inputs):
                    Inputs[(event.joy,event.axis,0)].UpdateCache(round(event.value,axisPresicion))
            elif event.type == pygame.JOYBUTTONUP:
                if ((event.joy,event.button,1) in Inputs):
                    Inputs[(event.joy,event.button,1)].UpdateCache(0)
            elif event.type == pygame.JOYBUTTONDOWN:
                if ((event.joy,event.button,1) in Inputs):
                    Inputs[(event.joy,event.button,1)].UpdateCache(1)
            elif event.type == pygame.JOYHATMOTION:
                if ((event.joy,event.hat,2) in Inputs):
                    Inputs[(event.joy,event.hat,2)].UpdateCache(event.value)
                    
            elif event.type == pygame.KEYDOWN:
                if ((pygame.key.name(event.key),1) in Inputs):
                    Inputs[(pygame.key.name(event.key),1)].UpdateCache(1)
                elif ((pygame.key.name(event.key),0) in Inputs):
                    Inputs[(pygame.key.name(event.key),0)].UpdateCache(1,pygame.key.name(event.key))
                elif event.key == 27:
                    console.log("[NOTICE] Escape key pressed, shutting down")
                    Exit = True
            elif event.type == pygame.KEYUP:
                if ((pygame.key.name(event.key),1) in Inputs):
                    Inputs[(pygame.key.name(event.key),1)].UpdateCache(0)
                elif ((pygame.key.name(event.key),0) in Inputs):
                    Inputs[(pygame.key.name(event.key),0)].UpdateCache(0,pygame.key.name(event.key))
                    
                
            elif event.type == pygame.QUIT:
                Exit = True
                break
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    console.scroll += 100
                    console.NeedUpdate = True
                    if console.scroll > 0:
                        console.scroll = 0
                if event.button == 5:
                    console.scroll += -100
                    console.NeedUpdate = True
                    if console.scroll < -console.ScrollLimit:
                        console.scroll = -console.ScrollLimit
    except Exception as e:
            console.log("[ERROR] Error raised while handling events")
            console.log("[ERROR] Logged as: %s" % (e))
            flag = True
       
    #Creating package
    try:
        package = "z"
        for i in Controls:
            package += str(i.getPack()) + ";"
    except Exception as e: 
        console.log("[ERROR] Error raised while creating bluetooth package")
        console.log("[ERROR] Logged as " + str(e))
        flag = True

    #Sending package via Bluetooth
    if test_mode == False:
        try:
            s.write(bytes(package,'utf-8'))
        except Exception as e:
            console.log("[ERROR] Error raised while sending bluetooth package")
            console.log("[ERROR] Logged as: %s" % (e))
            flag = True

    #Drawing screen
    try:
        screen.fill(WHITE)
        #console.NeedUpdate = True
        console.render()
        readout.render()
        rendertext(15,"FPS:" + str(1000/Clock.get_time()),0,0)
        pygame.display.update([(console.width,0,resolution[0],resolution[1]),(0,0,console.width,20),(0,resolution[1]-50,console.width,50)])
    except Exception as e:
        console.log("[ERROR] Error raised while drawing the screen")
        console.log("[ERROR] Logged as " + str(e))
        flag = True



if flag:
    console.log("[WARNING] Normal operation has ended, check error messages above")
    console.log("[WARNING] Press the escape key to exit")
    console.NeedUpdate = True
    while flag:
        Clock.tick(60)
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                flag = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    console.scroll += 100
                    if console.scroll > 0:
                        console.scroll = 0
                if event.button == 5:
                    console.scroll += -100
                    if console.scroll < -console.ScrollLimit:
                        console.scroll = -console.ScrollLimit
            elif event.type == pygame.KEYDOWN:
                if event.key == 27:
                    console.log("[NOTICE] Escape key pressed, shutting down")
                    flag = False

        screen.fill((0,0,75))
        console.NeedUpdate = True
        console.render()
        rendertext(15,"FPS:" + str(1000/Clock.get_time()),0,0,WHITE)
        pygame.display.update()


console.bail()
pygame.quit()
exit()
