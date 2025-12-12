## Quadstick flash drive related functions

import os
import csv
import subprocess

preferences = {}
defaults = {
    'joystick_deflection_minimum':'8',
    'joystick_deflection_maximum':'25',
    'deflection_multiplier_up':'140',
    'deflection_multiplier_down':'130',
    'deflection_multiplier_left':'100',
    'deflection_multiplier_right':'100',
    'joystick_D_Pad_inner':'25',
    'joystick_D_Pad_outer':'80',
    'sip_puff_threshold_soft':'8',
    'sip_puff_threshold':'40',
    'sip_puff_maximum':'70',
    'sip_puff_delay_soft':'1300',
    'sip_puff_delay_hard':'2400',
    'lip_position_minimum':'8',
    'lip_position_maximum':'35',
    'mouse_speed':'100',
    'volume':'40',
    'brightness':'75',
    'digital_out_1':'0',
    'digital_out_2':'0',
    'bluetooth_device_mode':'none',
    'bluetooth_authentication_mode':'4',
    'bluetooth_connection_mode':'pair',
    'bluetooth_remote_address':'',
    'enable_swap_inputs':'0',
    'enable_select_files':'1',
    'watchdog_disable':'0',
    'debug':'1',
    'joystick_dead_zone_shape':'1',
    'anti_dead_zone':'0',
    'enable_auto_zero':'0',
    'mouse_response_curve':'1',
    'enable_usb_comm':'0',
    'TIR_DeadZone':'0',
    'enable_DS3_emulation':'0',
    'enable_usb_a_host':'1',
    'titan_two':'0',
    }

# Local data storage for program data and game profile list


home_directory = os.path.expanduser("~")
settings_file = home_directory + '/QMP_3_settings.repr'
old_settings_file = home_directory + '/quadstick_settings.repr'
settings = dict()

print("INITIALIZE QSFLASH SETTINGS")

def read_repr_file():
    global settings
    #print "read settings: ",
    try:
        f = open(settings_file, 'r')
        settings_string = f.read()
        f.close()
        settings.clear()  # modify existing dictionary
        settings.update(eval(settings_string))
    except Exception as e:
        print("read_repr_file exception: ", repr(e))
        try:
            f = open(old_settings_file, 'r')
            settings_string = f.read()
            f.close()
            settings.clear()  # modify existing dictionary
            settings.update(eval(settings_string))
            return settings
        except:
            print("no old repr file either")
            pass
        settings.clear()
    return settings

def save_repr_file(settings):
    f = open(settings_file, 'w')
    settings_string = repr(settings)
    #print ("save settings: ", settings_string)
    f.write(settings_string)
    f.flush()
    f.close()

QuadStickDrive = None
def find_quadstick_drive(force=None):
    #return None # for testing serial port functions
    global QuadStickDrive
    if force: QuadStickDrive = None  # force new search for drive
    if QuadStickDrive: return QuadStickDrive

    volumes_path = '/Volumes'
    try:
        volumes = os.listdir(volumes_path)

        for volume in volumes:
            if "Quad" in volume and "Stick" in volume:
                QuadStickDrive = volumes_path + '/' + volume + '/'
                print("Found drive ", volume)
                return QuadStickDrive
    except:
        print("Failed to get drive")

    return None

def load_preferences_file(mainWindow):
    global preferences
    d = find_quadstick_drive()
    if d is None:
        if mainWindow.microterm:
            #mainWindow.text_ctrl_messages.AppendText( "Searching for Bluetooth or serial connection... ")
            # try a serial connection if bluetooth ssp enabled
            #if preferences.get("bluetooth_device_mode") == "ssp":
            mt = mainWindow.microterm
            if mt.serial:
                prefs_file = mt.read_qs_file("prefs.csv")
                print("serial port preferences file contents:\n\n", len(prefs_file), repr(prefs_file))
                csvfile = prefs_file.split("\n")
                if len(csvfile) > 3: # at least three lines long
                    while csvfile[0].find("QuadStick Configuration") < 0:
                        csvfile.pop(0)
                if len(csvfile) > 3:
                    reader = csv.reader(csvfile, delimiter=',')
                    row_count = 0
                    for row in reader:
                        #print ', '.join(row)
                        # skip header section
                        if row_count > 3 and row and row[0]:
                            if row[0] == "**END OF FILE**":
                                break
                            if row[1]:
                                preferences[row[0]] = row[1]
                                print("assign ", row[0], " with ", row[1])
                        row_count += 1
                    return preferences
        #mainWindow.text_ctrl_messages.AppendText( "Serial connection not found.")
        return None
    pathname = d + 'prefs.csv'
    preferences.clear()
    preferences.update(defaults.copy()) # start out with defaults for any missing items
    try:
        with open(pathname) as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            row_count = 0
            for row in reader:
                #print ', '.join(row)
                # skip header section
                if row_count > 3 and row and row[0] and row[1]:
                    preferences[row[0]] = row[1]
                row_count += 1
    except Exception as e:
        print('quadstick drive found but unable to read prefs.csv file')
        print(repr(e))
        return None
    #print repr(preferences)
    return preferences

CSV_HEADER = """QuadStick Configuration,Version 1.1
Preferences,,,,
prefs.csv,,,,
Preference,Value,Units,Description,
"""

def save_preferences_file(preferences):
    global QuadStickDrive
    QuadStickDrive = None # force refresh of quadstick drive
    d = find_quadstick_drive()
    if d is None:
        print("quadstick flash drive not found.  Try serial")
        # try a serial connection if bluetooth ssp enabled
        from microterm import microterm  # late import because microterm imports from this module
        mt = microterm()
        if mt.serial:
            lines = CSV_HEADER.splitlines()
            keys = list(preferences.keys())
            keys.sort()
            for key in keys:
                value = preferences[key]
                lines.append(key + "," + str(value) + ",,")
            for line in lines:
                print(line)
            resp = mt.write_qs_file("prefs.csv", lines)
            print("serial port preferences file bytes written: ", resp)
            if resp.find("bytes written") > -1:
                return True
        return None
    pathname = d + 'prefs.csv'
    try:
        os.remove(pathname)
    except:
        print('prefs.csv not found to delete')
    with open(pathname, 'w', newline='\r\n') as csvfile:
        # write header
        csvfile.write(CSV_HEADER)
        keys = list(preferences.keys())
        keys.sort()
        for key in keys:
            value = preferences[key]
            csvfile.write(key + ',' + str(value) + ',,\n')
            # cannot use percent sign in wxGlade source files
        csvfile.flush()
        os.fsync(csvfile.fileno())
    return True

def save_csv_file(name, text):
    d = find_quadstick_drive()
    if d is None:
        print("quadstick flash drive not found")
        return None
    pathname = d + name
    try:
        os.remove(pathname)
    except:
        print('file not found to delete')
    with open(pathname, 'wb', 0) as csvfile:
        # write header
        csvfile.write(text)
        csvfile.flush()
        os.fsync(csvfile.fileno())
    return True

def cleanup_macos_dot_files(drive_path):
    # remove mac ._ files from the drive
    if not drive_path:
        return
    try:
        for f in os.listdir(drive_path):
            if f.startswith('._'):
                os.remove(drive_path + f)
    except:
        pass

def list_quadstick_csv_files(mainWindow):  # quadstick flash drive
    mainWindow._csv_files = []
    d = find_quadstick_drive()
    if d is None:
        print("list_quadstick_csv_files, quadstick flash drive not found")
        if mainWindow.microterm:
            return mainWindow.microterm.list_files()
        return []
    print('quadstick drive letter ', repr(d))
    cleanup_macos_dot_files(d)
    file_names = os.listdir(d)
    csv_files = [n for n in file_names if n.lower().endswith('.csv') and not n.startswith('._')]
    file_list = []
    #move default and prefs to front
    if "prefs.csv" in csv_files:
        file_list.append("prefs.csv")
        csv_files.remove("prefs.csv")
    if "default.csv" in csv_files:
        file_list.append("default.csv")
        csv_files.remove("default.csv")
    csv_files = sorted(csv_files, key=lambda s: s.lower())
    file_list.extend(csv_files)
    # read first line in each csv file and get spreadsheet id and name
    answer = []
    for name in file_list:
        spreadsheet_name = ""
        id = ""
        try:
            pathname = d + name
            print(repr(pathname))
            with open(pathname) as csvfile:
                firstline = csvfile.readline()
            parts = firstline.split(",")
            print(repr(parts))
            if parts[0] == "QuadStick Configuration":
                if parts[1] == "Version 1.4":
                    id = (parts[2].split("spreadsheets/d/")[1]).split("/")[0]
                    spreadsheet_name = parts[3]
                elif parts[1] == "Version 1.5":
                    id = parts[2]
                    spreadsheet_name = parts[3]
        except Exception as e:
            print("exception while reading details from csv files")
            print(repr(e))
        t = (name, id, spreadsheet_name)
        answer.append(t)
        print("CSV file: ", repr(t))
        mainWindow._csv_files.append({"id":id, "name":spreadsheet_name,"csv_name":name})
    return answer

def quadstick_drive_serial_number(mainWindow):
    # read boot sector from quadstick and pull out build number from serial number
    d = find_quadstick_drive()
    if d is None:
        print("quadstick flash drive not found")
        if mainWindow.microterm:
            #mainWindow.text_ctrl_messages.AppendText( "Searching for Bluetooth or serial connection... ")
            # try a serial connection if bluetooth ssp enabled
            #if preferences.get("bluetooth_device_mode") == "ssp":
            mt = mainWindow.microterm
            if mt.serial:
                build = mt.get_build()
                print("build number is: ", build)
                if build:
                    return int(build.strip())
        return None

    try:
        result = subprocess.run(['diskutil', 'info', "/" + d.split("/")[1]], capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines():
            if 'Device Node' in line:
                device = line.split(':')[1].strip()
    except subprocess.CalledProcessError:
        print(f"Failed to get device node for {d}.")

    try:
        with open(device, 'rb') as f:  # Open the device file in binary read mode
            boot_sector = f.read(512)  # Read the first 512 bytes
    except Exception:
        print('I don\'t know how this highfallutin boot sector stuff works. but it\'s just for the serial right?')
        return 601

    build = boot_sector[40] * 256 + boot_sector[39] #drive.read(2) # serial number
    answer = build #ord(build[0]) + 256 * ord(build[1])
    if answer == 30867: #old firmware
        answer = 601
    return answer
