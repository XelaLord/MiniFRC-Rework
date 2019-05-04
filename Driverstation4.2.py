'''
MiniFRC driver station 2017
By Squidfairy/Goosefairy/ddthj/michael/Terrorbytes/FRC4561/a couple goblins/you get the idea

TODO:
comment
better line wrapping
multiple config files support
fix console dissappears when alt+tabbing bug
'''
version = 4.2

import pygame, time, serial, serial.tools.list_ports, random, os, sys, traceback, glob

WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,0,255)

#Setup pygame and the driver station window
pygame.init()
resolution = (1600,400) # Resolution of the screen opened    If using fullscreen use the resolution of your monitor
baudrate = 9600
screen = pygame.display.set_mode(resolution,pygame.RESIZABLE)# pygame.HWSURFACE|pygame.DOUBLEBUF|pygame.FULLSCREEN) # pygame.RESIZEABLE for windowed mode, pygame.FULLSCREEN for fullscreen, HWSURFACE and DOUBLEBUF are only used if in fullscreen mode
pygame.display.set_caption("MiniFRC Driver Station 2018 V%s" % (str(version)))
Text = pygame.font.SysFont("courier",20)
screen.fill(WHITE)
pygame.display.update()

class Console(): # Console class is the left most section of the screen that displays any messages logged
    def __init__(self):
        self.stack = []             # List of all messages logged
        self.width = 450            # The width of the console window in pixels. The UI is dynamic and so changing this shouldn't break anything
        self.running = False        # If False the window will be updated after every message logged, if True it will only be updated when the render() method is called
        self.NeedUpdate = True      # Variable to track if there has been an update made that needs rendering, improves performance to only render the console when it's updated
        self.scroll = 0
        self.ScrollLimit = 0
        
    def log(self,text="",color=None,display=True): # method used to add a messages to the console
        text=str(text)
        print(text)
        text = text.replace('\t', '    ')
       
        if display: # Display specifies whether to show the message on the UI. It will be printed to the python window regardless
            if(color == None):
                if('[INFO]' in text) or ('[NOTICE]' in text):
                    color = BLUE
                elif('[ERROR]' in text) or ('[WARNING]' in text):
                    color = RED
                elif(text[:1] == '/'):
                    color = BLUE
                    text = text[1:]
                else:
                    color = BLACK

            # If the message is too long to display on one line this will break it into multiple
            t = text.split(" ")
            temp = []
            while True:
                font = pygame.font.SysFont("courier",12)
                while font.size(''.join(t))[0] > self.width:
                    temp.append(t.pop())
                self.stack.append((" ".join(t), color))
                if len(temp) <=0:
                    break
                else:
                    t = temp[::-1]
                    temp = []

            # If not running this re-renders the console
            if not self.running:
                screen.fill(WHITE)
                self.Render()
                pygame.display.update((0,20,self.width,resolution[1]-70))

            # Deals with scrolling and the limiting how far you can scroll in either direction
            self.ScrollLimit = len(self.stack)*14-resolution[1]+70
            if (self.ScrollLimit < 0):
                self.ScrollLimit = 0
            if(self.scroll <= -self.ScrollLimit+14):
                self.scroll = -self.ScrollLimit
            
            self.NeedUpdate = True      # Marks the console in need of re-rendering
        
    def Render(self):       # Method that renders the console and updates that portion of the screen
        if self.NeedUpdate:
            # Rendering text
            for i in range(len(self.stack)):
                rendertext(12,self.stack[i][0],1,i*14 + 20 + self.scroll,self.stack[i][1])

            # Drawing the border
            pygame.draw.rect(screen,WHITE,(0,0,self.width,20))
            pygame.draw.rect(screen,BLACK,(0,20,self.width,resolution[1]-70), 1)

            pygame.display.update((0,20,self.width,resolution[1]-70))   # Updates only the portion of the screen with the console

        self.NeedUpdate = False     # Marks the console not in need of re-rendering

    def clear(self): # Method to clear the console of all messages, I made it and then never used it but it seems potentially useful
        self.stack = []
        self.scroll = 0
        self.render()
      
    def bail(self):     # Method to log all messages in a logfile if something goes wrong
        f = open('LOGFILE.txt',"w")
        for item in self.stack:
            f.write(item[0] + '\n')
        f.close()

class Readout():        # Class that handles all of the instrument readouts
    def __init__(self):
        self.AxisWidth = 500        # Width of the Axes portion. The UI is dynamic and so changing this shouldn't break anything
        self.AxisRange = [console.width + 10, console.width + self.AxisWidth + 10]              # Stores the left and right bounds of the Axes portion
        self.AxisRange.append((self.AxisRange[0]+self.AxisRange[1])/2)              # Adds the midpoint between left and right bound to the list
        
        self.ButtonWidth = 175      # Width of the Buttons portion. The UI is dynamic and so changing this shouldn't break anything
        self.ButtonRange = [self.AxisRange[1] + 10,self.AxisRange[1] + self.ButtonWidth + 10]   # Stores the left and right bounds of the buttions portion
        
        self.HatWidth = 75          # Width of the Hats portion.  The UI is dynamic and so changing this shouldn't break anything
        self.HatRange = [self.ButtonRange[1] + 10,self.ButtonRange[1] + self.HatWidth + 10]     # Stores the left and right bounds of the hats portion
        self.HatRange.insert(1,(self.HatRange[0]+self.HatRange[1])/3)               # Inserts the one third point between left and right bounds
        self.HatRange.insert(2,2*(self.HatRange[0]+self.HatRange[1])/3)             # Inserts the two thirds point between left and right bounds, the HatRange list will be [LeftBound, 1/3 value, 2/3 value, RightBound]

    def Render(self):   # Method that renders the readout
        vertPos = [10,10,10]
        for inp in inputs:   
            if inp.type == 'a':
                inp.Render(vertPos[0])
                vertPos[0] += 50  
            elif inp.type == 'b':
                inp.Render(vertPos[1])
                vertPos[1] += 25 
            elif inp.type == 'h':
                inp.Render(vertPos[2])
                vertPos[2] += self.HatWidth

        # Drawing the Live Package Readout
        pygame.draw.rect(screen, GREEN, (0,resolution[1]-50,resolution[0],50))
        rendertext(20,"Live Package Readout:",10,resolution[1]-50)
        rendertext(20,str(package),10,resolution[1]-30)
        
class Input():
    def __init__(self, name, src, typ, j, i=None):
        self.name = name
        self.source = src
        self.type = typ
        self.j = j
        self.i = i
        self.cache = 0

        inputs.append(self)
        if self.type == 'j':
            controls[('j'+typ, self.j, self.i)] = self
        else:
            controls[self.j] = self
            if self.i != None:
                controls[self.i] = self
            
        self.UpdateCache()
        
    def GetValue(self):
        return self.cache

    def GetPack(self):
        if self.type in ['a', 'b']:
            return round(self.GetValue(), 2)
        elif self.type == 'h':
            return ';'.join(self.GetValue())

    def UpdateCache(self, value=None):
        if value == None:
            if self.type == 'a':
                if self.source == 'j':
                    self.cache = joysticks[self.j].get_axis(self.i)
                else:
                    keys = pygame.key.get_pressed()
                    self.cache = keys[eval('pygame.K_'+self.j)] - keys[eval('pygame.K_'+self.i)]
            elif self.type == 'b':
                if self.source == 'j':
                    pass
                else:
                    keys = pygame.key.get_pressed()
                    self.cache = keys[eval('pygame.K_'+self.j)]
            elif self.type == 'h':
                self.cache = joysticks[self.j].get_hat(self.i)
        else:
            self.cache = value

    def Render(self, vertPos):
        if self.type == 'a':
            rendertext(15, self.name, readout.AxisRange[0], vertPos)
            pygame.draw.line(screen, BLACK,(readout.AxisRange[0], vertPos+20), (readout.AxisRange[1],vertPos+20))
            pygame.draw.line(screen, BLACK,(readout.AxisRange[0], vertPos+25), (readout.AxisRange[0],vertPos+15))
            pygame.draw.line(screen, BLACK,(readout.AxisRange[1], vertPos+25), (readout.AxisRange[1],vertPos+15))       
            pygame.draw.rect(screen, RED,  (readout.AxisRange[2], vertPos+17,  self.GetValue()*readout.AxisWidth/2,7)) # The actual red bar showing current value
            
        elif self.type == 'b':
            if self.cache == 1:
                pygame.draw.rect(screen, RED, (readout.ButtonRange[0], vertPos, readout.ButtonWidth, 25))
            pygame.draw.rect(screen, BLACK, (readout.ButtonRange[0], vertPos, readout.ButtonWidth, 25), 1)
            rendertext(15,self.name, readout.ButtonRange[0]+5, vertPos+5)
            
        elif self.type == 'h':
            hatValue = Hats[i].getValue()
            width = self.HatWidth/3
            pygame.draw.rect(screen,BLACK, (self.HatRange[0],vertPos,self.HatWidth,self.HatWidth),1)
            pygame.draw.rect(screen,RED, (self.HatRange[0]+(hatValue[0]+1)*width,vertPos + (1-hatValue[1])*width,width,width))
            vertPos += self.HatWidth
    
def InitJoysticks():
    # Initialise Joysticks
    console.log("[INFO] %s joystick(s) found: " % (pygame.joystick.get_count()))
    for i in range(pygame.joystick.get_count()):
        joysticks.append(pygame.joystick.Joystick(i))
        joysticks[-1].init()
        console.log('\t'+joysticks[i].get_name())

def ReadConfig():
    global configRaw
    
    # Find config.txt
    try:
        f = open("config.txt","r")
        configRaw = f.read().split('\n')
        f.close()
    except Exception as e:
        console.log('[WARNING] Could not find/open "config.txt"')
        console.log("[WARNING] Error logged as: %s"%(e))
        if testMode == False:
            flag = True
    console.log("[NOTICE] Config file read successfully")
    
def InitConfig():
    global joystickTestMode, testMode, com
    com=''
    
    # Read and interpret config.txt
    console.log("[NOTICE] Starting Setup")
    for line in configRaw:
        if len(line)>0:
            # COM line
            if line.find("COM")!= -1:
                if line.find("test") != -1:
                    testMode = True
                else:
                    com = line.strip('\n')

            # Joysticktest line
            # If the phrase 'joysticktest' is found it will initilise all joystick inputs
            elif line.find("joysticktest") != -1:
                joystickTestMode = True
                console.log("\t[NOTICE] Joystick test mode enabled, all joystick input devices will be initialised")

                for j in range(pygame.joystick.get_count()):
                    for i in range(joysticks[i].Object.get_numaxes()):
                        inputs[('ja',j,i)] = Input('ja',j,i)
                    for i in range(Joysticks[i].Object.get_numbuttons()):
                        inputs[('jb',j,i)] = Input('jb',j,i)
                    for i in range(Joysticks[i].Object.get_numhats()):
                        inputs[('jh',j,i)] = Input('jh',j,i)

            # BAUD line
            elif line.find("BAUD")!=-1:
                baudrate = int(line.split(",")[1])
                console.log("\t[NOTICE] Changed default Baudrate from 9600 to %s"%(str(baudrate)))

            # If we don't find the 'joysticktest' phrase, we initilise only the inputs we're told to
            else:
                if not joystickTestMode:
                    #Format <Name>,Joystick Axis,<joystick>,<input>
                    try:
                        v = line.split(',')
                        w = [i[0].lower() for i in v[1].split(' ')]
                        if (w[0] in ['k','j']) and (w[1] in ['a','b','h']):
                            Input(v[0], w[0], w[1], v[2], v[-1])
                        else:
                            raise Exception('Keyletters not found (second index)')
                    except Exception as e:
                        console.log("\t[ERROR] Config file not formated properly")
                        console.log("\t[ERROR] Initialising axis %s failed" % v[0])
                        traceback.print_exc()
                        return None

def InitConnection():
    global s, com, testMode
    
    # We're done with reading inputs and settings from the config file
    # Now we try to connect to the robot
    if not testMode:
        console.log("\t[INFO] Connecting to robot")
        s = Connect(com,baudrate)
        console.log(s)
    else:
        console.log("\t[INFO] Driver Station in Test Mode, not connecting to robot")    

#Function to connnect to robot
def Connect(default, baudrate):
    try:
        s = serial.Serial(str(default),baudrate) #Try to connect on the provided COM port
        console.log("\t[INFO] Connected to robot on port %s!" % default)
        return s
    except:
        console.log("\t[WARNING] Couldn't connect to robot with specified COM port in config file")

    #If the provided COM port didn't work, just try a bunch of them.
    ports = ['COM'+ str(i) for i in range(50)]
    for port in ports:
        try:
            s = serial.Serial(port,baudrate)
            console.log("\t[INFO] Connected to robot on port %s!" % port)
            return s
        except Exception as e:
            console.log("\t[WARNING] Couldn't connect to robot with port " + port)
            traceback.print_exc()

    #If we've gotten to here we just give up
    console.log()
    console.log("\t[WARNING] Couldn't connect to robot on ANY ports")
    return False

def HandleInputs(event):
    global inputs
    
    try:
        if event.type == pygame.JOYAXISMOTION:
            controls['ja',event.joy, event.axis].UpdateCache(event.value)
        elif event.type == pygame.JOYBUTTONUP:
            controls['jb',event.joy, event.button].UpdateCache(0)
        elif event.type == pygame.JOYBUTTONDOWN:
            controls['jb',event.joy, event.button].UpdateCache(1)
        elif event.type == pygame.JOYHATMOTION:
            controls['jh',event.joy, event.hat].UpdateCache(event.value)

        elif event.type == pygame.KEYDOWN:
            controls[pygame.key.name(event.key)].UpdateCache()
        elif event.type == pygame.KEYUP:
            controls[pygame.key.name(event.key)].UpdateCache()
                
    except Exception as e:
        return None             


def HandleUpkeep(event):
    global console, Exit
    
    if event.type == pygame.KEYDOWN:
        if event.key == 27:
            console.log("[NOTICE] Escape key pressed, shutting down")
            Exit = True  
    elif event.type == pygame.QUIT:
        Exit = True
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

def rendertext(scale,text,x,y,color=BLACK):     # General purpose method for rendering text        
    font = pygame.font.SysFont("courier",scale)
    thing = font.render(text,1,color)
    screen.blit(thing,(x,y))        # Pygame is stupid in that you can't render text directly on an existing surface (screen), you have to create it on a new surface and copy(blit) it over to an existing one



#Setup the console object and print starting messages
console = Console()
console.log("MiniFRC Driver Station 2018 V%s" % (str(version)))
console.log("Booting...")
console.log("This is a very long string for my wrapping system adsfasd a asdf asdf asd asd fas asd asd asd f")

#Setup some variables we have to create at the beginning
flag = False
testMode = False
joystickTestMode = False
joysticks = []      #List of all joysticks connected to computer
inputs = []         #List of Input objects
controls = {}       #Dict used to turn an pygame.event or key press into an Input object

InitJoysticks()
ReadConfig()
InitConfig()
InitConnection()

if not flag:
    Exit = False
    Clock = pygame.time.Clock()
    readout = Readout()
    axisUpdateList = [[] for i in range(10)]
    console.log("[INFO] Driver station is now ACTIVE")
    console.log("[INFO] Press escape to exit driver station")
    console.running = True
    
while (not Exit) and (not flag):
    Clock.tick(60)

    # Event handling
    try:
        events = pygame.event.get()
        #print(events)
        # keys = pygame.key.get_pressed()
        for event in events:        
            HandleInputs(event)
            HandleUpkeep(event)
    except Exception as e:
            console.log("[ERROR] Error raised while handling events")
            traceback.print_exc()
            flag = True

    #Updating Axes
    try:
        for i in range(len(axisUpdateList)):
            for j in range(len(axisUpdateList[i])):
                axisUpdateList[i][j].UpdateCache()
        axisUpdateList.pop(0)
        axisUpdateList.append([])
    except Exception as e:
        console.log("[ERROR] Error raised while updating axis values")
        traceback.print_exc()
        flag = True
       
    # Creating package
    try:
        package = "a"
        for i in inputs:
            package += str(i.GetPack()) + ";"
        package += "z"
    except Exception as e: 
        console.log("[ERROR] Error raised while creating bluetooth package")
        traceback.print_exc()
        flag = True

    # Sending package via Bluetooth
    if testMode == False:
        try:
            s.write(bytes(package,'utf-8'))
        except Exception as e:
            console.log("[ERROR] Error raised while sending bluetooth package")
            traceback.print_exc()
            flag = True

    # Drawing screen
    try:
        screen.fill(WHITE)
        # console.NeedUpdate = True
        console.Render()
        readout.Render()
        rendertext(15,"FPS:" + str(round(1000/Clock.get_time())),0,0)
        pygame.display.update([(console.width,0,resolution[0],resolution[1]),(0,0,console.width,20),(0,resolution[1]-50,console.width,50)])
    except Exception as e:
        console.log("[ERROR] Error raised while drawing the screen")
        traceback.print_exc()
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
        console.Render()
        rendertext(15,"FPS:" + str(1000/Clock.get_time()),0,0,WHITE)
        pygame.display.update()


console.bail()
pygame.quit()
exit()
