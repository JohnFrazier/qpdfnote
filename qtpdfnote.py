#!/usr/bin/python
import sys
from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QEvent
import popplerqt4
import citations

usage = """
Demo to load a PDF and display the first page.

Usage:

    qtpdfnote.py file.pdf

"""

class Overlay(QtGui.QWidget):
    def __init__(self, parent = None):
        QtGui.QTextEdit.__init__(self,parent)
        palette = QtGui.QPalette(self.palette())
        palette.setColor(palette.Base, Qt.transparent)
        self.setPalette(palette)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        self.drawFigures(painter)
        painter.end()

    def drawFigures(self, painter):
        pass

class OverlayEdit(Overlay):
    def __init__(self, parent = None):
        super(OverlayEdit, self).__init__(parent)
        self.figures=[]

    def drawFigures(self, painter):
        fgcolor = QtGui.QColor(0,0,0,122)
        fgcolor.setNamedColor("yellow")
        fgcolor.setAlpha(127)
        edgecolor = QtGui.QColor(0,0,0,122)
        painter.setPen(edgecolor)
        painter.setBrush(fgcolor)
        for a in self.figures:
            painter.drawRect(a)

class Pdf():
    def __init__(self, filename):
        self.doc = popplerqt4.Poppler.Document.load(filename)
        self.doc.setRenderHint(popplerqt4.Poppler.Document.Antialiasing)
        self.doc.setRenderHint(popplerqt4.Poppler.Document.TextAntialiasing)
        self.page = self.doc.page(1)
        self.pageNum = 1
        self.pages = self.doc.numPages() - 1 # count from zero as poppler.doc does

    def getPageImage(self):
        return self.page.renderToImage()

    def getPage(self, num):
        self.pageNum = num
        self.page = self.doc.page(num)
        return self.getPageImage()

    def getWordPos(self):
        result = []
        words = self.page.text()
        return [w.bbox.getRect() for w in words]

    def getTextAreas(self):
        return [w.boundingBox() for w in self.page.textList()]

class Window(QtGui.QMainWindow):
    def __init__(self, pdf, parent = None):
        QtGui.QMainWindow.__init__(self, parent)
        self.generic = QtGui.QWidget(self)
        self.pdflabel = QtGui.QLabel(self)
        self.pdfArea = QtGui.QScrollArea()

        self.pdf = pdf

        self.pal = QtGui.QPalette(self.palette())
        self.setWindowTitle('Pdf notes')
        self.pdflabel.setBackgroundRole(self.pal.Base)
        self.vbox = QtGui.QVBoxLayout(self.generic)
        self.vbox.addWidget(self.pdfArea)

        self.setCentralWidget(self.pdfArea)
        self.overlay = OverlayEdit(self.centralWidget())
        self.keybinds = {
                Qt.Key_Space: self.pgDnEvent,
                Qt.Key_D: self.pgDnEvent,
                Qt.Key_U: self.pgUpEvent}

        self.setPage(0)

    def pgDnEvent(self, event):
        if self.pdf.pageNum < self.pdf.pages:
            self.setPage(self.pdf.pageNum + 1)
        event.accept()

    def pgUpEvent(self, event):
        if self.pdf.pageNum > 0:
            self.setPage(self.pdf.pageNum - 1)
        event.accept()

    def keyPressEvent(self, event):
        if event.key() in self.keybinds.keys():
            return self.keybinds[event.key()](event)
        else:
            return event.ignore()

    def setPage(self, pageNum):
        self.pdflabel.setPixmap(QtGui.QPixmap.fromImage(
            self.pdf.getPage(pageNum)))
        self.pdfArea.setWidget(self.pdflabel)
        self.setFiguresPoints(self.pdf.getTextAreas())

    def setFiguresPoints(self, figures):
        pageSize = self.pdf.page.pageSize()
        #fpercent = [[f / p for f in fig for p in pageSize ]for fig in figures]
        fpercent = [ f for f in figures ]
        self.overlay.figures = fpercent

    def resizeEvent(self, event):
        self.overlay.resize(event.size())
        event.ignore()

    def quitEvent(self, event):
        QtGui.QApplication.postEvent(self,QEvent(QEvent.Close))

def main(argv = None):
    app = QtGui.QApplication(sys.argv)
    if argv == None:
        argv = QtGui.QApplication.arguments()
    if len(argv) < 2:
        sys.stderr.write(usage)
        return None

    filename = argv[-1]
    pdf = Pdf(filename)
    view = Window(pdf)
    view.show()
    return (app, view)

if __name__ == "__main__":
    app, view = main()
    if app:
        sys.exit(app.exec_())
    sys.exit(1)
