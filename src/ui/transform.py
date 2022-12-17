import os
import os.path

_dir = './'


def listUiFile():
    lst = []
    files = os.listdir(_dir)
    for filename in files:
        if os.path.splitext(filename)[1] == '.ui':
            lst.append(filename)
    return lst


def transPyFile(filename):
    return os.path.splitext(filename)[0] + '.py'


def runMain():
    lst = listUiFile()
    for uifile in lst:
        pyfile = transPyFile(uifile)
        cmd = 'pyuic5 -o {pyfile} {uifile}'.format(pyfile=pyfile, uifile=uifile)
        os.system(cmd)


if __name__ == '__main__':
    runMain()
