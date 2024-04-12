import sys
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor, QFont, QPolygon, QPen, QTransform
from PyQt5.QtCore import Qt, QPointF, QPoint


class DegMoveVis(QWidget):

    pos = 0
    cen = 0

    a = 1/9000.
    b = 0.01
    c1 = 1.
    c2 = 2.
    
    def __init__(self, wid):
        super().__init__(wid)

    def degCThick(self, x):
        return self.a*x*x + self.b*x + self.c1
    def degDThick(self, x):
        return -self.a*x*x + self.b*x + self.c2
    def degCenThick(self):
        return (4*self.a*self.pos+2*self.b)*(-self.cen) + self.c1 + self.c2 # inverse X coordinate
        
    def make_deg(self, degThick, xs=1, ys=25):
        deg_QP = []
        for x in range(-75,76):
            deg_QP.append(QPoint(int(x*xs), int(degThick(x)*ys)))
        deg_QP.append(QPoint(int( 75*xs),0))
        deg_QP.append(QPoint(int(-75*xs),0))
        return QPolygon(deg_QP)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        self.drawBase(qp)

        qp_degC = QPainter()
        qp_degC.begin(self)
        m1 = QTransform() # this is the coordinate transformation
        m1.translate( 210,  90 )
        m1.scale( -1, -1 ) # X, Y all reversed for DegC
        qp_degC.setTransform(m1)        
        qp_degC.translate(self.cen-self.pos,0) # no need to inverse cen, pos (coordinate transformed)
        self.drawDeg(qp_degC, self.degCThick)

        qp_degD = QPainter()
        qp_degD.begin(self)
        m2 = QTransform() # this is the coordinate transformation
        m2.translate( 210, 100 )
        m2.scale( -1,  1 ) # X should be reversed for DegD (Y already reversed by QT coordinate convention)
        qp_degD.setTransform(m2)
        qp_degD.translate(self.cen+self.pos,0) # no need to inverse cen, pos (coordinate transformed)
        self.drawDeg(qp_degD, self.degDThick)

        qp_degCL = QPainter()
        qp_degCL.begin(self)
        mc = QTransform() # this is the coordinate transformation
        mc.translate( 210, 0 )
        #mc.scale( -1,  1 ) # X should be reversed for Center line
        qp_degCL.setTransform(mc)        
        qp_degCL.translate(-self.cen,0) # need to inverse cen (coord. not transformed)
        self.drawDegCenLine(qp_degCL)
        
    def drawBase(self, qp):
        qp.setPen(QColor("black"))
        qp.drawRect(0,40,50,40)
        qp.drawRect(0,110,50,40)
        qp.drawRect(50,55,10,10)
        qp.drawRect(50,125,10,10)
        qp.drawRect(60,30,300,60)
        qp.drawRect(60,100,300,60)
        qp.setPen(Qt.DashLine)
        qp.drawLine(60+150, 20, 60+150, 190)
        qp.drawText(60+150-15,170+35,"beam ax.")
        qp.drawText(10, 170+35, "@ beam ax. = %.3f mm" % self.degCenThick())
        qp.drawText(60+150+50,15,"downstream")
        #qp.drawText(60+300/2+70,170+15,"upstream")
        qp.drawText(7,65,"Motor 2")
        qp.drawText(7,135,"Motor 1")
        qp.drawText(60+150-200,170+15,"<-- x coord.")
        qp.drawText(60+150-160,15,"thick" if self.b > 0 else "thin")
        qp.drawText(60+150+140,15,"thin" if self.b > 0 else "thick")

    def drawDeg(self, qp, degThick):
        qp.setPen(QColor("blue"))
        qp.drawPolygon(self.make_deg(degThick))
        qp.setPen(QPen(QColor("blue"),1,Qt.DashDotLine))
        qp.drawLine(0, 0, 0, 60) # X,Y is relative coordinate

    def drawDegCenLine(self, qp):
        qp.setPen(QColor("red"))
        qp.drawLine(  0, 20,  0, 170) # X is relative coordinate
        qp.drawText(-15,185,"deg cen") # X is relative coordinate
        
    def moveDeg(self, cen, pos):
        self.pos = pos
        self.cen = cen
        self.update()

    def invertDeg(self, flag):
        self.b = -0.01 if flag else 0.01
        self.update()
        
