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

