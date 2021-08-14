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

    @staticmethod
    def convertNonPrinting(text):
        res = []
        for char in text:
            i = ord(char)
            if(char == '\t'):
                res.append('->  ')
            elif(i < 32 or i > 126):
                res.append('<{}>'.format(hex(i)[2:]))
            else:
                res.append(char)
        return ''.join(res)
    
    def getWrappedLines(self, lineNum, width, convertNonPrinting=True):
        def wrapText(text, width):
            if(text == ''):
                yield ''
            else:
                for i in xrange(0, len(text), width):
                    yield text[i:i + width]

        assert lineNum >= 0, 'lineNum must be greater than 0.'
        
        line = self.buf.getLines()[lineNum]
        
        if(convertNonPrinting):
            line = self.convertNonPrinting(line)
        return list(wrapText(line, width))

    def getNumWrappedLines(self, lineNum, width):
        return len(self.getWrappedLines(lineNum, width))

    def scrollBottomToTop(self, bottom, width, height):
        def verify(top):
            rows = [list(self.getWrappedLines(n, width))
                    for n in range(top, bottom + 1)]
            numRows = sum(len(r) for r in rows)

            assert top <= bottom, ('top line {} may not be below bottom {}'
                                   .format(top, bottom))

            assert numRows <= height, (
                '{} {} {} {} {}'
                .format(numRows, top, bottom, height, rows))

        top, nextTop = bottom, bottom
        
        distance = self.getNumWrappedLines(bottom, width)

        while nextTop >= 0 and distance <= height:
            top = nextTop
            nextTop -= 1
            distance += self.getNumWrappedLines(max(0, nextTop), width)

        verify(top)
        return top

    def scrollTo(self, lineNum, width, rowHeight):
        lowestTop = self.scrollBottomToTop(lineNum, width, rowHeight)

        if(lineNum < self.scrollTop):
            self.scrollTop = lineNum
        elif(self.scrollTop < lowestTop):
            self.scrollTop = lowestTop
    
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

    def handleNormalMode(self, char):
        if(char == ord('q')): # quit
            self.exitEditor = True
        elif(char == ord('k')): # down
            self.row += 1
        elif(char == ord('i')): # up
            self.row -= 1
        elif(char == ord('j')): # left
            self.col -= 1
        elif(char == ord('l')): # right
            self.col += 1
        elif(char == ord('s')): # move to beginning of line
            self.col = 0
        elif(char == ord('e')): # move to end of line
            currentLineLen = len(self.buf.getLines()[self.row])
            self.col = currentLineLen - 1
        elif(char == ord('x')): # delete a character
            self.buf.setText(self.row, self.col, self.row,
                                self.col + 1, '')
        elif(char == ord('i')): # enter insert mode
            self.mode = "Insert"
        elif(char == ord('a')): # enter insert mode after cursor
            self.mode = "Insert"
            self.col += 1
        elif(char == ord('w')): # write file
            if(self.fileName == None):
                self.message = "Can\'t write file without filename."
            else:
                try:
                    with open(self.fileName, 'w') as f:
                        f.write('\n'.join(self.buf.getLines()))
                except IOError as e:
                    self.message = ("Failed to write file \'{}\': {}"
                                     .format(self.fileName, e))
        else:
            self.message = ''

    def handleInsertMode(self, char):
        if(char == 27): #ESC
            if(self.mode == 'Insert'):
                self.col -= 1
            self.mode = "Normal"
        elif(char == 127): # Backspace
            if(self.col == 0 and self.row == 0):
                pass
            
            elif(self.col == 0):
                prevLine = self.buf.getLines()[self.row - 1]
                cur_line = self.buf.getLines()[self.row]
                self.buf.setText(self.row - 1, 0, self.row,
                                    len(curLine), prevLine + curLine)
                self.col = len(prevLine)
                self.row -= 1
            else:
                self.buf.setText(self.row, self.col - 1, self.row,
                                    self.col, '')
                self.col -= 1
        else:
            self.message = ('inserted {} at row {} col {}'
                             .format(char, self.row, self.col))
            self.buf.setText(self.row, self.col, self.row,
                                self.col, chr(char))
            if(chr(char) == '\n'):
                self.row += 1
                self.col = 0
            else:
                self.col += 1
