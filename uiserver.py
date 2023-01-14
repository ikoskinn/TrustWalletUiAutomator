import configparser
import os
import re
import subprocess
import time

import uiautomator2
import uiautomator2 as u2

import Classes
import PlayerClasses
import TBot
import TrustWalletMethods
import sqlite3
import sqliteManager


#d = u2.connect("127.0.0.1:5555")
#print(d.dump_hierarchy())
#exit()
while True:
    try:
        p = PlayerClasses.PManager('BS4')
        pass
    except Exception as e:
        print(e)

