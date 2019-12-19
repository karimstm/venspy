from pathlib import Path
import win32com.client
from threading import Timer
import subprocess
import psutil
import json
import os


class Simulator():

    def __init__(self, vensim, model, runname="run", handlerFile="vinsimHandler"):
        self.__script = F"""
:SCREEN Simulator
COMMAND,"",0,0,0,0,,,SPECIAL>NOINTERACTION|0
COMMAND,"",0,0,0,0,,,SPECIAL>LOADMODEL|{model}
COMMAND,"",0,0,0,0,,,SIMULATE>RUNNAME|{runname}
COMMAND,"",0,0,0,0,,,MENU>RUN|O
COMMAND,"",0,0,0,0,,,MENU>VDF2DAT|{runname}.vdf|{runname}.dat
COMMAND,"",0,0,0,0,,,SPECIAL>EXIT1
COMMAND,"",0,0,0,0,,,MENU>EXIT
"""
        self.vensim = vensim
        self.runname = runname
        self.handlerFile = handlerFile
        self.execute()
        self.dat2json()
        self.clear()

    def dat2json(self):
        data = Path(F"{self.runname}.dat").read_text()
        lines = data.split("\n")
        self.results = {}
        current = None
        for line in lines:
            if not line:
                continue
            keyVal = line.split("\t")
            if len(keyVal) is not 2:
                current = line.encode('ISO-8859-1').decode('utf-8')
                self.results[current] = {}
            elif len(keyVal) is 2:
                self.results[current][keyVal[0]] = float(keyVal[1])

    def execute(self):
        Path(F"{self.handlerFile}.VCD").write_text(self.__script)
        command = F"{self.vensim} {self.handlerFile}.VCD"
        subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).wait()
        #Timer(40, proc.kill)

    def clear(self):
        os.remove(F"{self.runname}.dat")
        os.remove(F"{self.runname}.vdfx")
        os.remove(F"{self.handlerFile}.VCD")
        PROCNAME = "EXCEL.EXE"
        for proc in psutil.process_iter():
            if proc.name() == PROCNAME:
                proc.kill()
