from ast import walk
import os
from os.path import abspath, basename


def convert(dir = "."):
    for root,dirs,files in os.walk(dir):
        for file in files:
            if (os.path.splitext(file)[-1]!=".ui"):
                continue
            # uiFile=os.path.realpath(root)+"/"+file
            uiFile=root+"/"+file
            pyFile=os.path.splitext(uiFile)[0]+".py"
            print("[FILE]",file,"\t",uiFile)

            cmd= "pyuic5 -o {pyFile} {uiFile}".format(
            pyFile=pyFile, uiFile=uiFile)
            print("[RUN]",cmd)
            os.system(cmd)
            print()

if __name__ == "__main__":
    dir = ".."
    convert(dir=dir)
