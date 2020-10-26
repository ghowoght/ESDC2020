from ast import walk
import os
from os.path import abspath, basename


def convert(dir = "."):
    for root,dirs,files in os.walk(dir):
        for file in files:
            if (os.path.splitext(file)[-1]!=".qrc"):
                continue
            # uiFile=os.path.realpath(root)+"/"+file
            qrcFile=root+"/"+file
            pyFile=os.path.splitext(qrcFile)[0]+"_rc.py"
            print("[FILE]",file,"\t",qrcFile)

            cmd= "pyrcc5 {qrcFile} -o {pyFile}".format(
            pyFile=pyFile, qrcFile=qrcFile)
            print("[RUN]",cmd)
            os.system(cmd)
            print()

if __name__ == "__main__":
    dir = ".."
    convert(dir = dir)
