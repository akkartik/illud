import curses
import os
from sys import argv
from contextlib import contextmanager

class Buffer(object):
    def __init__(self, text = ''):
        self.lines = text.split('\n')

    def getLines(self):
        return list(self.lines)

    def checkPoint(self, row, col):
        if(row < 0 or row > len(self.lines) - 1):
            print("Row exceeded the limit: '{}'".format(row))

        currentRow = self.lines[row]
        
        if(col < 0 or col > len(currentRow)):
            print("Column exceeded the limit: '{}'".format(col))

    def setText(self, row1, col1, row2, col2, text):
        self.checkPoint(row1, col1)
        self.checkPoint(row2, col2)

        line = self.lines[row1][:col1] + text + self.lines[row2][col2:]
        self.lines[row1:row2+1] = line.split('\n')

class IlludGUI(object):
    def __init__(self, stdscr, filename):
        self.screen = stdscr
        
        text = ''
        
        if(filename != None and os.path.isfile(filename)):
            with open(filename) as f:
                text = f.read()
        self.fileName = filename
        self.buf = Buffer(text)
        self.row = 0
        self.col = 0
        self.scrollTop = 0
        self.mode = 'Normal'
        self.message = 'Illud'
        self.exitEditor = False

    def drawGutter(self, numStart, numRows, lastLineNum):
        lineNums = range(numStart, numStart + numRows)

        assert len(lineNums) == numRows

        gutterWidth = max(3, len(str(lastLineNum))) + 1
        
        for y, lineNum in enumerate(lineNums):
            if lineNum > lastLineNum:
                text = '.'.ljust(gutterWidth)
            else:
                text = '{} '.format(lineNum).rjust(gutterWidth)
            self.screen.addstr(y, 0, text, curses.A_REVERSE)
        return gutterWidth

