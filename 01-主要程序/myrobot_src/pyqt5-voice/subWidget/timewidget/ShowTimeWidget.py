import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *


class ShowTimeWidget(QWidget):
    """
    docstring
    """
    pass
    def __init__(self,parent=None):
        super(ShowTimeWidget,self).__init__(parent)
        
        self.setWindowTitle("Dynamically current time")
        layout=QVBoxLayout()
        self.label=QLabel("Current Time")
        layout.addWidget(self.label)
        self.setLayout(layout)
       
        self.timer=QTimer()
        self.timer.timeout.connect(self.show_time)
        self.timer.start(1000) # timer interval(ms)/frequency(kHz)


    def show_time(self):
        time=QDateTime.currentDateTime()
        '''
            timeDisplay=time.toString("yyyy-MM-dd hh:mm:ss dddd")
        '''
        timeDisplay=time.toString("yyyy-MM-dd hh:mm:ss dddd")
        # print(timeDisplay)

        # tYear=time.toString("yyyy")
        # tMonth=time.toString("MM")
        # tDay=time.toString("dd")
        # tHour=time.toString("hh")
        # tMinute=time.toString("mm")
        # tSecond=time.toString("ss")
        # tWeek=time.toString("dddd")
        # print(tYear,tMonth,tDay,tHour,tMinute,tSecond,tWeek)
        # timeDisplay="%s-%s-%s %s:%s:%s %s"%(tYear,tMonth,tDay,tHour,tMinute,tSecond,tWeek)

        self.label.setText(timeDisplay)
    
    def getTime(self):
        time=QDateTime.currentDateTime()
        '''
            timeDisplay=time.toString("yyyy-MM-dd hh:mm:ss dddd")
        '''
        timeDisplay=time.toString("yyyy-MM-dd hh:mm:ss dddd")
        return timeDisplay

class ShowDateWidget(QWidget):
    """
        ShowDateWidget
        ===
        display date by format as follows
        >>> year-month-day
        >>> 2000-12-31
    """
    pass
    def __init__(self,parent=None):
        super(ShowDateWidget,self).__init__(parent)
        
        self.setWindowTitle("Dynamically current time")
        layout=QVBoxLayout()
        self.label=QLabel("Current Time")
        layout.addWidget(self.label)
        self.setLayout(layout)
       
        self.timer=QTimer()
        self.timer.timeout.connect(self.show_time)
        self.timer.start(1000) # timer interval(ms)/frequency(kHz)


    def show_time(self):
        time=QDateTime.currentDateTime()
        '''
            timeDisplay=time.toString("yyyy-MM-dd hh:mm:ss dddd")
        '''
        timeDisplay=time.toString("yyyy-MM-dd")
        print(timeDisplay)

        self.label.setText(timeDisplay)
        
class DisplayFullTimeWidget(QWidget):
    """
        DisplayFullTimeWidget
        ===
        base class 
    """
    def __init__(self):
        # QWidget.__init__(self)
        super().__init__()

        self.__tYear = ''
        self.__tMonth = ''
        self.__tDay = ''
        self.__tHour = ''
        self.__tMinute = ''
        self.__tSecond = ''
        self.__tWeek = ''

        self.setWindowTitle("dynamically display current time")

        layout = QVBoxLayout()
        self._label = QLabel()

        layout.addWidget(self._label)
        self.setLayout(layout)

        self.__timer = QTimer()
        self.__timer.timeout.connect(self.display_time)
        self.__timer.start(1000)  # timer interval(ms)/frequency(kHz)

    def __update_time(self):
        time = QDateTime.currentDateTime()
        self.__tYear = time.toString("yyyy")
        self.__tMonth = time.toString("MM")
        self.__tDay = time.toString("dd")
        self.__tHour = time.toString("hh")
        self.__tMinute = time.toString("mm")
        self.__tSecond = time.toString("ss")
        self.__tWeek = time.toString("dddd")

    def display_time(self):
        """
            Display Time
            ===
            this function `display_time` need to be overwritten for displaying the time

        """
        self.__update_time()

        # !!! change this format of the time
        currentTime = self.get_currentTime()
        tYear = currentTime[0]
        tTime = currentTime[1]
        tWeek = currentTime[2]
        timeDisplay="%s-%s-%s %s:%s:%s %s"%(tYear[0],tYear[1],tYear[2],tTime[0],tTime[1],tTime[2],tWeek)

        self._label.setText(timeDisplay)

    def get_currentTime(self):
        self.__update_time()
        currentFullTime = (
            (self.__tYear, self.__tMonth, self.__tDay),
            (self.__tHour, self.__tMinute, self.__tSecond),
            self.__tWeek
        )
        return currentFullTime


class DisplayDateWidget(DisplayFullTimeWidget):
    def __init__(self):
        super().__init__()

    def display_time(self):        
        currentTime = self.get_currentTime()
        tDate = currentTime[0]
        timeDisplay = "%s-%s-%s" % (tDate[0], tDate[1], tDate[2])
        self._label.setText(timeDisplay)
        

class DisplayTimeWidget(DisplayFullTimeWidget):
    def __init__(self):
        super().__init__()

    def display_time(self):
        currentTime =self.get_currentTime()
        tTime = currentTime[1]
        timeDisplay = "%s:%s:%s"% (tTime[0], tTime[1], tTime[2])
        self._label.setText(timeDisplay)


"""
    run
"""
if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = DisplayDateWidget()
    form.show()
    sys.exit(app.exec_())