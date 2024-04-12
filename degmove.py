# import
import sys
import math
import re
import emp400 
import ui_degmove

from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox
from PyQt5.QtCore import QTimer, Qt
from PyQt5 import QtCore

class DegMoveForm(QDialog):

    mmToPulse = 200      # 5 mm = 1 revolution = 1000 pulses
    moveLimit = 45       # +-45 mm from the center
    pos = 0
    ang = 0 
    cen = 0
    inverted = 1 # 1 is default, -1 is inverted

    a = 1/9000.
    b = 0.01
    
    def __init__(self):
        super(DegMoveForm, self).__init__()

        try:
            self.emp = emp400.EMP400()
        except Exception as e:
            msgBox = QMessageBox();
            msgBox.setWindowTitle("Error")
            msgBox.setText("%s" % e)
            msgBox.exec();
            quit()

        self.ui = ui_degmove.Ui_DegMove()
        self.ui.setupUi(self)

        self.ui.pbSetZero.clicked.connect(self.setzero)
        self.ui.pbMoveZero.clicked.connect(self.movezero)
        self.ui.pbMove.clicked.connect(self.move)
        self.ui.pbMoveLimit.clicked.connect(self.movelimit)
        self.ui.pbMoveCenter.clicked.connect(self.movecenter)
        self.ui.pbMotorStatus.clicked.connect(self.motorStatus)
        self.ui.pbQuit.clicked.connect(quit)
        self.ui.leMMMove.textEdited.connect(self.mmEdited)
        self.ui.leDegMove.textEdited.connect(self.degEdited)
        self.ui.checkBox.stateChanged.connect(self.degInvert)

        (pos1, pos2) = (0, 0) 
        (pos1, pos2) = self.motorStatus() # for offline test (comment out)
        pos1 = -pos1 / self.mmToPulse # minus for the different convention between motor and exp. coord.
        pos2 = -pos2 / self.mmToPulse # minus for the different convention between motor and exp. coord.
        self.pos = (pos1 - pos2)/2
        self.cen = (pos1 + pos2)/2
        self.ang = self.posToAng(self.pos)
        self.ui.lCurCen.setText("%.4f mm" % self.cen)        
        self.ui.lCurPos.setText("%.4f mm" % self.pos)
        self.ui.lCurAng.setText("%.2f mrad" % self.ang)
        self.ui.Figure.moveDeg(self.cen, self.pos)

    def decodeOutput(self, lines):
        lines[:] = [line.decode() for line in lines]
        lines[:] = [line.replace('\r\n','\n') for line in lines]
        lines[:] = [line.replace('\n\r','\n') for line in lines]
        return ("".join(lines))

    def decodeStatusOutput(self, lines):
        lines[:] = [line.decode() for line in lines]
        lines[:] = [line.replace('\r\n','\n') for line in lines]
        lines[:] = [line.replace('\n\r','\n') for line in lines]
        lines[:] = [line[5:] for line in lines]
        lines.pop(0)
        lines.pop(0)
        return ("".join(lines))

    def procOut(self, lines):
        self.ui.tbOut.insertPlainText(self.decodeOutput(lines))
        self.ui.tbOut.verticalScrollBar().setValue(self.ui.tbOut.verticalScrollBar().maximum())

    def statusOut(self, lines, label):
        output = self.decodeStatusOutput(lines)
        m = re.search("PC[12] = (-?[0-9]+)",output)
        statStartInd = output.find("System status")
        output = output[statStartInd:]
        label.setText(output)
        return int(m.group(1))

    def movecenter(self):
        self.lockButtons()
        QTimer.singleShot(20000, self.unlockButtons)

        self.procOut(self.emp.commrecv("run 4"))

    def setzero(self):
        self.procOut(self.emp.commrecv("run 0"))

    def movelimit(self):
        self.lockButtons()
        QTimer.singleShot(40000, self.unlockButtons)

        self.procOut(self.emp.commrecv("run 3"))

    def movezero(self):
        self.lockButtons()
        QTimer.singleShot(20000, self.unlockButtons)

        self.procOut(self.emp.commrecv("run 2"))
        self.cen = 0
        self.pos = 0
        self.ang = self.posToAng(self.pos)
        self.ui.lCurCen.setText("%.4f mm" % self.cen)           
        self.ui.lCurPos.setText("%.4f mm" % self.pos)
        self.ui.lCurAng.setText("%.2f mrad" % self.ang)
        self.ui.Figure.moveDeg(self.cen, self.pos)

    def move(self):
        try:
            if self.ui.rbMMMove.isChecked(): 
                input = float(self.ui.leMMMove.text())
                posi = input
            else:
                input = float(self.ui.leDegMove.text())
                posi = self.angToPos(input)
            input2 = float(self.ui.leMPMove.text())
            ceni = input2
        except ValueError:
            msgBox = QMessageBox();
            msgBox.setWindowTitle("Warning")
            msgBox.setText("Please input an figure.")
            msgBox.exec();
            return

        if (abs(posi) + abs(ceni)) > self.moveLimit:
            msgBox = QMessageBox();
            msgBox.setWindowTitle("Warning")
            msgBox.setText("Please input a value within the limit (+-%d mm)." % self.moveLimit)
            msgBox.exec();
            return

        pulse_p = int(posi * self.mmToPulse)
        pulse_c = int(ceni * self.mmToPulse)

        self.lockButtons()
        QTimer.singleShot(40000, self.unlockButtons)

        comms = ["edit 1", "a8", "d1 %d" % (-pulse_c - pulse_p), "a9", "d2 %d" % (-pulse_c + pulse_p), "q", "run 1"]     
        for comm in comms:
            self.procOut(self.emp.commrecv(comm))

        self.pos = pulse_p / self.mmToPulse
        self.ang = self.posToAng(self.pos)
        self.ui.lCurPos.setText("%.4f mm" % self.pos)
        self.ui.lCurAng.setText("%.2f mrad" % self.ang)

        self.cen = pulse_c / self.mmToPulse
        self.ui.lCurCen.setText("%.4f mm" % self.cen)  
        
        self.ui.Figure.moveDeg(self.cen, self.pos)

    def motorStatus(self):
        try:
            pulse1 = self.statusOut(self.emp.commrecv("r1"), self.ui.lMotor1Status)
        except Exception as e:
            msgBox = QMessageBox();
            msgBox.setWindowTitle("Error")
            msgBox.setText("%s" % e)
            msgBox.exec();
            quit()
        pulse2 = self.statusOut(self.emp.commrecv("r2"), self.ui.lMotor2Status)
        return (pulse1, pulse2)

    def mmEdited(self):
        self.ui.rbMMMove.setChecked(True)
        try:
            input = float(self.ui.leMMMove.text())
        except ValueError:
            return
        self.ui.leDegMove.setText("%.2f" % (self.posToAng(input)))

    def degEdited(self):
        self.ui.rbDegMove.setChecked(True)
        try:
            input = float(self.ui.leDegMove.text())
        except ValueError:
            return
        self.ui.leMMMove.setText("%.4f" % self.angToPos(input))

    def degInvert(self, state):
        self.inverted = -1 if (state == Qt.Checked) else 1
        self.ui.Figure.invertDeg(state == Qt.Checked)
        self.ang = self.posToAng(self.pos)
        self.ui.lCurAng.setText("%.2f mrad" % self.ang)

    def posToAng(self, pos):
        return 1000*(math.atan(4*self.a*pos + 2*self.b*self.inverted))

    def angToPos(self, ang):
        return (( math.tan(ang/1000.) - 2*self.b*self.inverted )/4./self.a)

    def lockButtons(self):
        self.ui.pbSetZero.setEnabled(False)
        self.ui.pbMoveZero.setEnabled(False)
        self.ui.pbMove.setEnabled(False)
        self.ui.pbMoveLimit.setEnabled(False)
        self.ui.pbMoveCenter.setEnabled(False)
        self.ui.pbMotorStatus.setEnabled(False)
        self.ui.pbQuit.setEnabled(False)
        self.ui.groupBox.setEnabled(False)
        self.ui.checkBox.setEnabled(False)
        
    def unlockButtons(self):
        self.ui.pbMoveZero.setEnabled(True)
        self.ui.pbMove.setEnabled(True)
        self.ui.pbQuit.setEnabled(True)
        self.ui.pbMotorStatus.setEnabled(True)
        self.ui.checkBox.setEnabled(True)
        self.ui.groupBox.setEnabled(True)
        if self.ui.groupBox.isChecked():
            self.ui.pbMoveLimit.setEnabled(True)
            self.ui.pbMoveCenter.setEnabled(True)
            self.ui.pbSetZero.setEnabled(True)
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myapp = DegMoveForm()
    myapp.show()
    sys.exit(app.exec_())
