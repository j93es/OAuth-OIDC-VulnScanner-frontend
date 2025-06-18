# read json file .sensitive.json

import json
import os

def GetSensitiveData():
    """
    Reads sensitive data from a .sensitive.json file in the current directory.
    
    Returns:
        dict: A dictionary containing the sensitive data.
    """
    file_path = os.path.join(os.getcwd(), '.sensitive.json')
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    with open(file_path, 'r') as file:
        sensitive_data = json.load(file)
    
    return sensitive_data