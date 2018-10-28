import subprocess
import os
import logfile as lgf

'''
Reboot Master class
Functionality:
1) Gets command for restarting RPi
2) Logs error and reset in log file
3) Sets flags for automatic startup (without needed GUI interfacing) when restarted
4) Runs restart sequence to reboot RPi and begin code after reset
'''

class RebootMaster:
    def __init__(self):
        self.is_reboot_ready = False

    def set_reboot_ready(self):
        self.is_reboot_ready = True

    def write_reboot_log(self):
        lgf.logger.critical("Critical error found. Resetting Raspberry Pi")

    def run_reboot_sequence(self, static_master):
        if self.is_reboot_ready is True:
            self.set_config_flag(static_master)
            static_master.load_config()
            if static_master.get_config()['rebootFlag'] is True:
                # write reboot to log file
                self.write_reboot_log()
                # reboot system if flags passed
                os.system("sudo shutdown r- now")

    def set_config_flag(self, static_class):
        # sets reboot flag to true in static class
        static_class.write_reboot_flag()


