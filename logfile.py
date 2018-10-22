# https://docs.python.org/2.6/library/logging.html
# Need to make sure we have file-write permissions for this to work

import logging

LOG_FILENAME = 'EDStesting_logfile.txt'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)

#Loggers
logger = logging.getLogger("AutomatedTestSystem")
logger.setLevel(logging.DEBUG)
#Handlers
logfileFormat = logging.FileHandler() #Need to check this is correct usage of .FileHandler()
errorlogfileFormat = logging.FileHandler()
#Formatters
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logfileFormat.setFormattter(formatter)
logger.addHandler(logfileFormat)

#limit file size of logfile if desired (?)

# The "application" code. The lines below will not remain in this file, but will instead be included in the other files comprising this automated test system.
# The format of each line in the logfile will look like:
'2018-10-20 11:00:00,000 - AutomatedTestSystem - INFO - Config file successfully loaded'

logger.info("Config file successfully loaded")
logger.info("USB is correctly mounted")
logger.info("Solar Cell 1 presence verified")
logger.info("Solar Cell 2 presence verified")
logger.info("Solar Cell 3 presence verified")
logger.info("Solar Cell 4 presence verified")
logger.info("Solar Cell 5 presence verified")
logger.info("Solar Cell 6 presence verified")
logger.info("Solar Cell 7 presence verified")
logger.info("Solar Cell 8 presence verified")
logger.info("Weather sensor presence verified")
logger.info("Real-time clock presence verified")
logger.info("Logfile presence verified")
logger.info("Weather check completed, data stored in USB")
logger.info("Cloud coverage check completed")
logger.info("Weather sensor presence verified")
logger.info("Solar Cell 1 Isc measured and recorded")
logger.info("Solar Cell 2 Isc measured and recorded")
logger.info("Solar Cell 3 Isc measured and recorded")
logger.info("Solar Cell 4 Isc measured and recorded")
logger.info("Solar Cell 5 Isc measured and recorded")
logger.info("Solar Cell 6 Isc measured and recorded")
logger.info("Solar Cell 7 Isc measured and recorded")
logger.info("Solar Cell 8 Isc measured and recorded")
logger.info("Solar Cell 1 EDS activated")
logger.info("Solar Cell 1 EDS deactivated")
logger.info("Solar Cell 2 EDS activated")
logger.info("Solar Cell 2 EDS deactivated")
logger.info("Solar Cell 3 EDS activated")
logger.info("Solar Cell 3 EDS deactivated")
logger.info("Data written successfully to USB")

logger.warning("Config file not found, default config file generated")
logger.warning("Logfile not found, new logfile generated")

logger.error("Weather sensor presence not found")
logger.error("Real-time clock presence not found")
logger.error("USB name described in config file not found")
logger.error("USB presence not found")
logger.error("Shell process malfunction is USB mount check")

logger.critical("Solar Cell 1 presence not found")
logger.critical("Solar Cell 2 presence not found")
logger.critical("Solar Cell 3 presence not found")
logger.critical("Solar Cell 4 presence not found")
logger.critical("Solar Cell 5 presence not found")
logger.critical("Solar Cell 6 presence not found")
logger.critical("Solar Cell 7 presence not found")
logger.critical("Solar Cell 8 presence not found")
