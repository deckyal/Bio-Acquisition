import os
from os import getcwd
import sys
from operator import truediv
from plux_functions import *
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtGui import *
import numpy as np, random
from pypylon import pylon
import cv2
import csv
from multiprocessing import Pool
from threading import Thread
from multiprocessing import Process
import matplotlib
import time
from PyQt4.QtCore import QThread
from time import sleep
from time import sleep
#from vispy.plot import Fig


matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar

qtCreatorFile = "viewer.ui"  # Enter file here.

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class testThread(QtCore.QThread):
    def __init__(self,parent = None):
        QtCore.QThread.__init__(self, parent)
        self.counter = 0
        self.isStop = True

    def startThread(self):
        self.isStop  = False
        Thread(target=self.update, args=()).start()
        #Process(target=self.update, args=()).start()
        return self

    def stopThread(self):
        self.isStop = True

    def update(self):
        while not self.isStop:
            self.counter+=1
            if self.counter > 9999999 :
                self.counter = 0


class FetchingThreadClass(QtCore.QThread):                          # Infinite thread to communicate with robot
    def __init__(self, main_window):
        self.main_window = main_window
        super(FetchingThreadClass, self).__init__(main_window)
        self.fps = 2000
        self.dataCollectionTimer = QtCore.QTimer()
        self.dataCollectionTimer.moveToThread(self)
        self.dataCollectionTimer.timeout.connect(self.collectProcessData)
        self.toStop = True

    def collectProcessData(self):
        if not self.toStop:
            print ("Collecting Process Data")
            print(self.main_window.camera.counter)

    def run(self):
        self.toStop = False
        self.dataCollectionTimer.start(1000 / self.fps);
        loop = QtCore.QEventLoop()
        loop.exec_()

    def stop(self):
        self.toStop = True





class CameraQThread(QThread):
    def collectProcessData(self):
        print(camera.counterTemp)

    def __init__(self, *args, **kwargs):
        QThread.__init__(self, *args, **kwargs)
        self.fps = 240
        self.dataCollectionTimer =QtCore.QTimer()
        self.dataCollectionTimer.moveToThread(self)
        self.dataCollectionTimer.timeout.connect(self.collectProcessData)
        self.toStop = True

    def run(self):
        self.toStop = False
        self.dataCollectionTimer.start(1000/self.fps);
        loop = QtCore.QEventLoop()
        loop.exec_()

    def stop(self):
        self.toStop = True

from contextlib import contextmanager

@contextmanager
def terminating(thing):
    try:
        yield thing
    finally:
        thing.terminate()


def saveImageToFolder(*listData):
    for x in listData:
        print('writing : ',x[0])
        cv2.imwrite(str(x[0])+'.png',x[1])
        #exit(0)

def saveAnImageToFolder(name,data):
    cv2.imwrite(name, data)

class CameraThread(QtCore.QThread):
    def __init__(self,parent = None):
        QtCore.QThread.__init__(self, parent)
        self.stream = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        self.data = []
        self.temp = None
        self.toStopThread = True
        self.nowRecording = False
        self.counter = 0
        self.counterTemp  = 0

        self.converter = pylon.ImageFormatConverter()

        # converting to opencv bgr format
        self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

    def startThread(self):
        self.stream.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        self.toStopThread = False
        Thread(target=self.update, args=()).start()
        #Process(target=self.update, args=()).start()
        return self

    def stopThread(self):
        self.toStopThread = True

    def startRecording(self):
        self.nowRecording = True

    def stopRecording(self):
        self.nowRecording = False
        self.counter = 0

    def retrieveResult(self):
        temp = self.data
        self.data = []
        return temp

    def clean(self):
        self.data = []
        self.counter = 0

    def update(self):
        while self.stream.IsGrabbing():
            start_time = time.time()  # start time of the loop

            if self.toStopThread:
                self.stream.StopGrabbing()
                return;
            else:
                self.grabResult = self.stream.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                if self.counterTemp > 99999:
                    self.counterTemp = 99999
                else :
                    self.counterTemp+=1
                try :
                    if self.grabResult.GrabSucceeded():
                        # Access the image data
                        self.temp = [self.converter.Convert(self.grabResult).GetArray(),datetime.datetime.now()]
                    self.grabResult.Release()
                    #print(self.temp.shape)
                    if self.nowRecording and False:
                        self.data.append([self.counter,self.temp, datetime.datetime.now()])
                        self.counter+=1
                except :
                    print('error grabbing images')

            self.fps =  1.0 / (time.time() - start_time) # FPS = 1 / time to process loop

class BioThread(QtCore.QThread):
    def __init__(self,parent = None):
        QtCore.QThread.__init__(self, parent)
        self.stream = MyDevice("BTH00:07:80:46:E0:64")
        self.data = []
        self.temp = None
        self.toStopThread = True
        self.nowRecording = False
        self.counter = 0
        self.x = 1
        self.start_time = time.time()  # start time of the loop
        self.cf = 0
        self.fps = 0

    def clean(self):
        self.data = []
        self.counter = 0

    def startThread(self):
        self.stream.start(2000, 0xFF, 16)
        self.toStopThread = False
        Thread(target=self.update, args=()).start()
        #Process(target=self.update, args=()).start()
        return self

    def stopThread(self):
        self.toStopThread = True

    def startRecording(self):
        self.nowRecording = True

    def stopRecording(self):
        self.nowRecording = False

    def retrieveResult(self):
        temp = self.data
        self.data = []
        return temp

    def clean(self):
        self.data = []

    def update(self):
        while True:
            if self.toStopThread:
                self.stream.stop()
                self.stream.close()
                return;
            else:
                # otherwise, read the next frame from the stream
                self.stream.loop()
                self.temp = self.stream.inter
                #print(self.temp)
                if self.nowRecording:
                    self.data.append(self.temp)

            self.cf += 1
            if (time.time() - self.start_time) > self.x:
                self.fps =  self.cf / (time.time() - self.start_time)
                self.cf = 0
                self.start_time = time.time()

class MyApp(QtGui.QMainWindow, Ui_MainWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.pushButtonPlot.clicked.connect(self.graph)
        self.addToolBar(NavigationToolbar(self.canvas, self))

        self.pushButtonStartRecording.clicked.connect(self.startRecordAllModality)
        self.pushButtonStopRecording.clicked.connect(self.stopRecordAllModality)
        self.pushButtonExit.clicked.connect(self.toExit)
        self.pushButtonTrOn.clicked.connect(self.turnOnMachine)
        self.pushButtonTrOf.clicked.connect(self.turnOffMachine)
        self.pushButtonDel.clicked.connect(self.starting)

        global camera;
        camera = CameraThread(self)
        self.Bio = BioThread(self)

        camera.startThread()
        self.Bio.startThread()

        self.toRefresh = True

        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.showlcd)
        timer.start(500)
        self.showlcd()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.updateVis)
        self.timer.start(1000/50)


        self.timerG = QtCore.QTimer(self)
        self.timerG.timeout.connect(self.updateGraph)
        self.timerG.start(1000/1000)


        self.timerGC = QtCore.QTimer(self)
        self.timerGC.timeout.connect(self.updateGraphECG)
        #self.timerGC.start(1000/300)#300dps

        self.timerGD = QtCore.QTimer(self)
        self.timerGD.timeout.connect(self.updateGraphEDA)
        #self.timerGD.start(1000/300)


        self.timerRecorder = QtCore.QTimer(self)
        self.timerRecorder.timeout.connect(self.recordData)


        self.timerCRecorder = QtCore.QTimer(self)
        self.timerCRecorder.timeout.connect(self.fetchSaveImage)
        self.CCounter = 0
        self.listImages = []

        self.timerBRecorder = QtCore.QTimer(self)
        self.timerBRecorder.timeout.connect(self.fetchSaveBio)
        self.BCounter = 0
        self.listBios = []

        self.runningCount = 0
        self.visRunningCount = 0
        self.visBio=[]

        self.runningCountECG = 0
        self.runningCountEDA= 0

        self.visRunningCountECG = 0
        self.visRunningCountEDA = 0
        self.visECG=[]
        self.visEDA=[]

        self.displayEvery = 300
        self.ECGMinMax = [9999,-9999]
        self.EDAMinMax = [9999,-9999]
        self.ax = self.canvas.figure.add_subplot(111)
        self.isRecording = False

        #self.CameraQThread.start()
        #self.FetchingThreadClass = FetchingThreadClass(self)
        #self.FetchingThreadClass.run()


        self.stopCameraWritingThread = True

    def starting(self):
        self.cq = CameraQThread()
        self.cq.start()

    def graph(self):
        filedata = QtGui.QFileDialog.getOpenFileName(self, 'Open file', "C:/Users/cmtech/Documents/Python Scripts/",
                                                     '*.npy')
        filedata = str(filedata)
        data = np.load(filedata)
        datetime = data[:, 1]
        data = data[:, 0]
        ecg = []
        eda = []

        for i in range(data.shape[0]):
            sample1 = data[i][0]
            ecg.append(sample1)
        for j in range(data.shape[0]):
            sample2 = data[j][1]
            eda.append(sample2)

        print(ecg)
        print(len(ecg))

        # absolut1= map(abs,ecg)
        # absolut2= map(abs,eda)

        # maxvalue_ecg= max(ecg)
        # maxvalue_eda= max(eda)

        # ecg_norm = [e/max(ecg) for e in ecg]
        # eda_norm = [d/maxvalue_eda for d in eda]

        dt = datetime[-1] - datetime[0]
        seconds = dt.item().total_seconds()
        time = np.linspace(0, seconds, len(ecg))

        ax = self.canvas.figure.add_subplot(111)
        ax.plot(time, ecg, '-')
        self.canvas.draw()

    def toExit(self):
        self.close()


    def turnOnMachine(self):
        self.camera = CameraThread()
        self.Bio = BioThread()
        self.camera.startThread()
        self.Bio.startThread()
        self.timer.start(100)
        self.timerG.start(100)
        self.toRefresh = True
        self.runningCount = 0
        self.visBio=[]

    def turnOffMachine(self):
        self.runningCount = 0
        self.camera.stopThread()
        self.Bio.stopThread()
        self.timer.stop()
        self.timerG.stop()
        self.toRefresh = False

    def updateVis(self):
        #QMessageBox.information(None, 'Installer', 'Installation complete.', QMessageBox.Ok, QMessageBox.Ok)
        # display it to the qt

        img = camera.temp[0]

        h, w, c = img.shape
        bytesPerLine = 3 * w
        try :
            self.qImg = QtGui.QImage(img.data, w, h, bytesPerLine, QtGui.QImage.Format_RGB888).rgbSwapped()
            self.pixmap = QtGui.QPixmap.fromImage(self.qImg)
            self.labelCamera.setPixmap(self.pixmap)
        except :
            print('problem on drawing')

        bio = self.Bio.temp
        self.labelECG.setText(str(bio))

        self.labelSpeed.setText('FPS:'+str(round(camera.fps))+' - DPS:'+str(round(self.Bio.fps)))
        if self.isRecording :
            self.labelInfo.setText(
                'Now Recording...,' + str(round(abs(self.startTimeR - time.time()))) + ' Seconds Elapsed')
        #self.updateGraph()
        #t = Thread(target=self.updateGraph, args=()).start()
        #t = Thread(target=self.updateGraphOptim, args=()).start()
        pass

    def updateGraphOptim(self):
        self.runningCount+=1
        self.visRunningCount+=1
        bio = self.Bio.temp

        #if self.visRunningCount % (self.displayEvery * 2) == 0:
            #self.visBio = self.visBio[self.visRunningCount - self.displayEvery:]
            #self.visRunningCount = 0

        data = [self.runningCount, bio[1], bio[0][0], bio[0][1]]  # i,time,ecg,eda

        # print(vData.shape)
        x = [data[0]]  # [self.runningCount]#random.normal(size = 10)
        yECG = [data[2]]
        yEDA = [data[3]]

        if self.runningCount > self.displayEvery:
            left = self.runningCount - self.displayEvery
            right = self.runningCount
        else:
            left = 0
            right = self.runningCount

        if self.ECGMinMax[0] > yECG [0]:
            self.ECGMinMax[0] = yECG[0]
        if self.ECGMinMax[1] < yECG[0] :
            self.ECGMinMax[1] = yECG[0]

        if self.EDAMinMax[0] > yEDA[0]:
            self.EDAMinMax[0] = yEDA[0]
        if self.EDAMinMax[1] < yEDA[0]:
            self.EDAMinMax[1] = yEDA[0]

        print(self.ECGMinMax,self.EDAMinMax,x)

        #exit(0)

        self.gvECG.setYRange(self.ECGMinMax[0],self.ECGMinMax[1])
        self.gvECG.setXRange(left, right)
        self.gvECG.plot(x,yECG)

        # self.ax.set_ylim([np.min(yECG),np.max(yECG)])
        # self.ax.set_xlim([left,right])
        # self.ax.plot(x, yECG, '-')
        # self.canvas.draw()

        #self.gvEDA.setYRange(self.EDAMinMax[0],self.EDAMinMax[1])
        #self.gvEDA.setXRange(left,right)
        #self.gvEDA.plot(x,yEDA)


    def updateGraphECG(self):
        self.runningCountECG+=1
        self.visRunningCountECG+=1

        bio = self.Bio.temp
        displayEvery = 100

        if self.visRunningCountECG % (displayEvery +1) == 0:
            self.visECG = self.visECG[self.visRunningCountECG - displayEvery:]
            self.visRunningCountECG = 0

        self.visECG.append([self.runningCountECG, bio[1], bio[0][0]])  # i,time,ecg,eda
        vData = np.asarray(self.visECG)

        x = vData[:,0]  # [self.runningCount]#random.normal(size = 10)
        yECG = vData[:,2]

        if self.runningCountECG > displayEvery:
            left = self.runningCountECG - displayEvery
            right = self.runningCountECG
        else:
            left = 0
            right = self.runningCountECG

        self.gvECG.clear()
        self.gvECG.setYRange(np.min(yECG), np.max(yECG))
        self.gvECG.setXRange(left, right)
        self.gvECG.plot(x,yECG)

    def updateGraphEDA(self):
        self.runningCountEDA += 1
        self.visRunningCountEDA += 1

        bio = self.Bio.temp
        displayEvery = 100

        if self.visRunningCountEDA % (displayEvery +1) == 0:
            self.visEDA = self.visEDA[self.visRunningCountEDA - displayEvery:]
            self.visRunningCountEDA = 0

        self.visEDA.append([self.runningCountEDA, bio[1], bio[0][1]])  # i,time,ecg,eda
        vData = np.asarray(self.visEDA)

        x = vData[:, 0]  # [self.runningCount]#random.normal(size = 10)
        yEDA = vData[:, 2]

        if self.runningCountEDA > displayEvery:
            left = self.runningCountEDA - displayEvery
            right = self.runningCountEDA
        else:
            left = 0
            right = self.runningCountEDA

        self.gvEDA.clear()
        self.gvEDA.setYRange(np.min(yEDA), np.max(yEDA))
        self.gvEDA.setXRange(left, right)
        self.gvEDA.plot(x, yEDA)
        #self.ax.set_ylim([np.min(yEDA),np.max(yEDA)])
        #self.ax.set_xlim([left,right])
        #self.ax.plot(x, yEDA, '-')
        #self.canvas.draw()

        #ax_left = fig[0, 0]
        #ax_right = fig[0, 1]

        #plt.plot([1, 2, 3, 4], [1, 4, 9, 16])
        #vispyCanvas = plt.show()[0]
        #self.canvas(vispyCanvas.native)

    def updateGraph(self):
        self.runningCount+=1
        self.visRunningCount+=1

        bio = self.Bio.temp
        displayEvery = 100

        if self.visRunningCount % (displayEvery * 2) == 0:
            self.visBio = self.visBio[self.visRunningCount - displayEvery:]
            self.visRunningCount = 0

        self.visBio.append([self.runningCount, bio[1], bio[0][0], bio[0][1]])  # i,time,ecg,eda
        vData = np.asarray(self.visBio)

        x = vData[:,0]  # [self.runningCount]#random.normal(size = 10)
        yECG = vData[:,2]
        yEDA = vData[:,3]

        if self.runningCount > displayEvery:
            left = self.runningCount - displayEvery
            right = self.runningCount
        else:
            left = 0
            right = self.runningCount

        self.gvECG.clear()
        self.gvECG.setYRange(np.min(yECG), np.max(yECG))
        self.gvECG.setXRange(left, right)

        self.gvECG.plot(x,yECG)

        # self.ax.set_ylim([np.min(yECG),np.max(yECG)])
        # self.ax.set_xlim([left,right])
        # self.ax.plot(x, yECG, '-')
        # self.canvas.draw()

        #self.gvEDA.clear()
        #self.gvEDA.setYRange(np.min(yEDA),np.max(yEDA))
        #self.gvEDA.setXRange(left,right)
        #self.gvEDA.plot(x,yEDA)

    def showlcd(self):
        time = QtCore.QTime.currentTime()
        text = time.toString('hh:mm:ss')
        self.lcd.display(text)

    def setButton(self,isRecording):
        self.pushButtonStartRecording.setEnabled(not isRecording)
        self.groupBoxPatients.setEnabled(not isRecording)
        self.pushButtonExit.setEnabled(not isRecording)
        self.groupBoxMisc.setEnabled(not isRecording)
        self.pushButtonStopRecording.setEnabled(isRecording)

    def startRecordAllModality(self):
        j = 0
        directory = 'Patient_' + str(j)
        if not os.path.exists(directory):
            os.makedirs(directory)
        else:
            while os.path.exists("Patient_%s" % j):
                j += 1
            directory = 'Patient_' + str(j)
            os.makedirs(directory)

        self.dirName = directory

        self.csvName = directory + '/test' + str(j) + '.csv'
        self.bioName = directory + '/' + 'ecg_' + str(j - 1) + '.npy'
        self.startRecordCamera()
        self.startRecordBio()
        self.setButton(True)
        self.labelInfo.setText('Now Recording...')
        self.startTimeR = time.time()
        self.isRecording = True

    def stopRecordAllModality(self):
        totalTime = time.time()-self.startTimeR
        limages = len(self.listImages)
        self.stopRecordCamera()
        lbios = self.stopRecordBio()
        self.setButton(False)
        fps = round(truediv(limages,totalTime))
        dps = round(truediv(lbios,totalTime))
        self.labelInfo.setText(str(limages)+' Images and '+str(lbios)+' ECG/EDA Saved. For '+str(totalTime)+' ['+str(fps)+' FPS/'+str(dps)+' DPS]')
        self.isRecording  = False

    def startRecordCamera(self):
        self.fps = 1200
        self.timerCRecorder.start(1000/(self.fps))#120fps
        '''self.stopCameraWritingThread = False
        t = Thread(target=self.fetchSaveImage(), args=()).start()'''

    def stopRecordCamera(self):
        self.timerCRecorder.stop()
        #self.stopCameraWritingThread = True
        #print(self.listImages)
        #write csv

        with open(self.csvName, mode='w') as cf:
            cfWriter = csv.writer(cf, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for data in self.listImages:
                cfWriter.writerow([data[0], data[1]])

        self.CCounter = 0
        self.listImages = []

    def fetchSaveImage(self):
        imageData = camera.temp
        img = imageData[0]
        dateTimeD  = imageData[1]
        fname = self.dirName+'/'+str(self.CCounter)+'.png'
        t = Thread(target=saveAnImageToFolder, args=(fname,img)).start()
        self.listImages.append([fname, dateTimeD])
        self.CCounter+=1
        '''while not self.stopCameraWritingThread :
            imageData = camera.temp
            img = imageData[0]
            dateTimeD = imageData[1]
            fname = self.dirName + '/' + str(self.CCounter) + '.png'
            #print('creating thread')
            t = Thread(target=saveAnImageToFolder, args=(fname, img)).start()
            saveAnImageToFolder(fname, img)
            self.listImages.append([fname, dateTimeD])
            self.CCounter += 1'''


    def startRecordBio(self):
        self.Bio.startRecording()
        pass
        self.bps = 1500 #1000 acq per second. mean running every .001 = dps*1000
        self.timerBRecorder.start(1000/self.bps)#1000fps

    def stopRecordBio(self):
        self.Bio.stopRecording()
        #write npy
        self.listBios = self.Bio.retrieveResult()
        np.save(self.bioName, np.asarray(self.listBios))
        saved = len(self.listBios)

        self.BCounter = 0
        self.listBios = []
        return(saved)

        pass
        self.timerBRecorder.stop()

        # print('saved : ',len(self.listImages))

    def fetchSaveBio(self):
        pass
        self.listBios.append(self.Bio.temp)






    def recordData(self):
        imageData = camera.retrieveResult()
        print('threading')
        print(len(imageData))
        n_pool = 10
        with terminating(Pool(processes=n_pool)) as p:
            p.apply_async(saveImageToFolder, imageData)
    def testPrint(self,stringData):
        print(stringData)



    def startRecording(self):
        self.Bio.startRecording()
        camera.startRecording()
        self.timerRecorder.start(5000)#save every 1000/10 second

    def stopRecording(self):
        self.Bio.stopRecording()
        camera.stopRecording()
        self.timerRecorder.stop()


    def saveBioToFolder(self,listData):
        for x in listData:
            cv2.imwrite(str(x[0]+'.png'), x[0][0])

    def closeEvent(self, event):
        print "Exiting"

        camera.stopThread()
        self.Bio.stopThread()
        event.accept()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
