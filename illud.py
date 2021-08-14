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

    def drawStatusLine(self, left, top, width):
        mode = '{} - {}'.format(self.message, self.mode).ljust(width - 1)
        self.screen.addstr(top, left, mode, curses.A_BOLD)
        position = '{}:{}'.format(self.row + 1, self.col + 1)
        self.screen.addstr(top, left + width - 1 - len(position),
                           position, curses.A_BOLD)

    def drawText(self, left, top, width, height):
        highestLineNum = len(self.buf.getLines())
        gutterWidth = max(3, len(str(highestLineNum))) + 1
        lineWidth = width - gutterWidth
        cursorY, cursorX = None, None

        self.scrollTo(self.row, lineWidth, height)

        lineNums = range(self.scrollTop, highestLineNum)
        currentY = top
        trailingChar = '.'

        for lineNum in lineNums:
            remainingRows = top + height - currentY

            if(remainingRows == 0):
                break
            wrappedLines = self.getWrappedLines(lineNum, lineWidth)
            if(len(wrappedLines) > remainingRows):
                trailing_char = '>'
                break
            
            if(lineNum == self.row):
                lines = self.getWrappedLines(lineNum, lineWidth,
                                                convertNonPrinting=False)
                realCol = len(self.convertNonPrinting(
                    ''.join(lines)[:self.col])
                )
                cursorY = curY + realCol / lineWidth
                cursorX = left + gutterWidth + realCol % lineWidth
                
            for n, wrappedLine in enumerate(wrappedLines):
                if(n == 0):
                    gutter = '{} '.format(lineNum + 1).rjust(gutterWidth)
                else:
                    gutter = ' ' * gutterWidth
                self.screen.addstr(currentY, left, gutter, curses.A_REVERSE)
                self.screen.addstr(currentY, left + len(gutter), wrappedLine)
                currentY += 1
                
        for currentY in range(currentY, top + height):
            gutter = trailingChar.ljust(gutterWidth)
            self.screen.addstr(currentY, left, gutter)

        assert cursorX != None and cursorY != None
        self.screen.move(cursorY + 0, cursorX + 0)

    def draw(self):
        self.screen.erase()
        height = self.screen.getmaxyx()[0]
        width = self.screen.getmaxyx()[1]
        self.drawStatusLine(0, height - 1, width)
        self.drawText(0, 0, width, height - 1)
        self.screen.refresh()

