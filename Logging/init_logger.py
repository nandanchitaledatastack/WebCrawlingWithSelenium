import logging
import os
from datetime import datetime

def init_logger():
    log_file_name = f"log_{datetime.now().strftime('_%y_%m_%d')}.log"
    try:
        root = os.path.abspath(os.curdir)
        logdir = os.path.join(root,"Log")
        if not os.path.exists(logdir):
            os.mkdir(logdir)
            
        log_file = os.path.join(logdir, log_file_name)
        
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter and add it to the file handler
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add the file handler to the logger
        logger.addHandler(file_handler)
        
        return logger
    except Exception as e:
        with open(log_file_name, "a") as logFile:
            logFile.write(f"Error in init_logger > {e}")
        
        raise Exception(e)