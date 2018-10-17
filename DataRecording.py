import os
import subprocess

# necessary constants
USB_PATH = "/media/pi"


'''
USB Master Class:
Functionality:
1) Checks if USB is mounted
2) If mounted, gets USB name
3) If USB name found, construct file path for saving files to USB
'''


class USBMaster:
    def __init__(self):
        self.name = None
        self.USB_file_path = None
        self.is_mounted = False

    def reset(self):
        # resets parameters if needed
        self.__init__()

    def check_if_mounted(self):
        # check if USB mounted
        try:
            if not subprocess.call("grep -qs '/mnt/usbdrive' /proc/mounts", shell=True):
                self.is_mounted = True

            else:
                self.reset()
                print("USB not mounted! Please insert USB.")

        except RuntimeError:
            self.reset()
            print("ERROR: Shell process malfunction!")

    def set_USB_name(self):
        # gets USB name if mounted
        if self.is_mounted:
            try:
                proc = subprocess.Popen("ls "+USB_PATH, shell=True, preexec_fn=os.setsid, stdout=subprocess.PIPE)
                self.name = proc.stdout.readline()

            except RuntimeError:
                self.reset()
                print("ERROR: USB name not found!")

    def set_USB_file_path(self):
        # gets USB file path for saving if USB name found
        if self.name is not None:
            self.USB_file_path = USB_PATH+"/"+self.name
            
    def process_sequence(self):
        # runs through necessary sequence for single method call
        self.check_if_mounted()
        self.set_USB_name()
        self.set_USB_file_path()

    def get_USB_file_path(self):
        # outputs USB file path
        return self.USB_file_path




