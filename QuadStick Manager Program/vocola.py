## Vocola related functions
from win32com.shell import shell, shellcon
import os
import threading
import copy
from microterm import microterm
from qsflash import preferences

# Vocola Command Listener

UDP_IP = "127.0.0.1" #"0.0.0.0" #
UDP_PORT = 47807


USERPROFILE = os.environ['USERPROFILE']
PERSONAL_FOLDER = shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, None, 0)
VocolaFolder = "\\Natlink\\Vocola\\"
VocolaPath = PERSONAL_FOLDER + VocolaFolder

def list_voice_files():
    vch_files = list()
    try:
        for (paths, dirs, file_names) in os.walk(VocolaPath):
            break #first level directory only is what we want
        vcl_files = [n for n in file_names if ((n.lower().find(".vcl") > 0) and (n.find("_") != 0))] # only want .vch .vcl
        vch_files = [n for n in file_names if ((n.lower().find(".vch") > 0) and (n.find("_") != 0))] # only want .vch .vcl and not _special files
        vcl_files = sorted(vcl_files, key=lambda s: s.lower())
        vch_files = sorted(vch_files, key=lambda s: s.lower())
        vch_files.append("--------")
        vch_files.extend(vcl_files)
    except Exception as e:
        print(repr(e))
    return vch_files

def save_voice_file(name, text):
    pathname = VocolaPath + name
    try:
        os.remove(pathname)
    except:
        print('file not found to delete')
    with open(pathname, 'wb', 0) as f:
        # write header
        f.write(text)
        f.flush()

    if ".vch" in name:
        generate_includes_vch_file()

VCH_file_words = {}

def generate_includes_vch_file():
    # create "_includes.vch" file with all the .vch files
    for (paths, dirs, file_names) in os.walk(VocolaPath):
        break #first level directory only is what we want
    vch_files = [n for n in file_names if ((n.find(".vch") > 0) and (n.find("_") != 0))] # only want .vch .vcl
    vch_files.sort()
    lines = []
    for fn in vch_files:
        lines.append("include " + fn + ";\n")
    with open(VocolaPath + "_includes.tmp", "w") as f:
        f.write("# File automatically generated by QuadStick configuration manager\n\n")
        for line in lines:
            f.write(line)
        f.flush()
    try:
        os.remove(VocolaPath + "_includes.vch")
    except:
        print("_includes.vch did not exist.  Must be first time.")
    try:
        # remove any left over includes.vch
        os.remove(VocolaPath + "includes.vch")
    except:
        pass
    os.rename(VocolaPath + "_includes.tmp", VocolaPath + "_includes.vch")

    # scan vch files and put their game specific words in a dictionary keyed by title
    # title is line terminated with :, phrases are everything left of an = sign
    common_phrases = ["load default",]
    global VCH_file_words
    VCH_file_words = {'_common_phrases':common_phrases,}
    for fn in vch_files:
        try:
            with open(VocolaPath + "\\" + fn, "r") as f:
                print("vch file: ", fn)
                phrases = []
                title = ""
                for line in f.readlines():
                    line = line.strip()
                    if line.find("#") == 0: continue # skip comments
                    if line.find(":") > 0:
                        title, scrap = line.split(":")
                    if line.find("=") > 0:
                        phrase, scrap = line.split("=")
                        if title: # place in title specific list
                            phrases.append(phrase.strip())
                        else:
                            common_phrases.append(phrase.strip())
                if title:
                    VCH_file_words[title] = phrases
        except Exception as e:
            print("generate_includes_vch_file exception: ", repr(e))
    #print "vocola game specific phrases: ", repr(VCH_file_words)

# Bring window to front
import win32gui
import win32con
def BringToFront(HWND):
    print("BringToFront")
    win32gui.ShowWindow(HWND, win32con.SW_RESTORE)
    win32gui.SetWindowPos(HWND,win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)  
    win32gui.SetWindowPos(HWND,win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)  
    win32gui.SetWindowPos(HWND,win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_SHOWWINDOW + win32con.SWP_NOMOVE + win32con.SWP_NOSIZE)            


# The Voice control portion works by listening to a UDP socket for command strings
# coming from a Vocola Extension.  When a string is received, it is sent via
# a serial port to the QuadStick.  Any response from the QuadStick is displayed
# on the Transcript text pane in the QMP window

class VocolaListenerThread(threading.Thread):
    def __init__(self, mainWindow, sock, qs):
        super(VocolaListenerThread, self).__init__()
        self.daemon = True
        self._mainWindow = mainWindow
        self._transcript = mainWindow.voice_transcript # text pane on voice tab
        self._messages = mainWindow.text_ctrl_messages # text pane in lower left corner
        self.term = None
        self._alive = True
        self.sock = sock
        self.qs = qs

    def run(self):
        try:
            while self._alive:
                data, addr = self.sock.recvfrom(1024) # buffer size is 1024 bytes, block waiting for vocola
                print("Vocola thread received: ", str(data))
                # check for special command strings
                try:
                    data = data.decode()
                    if data.find("BRING TO FRONT") >= 0:
                        self._mainWindow.Raise()
                        BringToFront(self._mainWindow.GetHandle())
                        self._mainWindow.Raise()
                        continue
                    if data.find("LOAD: ") >= 0:
                        qmp_url = data.split(": ")[1]
                        self._mainWindow.Raise()
                        BringToFront(self._mainWindow.GetHandle())
                        self._mainWindow.CallAfter(self._mainWindow.csv_files_dropped, None, None, qmp_url)
                        self._mainWindow.Raise()
                        continue
                except Exception as e:
                    print("Vocola thread: ", repr(e))
                if self._transcript:
                    self._mainWindow.CallAfter(self._transcript.AppendText, *(data + '\r\n',))
                else:
                    print("received message:", data)
                #self._mainWindow.Raise()
                if self.qs and int(preferences.get('enable_usb_comm', 0)):  # since quadstick active, send commands via USB
                    self.qs.sendline(copy.copy(data))
                    continue
                if self.term is None:
                    self.term = microterm(self._mainWindow)
                if self.term.serial:
                    #print repr(data)
                    resp = self.term.sendline(copy.copy(data))
                    if resp:
                        self._mainWindow.CallAfter(self._transcript.AppendText, resp)
                else:
                    self.term = None # if no serial port, force rescan for port on next command
                    self._mainWindow.CallAfter(self._messages.AppendText, "No serial connection to QuadStick found for commands.\n")
        except:
            self._alive = False
            print ("vocola thread exception.  Stopping\n")
                
    def kill(self):
        self._alive = False
        try:
            if self.sock:
                self.sock.close()
        except:
            pass
        try:
            if self.term:
                self.term.close()
        except:
            pass

            
CommonVoiceCommands = """playstation buttons names: 

cross | circle | square | triangle
left one, two, three | right one, two, three

xbox button names:

alpha | action | bravo | yankee | xray
left button, trigger, stick | right button, trigger, stick

D-Pad: north | south | east | west
       north east | south east | south west | north west

home | select | start | share | pause

Button modifiers [optional parameter]:

<button name> [<pct>] [for <sec> seconds]
[hold | release | toggle] <button name>
<button name> [on | off | toggle]
[repeat] <button name> [# times]  # default to 10

# Analog sticks

Left Stick: player | move
Right Stick:  look | camera | view

Direction: up | down | left | right

<stick> <direction>
<stick> <direction> [<pct>] [for <sec> seconds]

# Quadstick operational  control

Reset | stop  # releases all buttons
Mode <mode #>
reboot quad stick                         

# Preference changing commands

display preferences
calibrate quad stick
use USB [(A=1 | B=0)]
set mouse speed <pct>
set mouse curve 0..2
set volume <pct>
set brightness <pct>
set digital out (1 | 2) (on | off)    # control digital outputs

# control sip/puff thresholds
set sip puff soft (2..20)
set sip puff (30..90)
set sip puff maximum (50..100)
set sip puff delay (1..20) hundred

# control joystick calibration
joy stick deflection minimum (1..20)
joy stick deflection maximum (10..100)
D pad inner (1..100)
D pad outer (20..100)
joy stick dead zone (circle | square)
anti dead zone (0..50)
"""

def RestartDragon():
    import subprocess
    subprocess.check_call('taskkill /im natspeak.exe /f')
    sleep(3.0)
    subprocess.Popen(["C:\\Program Files (x86)\\Nuance\\NaturallySpeaking13\\Program\\natspeak.exe", "/user", "Fred IV (v13)"]).pid
