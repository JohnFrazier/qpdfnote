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
    def __init__(self, parent=None):
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

class DisplayInfo():
    def __init__(self, app):
        window = app.desktop().window().x11Info()
        self.depth = window.depth()
        self.dpiX = window.appDpiX()
        self.dpiY = window.appDpiY()

class PdfState():
    def __init__(self, filename, page=1, zoom=1, rotate=None, hints=None):
        self.filename = filename
        self.page = page
        self.zoom = zoom
        if rotate:
            self.rotate = rotate
        else:
            self.rotate = popplerqt4.Poppler.Page.Rotate0
        self.rotate = rotate
        if not hints:
            self.renderHints = [ popplerqt4.Poppler.Document.Antialiasing,
                    popplerqt4.Poppler.Document.TextAntialiasing ]
        else:
            self.renderHints = hints

class Pdf():
    def __init__(self, filename):
        self.state=PdfState(filename)
        self.doc = popplerqt4.Poppler.Document.load(filename)
        self.page = self.doc.page(self.state.page - 1)
        self.pages = self.doc.numPages() # count from zero as poppler.doc does

    def setOptions(self, state=None):
        if state:
            if state.filename != self.state.filename:
                self.doc = popplerqt4.Poppler.Document.load(state.filename)
            self.state = state
        for r in self.state.renderHints:
            self.doc.setRenderHint(r)
        resetPage()

    def decPage(self):
        if 1 < self.state.page:
            self.state.page -= 1
            self.resetPage()
            return True
        return False

    def incPage(self):
        if self.pages > self.state.page:
            self.state.page += 1
            self.resetPage()
            return True
        return False

    def resetPage(self):
        self.page = self.doc.page(self.state.page - 1)

    def incZoom(self):
        self.state.zoom *= 2
        print(self.state.zoom)
        self.resetPage()

    def decZoom(self):
        self.state.zoom /= 2
        print(self.state.zoom)
        self.resetPage()

    def getPageImage(self):
        return self.page.renderToImage()

    def getWordPos(self):
        result = []
        words = self.page.text()
        return [w.bbox.getRect() for w in words]

    def getTextAreas(self):
        return [w.boundingBox() for w in self.page.textList()]

    def getText(self):
        return self.page.textList()

class Window(QtGui.QMainWindow):
    def __init__(self, ctx, parent = None):
        QtGui.QMainWindow.__init__(self, parent)
        self.generic = QtGui.QWidget(self)
        self.pdflabel = QtGui.QLabel(self)
        self.pdfArea = QtGui.QScrollArea()
        self.ctx=ctx

        self.pal = QtGui.QPalette(self.palette())
        self.setWindowTitle('Pdf notes')
        self.pdflabel.setBackgroundRole(self.pal.Base)
        self.vbox = QtGui.QVBoxLayout(self.generic)
        self.vbox.addWidget(self.pdfArea)

        self.setCentralWidget(self.pdfArea)
        self.overlay = OverlayEdit(self.centralWidget())
        self.keybinds = {
                Qt.Key_Space: self.pgDnEvent,
                Qt.Key_J: self.pgDnEvent,
                Qt.Key_K: self.pgUpEvent,
                Qt.Key_Up: self.pgUpEvent,
                Qt.Key_Down: self.pgDnEvent,
                Qt.Key_Plus: self.zoomIncEvent,
                Qt.Key_Minus: self.zoomDecEvent}
        self.setPage()


    def zoomIncEvent(self, event):
        self.ctx.pdf.incZoom()
        self.setPage()
        event.accept()

    def zoomDecEvent(self, event):
        self.ctx.pdf.decZoom()
        self.setPage()
        event.accept()

    def pgDnEvent(self, event):
        self.ctx.pdf.incPage()
        self.setPage()
        event.accept()

    def pgUpEvent(self, event):
        self.ctx.pdf.decPage()
        self.setPage()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() in self.keybinds.keys():
            return self.keybinds[event.key()](event)
        else:
            return event.ignore()

    def setPage(self):
        self.pdflabel.setPixmap(QtGui.QPixmap.fromImage(
            self.ctx.pdf.getPageImage( )))
        self.pdfArea.setWidget(self.pdflabel)
        self.setFiguresPoints(self.ctx.pdf.getTextAreas())

    def setFiguresPoints(self, figures):
        pageSize = self.ctx.pdf.page.pageSize()
        #fpercent = [[f / p for f in fig for p in pageSize ]for fig in figures]
        fpercent = [ f for f in figures ]
        self.overlay.figures = fpercent

    def resizeEvent(self, event):
        self.overlay.resize(event.size())
        event.ignore()

    def quitEvent(self, event):
        QtGui.QApplication.postEvent(self,QEvent(QEvent.Close))

class Context():
    def __init__(self, filename=None):
        self.app = QtGui.QApplication(sys.argv)
        self.pdf = None
        if filename:
            self.pdf = Pdf(filename)
        self.window = Window(self)
        self.dpy = DisplayInfo(self.app)
        self.updateQueue = []

    def showWindow(self):
        self.window.show()

def main(argv = None):
    if not argv:
        argv = sys.argv
    if len(argv) < 2:
        sys.stderr.write(usage)
        return None

    filename = argv[-1]
    ctx = Context(filename=filename)
    ctx.showWindow()
    return ctx

if __name__ == "__main__":
    ctx = main()
    if ctx:
        sys.exit(ctx.app.exec_())
    sys.exit(1)
