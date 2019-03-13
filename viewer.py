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
import datetime
from time import sleep
from time import sleep
import psutil
import shutil
#from vispy.plot import Fig


matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar

qtCreatorFile = "viewer.ui"  # Enter file here.

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class visImageThread(QThread):
    def collectProcessData(self):
        
        global stepImage, toDisplayImgData,toDisplayImgTime,labelTimeImage
        
        theIndex = self.runningIndexImage * stepImage
        
        if theIndex < len(toDisplayImgData):
            self.runningIndexImage += 1
            imageToDisplay = cv2.imread(toDisplayImgData[theIndex])
            h, w, c = imageToDisplay.shape
            bytesPerLine = 3 * w
            try:
                qImg = QtGui.QImage(imageToDisplay.data, w, h, bytesPerLine,
                                         QtGui.QImage.Format_RGB888).rgbSwapped()
                pixmap = QtGui.QPixmap.fromImage(qImg)
                labelCamera.setPixmap(pixmap)
                
                labelTimeImage.setText(str(toDisplayImgTime[theIndex]))
                
            except:
                print('problem on drawing')
            pass

        else:
            print('image finished')
            self.isFinished = True

    def __init__(self, *args, **kwargs):
        QThread.__init__(self, *args, **kwargs)
        global displayFPS
        self.fps = displayFPS
        self.dataCollectionTimer =QtCore.QTimer()
        self.dataCollectionTimer.moveToThread(self)
        self.dataCollectionTimer.timeout.connect(self.collectProcessData)
        self.runningIndexImage = 0

    def run(self):
        self.isFinished = False
        self.dataCollectionTimer.start(1000/self.fps);
        loop = QtCore.QEventLoop()
        loop.exec_()

    def getStatus(self):
        return self.isFinished


class visBioThread(QThread):
    def collectProcessData(self):
        global stepBio
        global toDisplayBioData
        global toDisplayBioTime
        global displayEvery
        global labelTimeBio
        
        theIndex = self.runningIndexBio * stepBio
        if theIndex < len(toDisplayBioData[0]) and self.toUpdate:
            self.runningIndexBio += 1
            global gvECG,gvEDA,displayECG
            
            bio = [toDisplayBioData[0][theIndex], toDisplayBioData[1][theIndex]]
            
            labelTimeBio.setText(str(toDisplayBioTime[theIndex]))
            
            self.runningCount += 1
            self.visRunningCount += 1

            #displayEvery = 100

            if self.visRunningCount % (displayEvery * 2) == 0:
                self.visBio = self.visBio[len(self.visBio) - displayEvery:]
                self.visRunningCount = 0

            self.visBio.append([self.runningCount, bio[0], bio[1]])  # i,time,ecg,eda
            vData = np.asarray(self.visBio)

            x = vData[:, 0]  # [runningCount]#random.normal(size = 10)
            yECG = vData[:, 1]
            yEDA = vData[:, 2]

            if self.runningCount > displayEvery:
                left = self.runningCount - displayEvery
                right = self.runningCount
            else:
                left = 0
                right = self.runningCount
            
            if displayECG : 
                data = yECG 
            else : 
                data = yEDA
            
            gvECG.clear()
            gvECG.setYRange(np.min(data),np.max(data))
            gvECG.setXRange(left,right)
            gvECG.plot(x,data)
            
            #print('printing',displayECG,data)
            
            '''if displayECG : 
                gvECG.clear()
                gvECG.setYRange(np.min(yECG), np.max(yECG))
                gvECG.setXRange(left, right)
                gvECG.plot(x, yECG)
            else : 
                gvEDA.clear()
                gvEDA.setYRange(np.min(yECG), np.max(yECG))
                gvEDA.setXRange(left, right)
                gvEDA.plot(x, yECG)'''
            
        else:
            print('bio finished')
            self.isFinished = True


    def __init__(self, *args, **kwargs):
        QThread.__init__(self, *args, **kwargs)
        global displayDPS
        self.fps = displayDPS
        self.dataCollectionTimer =QtCore.QTimer()
        self.dataCollectionTimer.moveToThread(self)
        self.dataCollectionTimer.timeout.connect(self.collectProcessData)
        self.toUpdate = True
        self.runningIndexBio = 0
        self.visRunningCount = 0
        self.runningCount = 0
        self.visBio = []

    def run(self):
        self.isFinished = False
        self.dataCollectionTimer.start(1000/self.fps);
        loop = QtCore.QEventLoop()
        loop.exec_()

    def getStatus(self):
        return self.isFinished


class CameraQThread(QThread):
    def collectProcessData(self):
        #print(camera.counterTemp)
        global CCounter
        global dirName
        global camera
        imageData = camera.temp
        img = imageData[0]
        dateTimeD = imageData[1]
        #print(dirName,dateTimeD)
        fname = dirName + '\\' + str(CCounter) + '.png'
        #print(fname)
        t = Thread(target=saveAnImageToFolder, args=(fname, img)).start()
        listImages.append([fname, dateTimeD])
        CCounter += 1

    def __init__(self, *args, **kwargs):
        global recordingFPS
        QThread.__init__(self, *args, **kwargs)
        self.dataCollectionTimer =QtCore.QTimer()
        self.dataCollectionTimer.moveToThread(self)
        self.dataCollectionTimer.timeout.connect(self.collectProcessData)
        self.toStop = True

    def run(self):
        print('saving with ',recordingFPS,' FPS')
        self.fps = recordingFPS
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
            try :
                self.fps =  1.0 / (time.time() - start_time) # FPS = 1 / time to process loop
            except :
                self.fps = "None"

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
        global recordingDPS
        self.stream.start(recordingDPS, 0xFF, 16)
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
                self.temp = np.asarray(self.stream.inter)
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
        #self.pushButtonPlot.clicked.connect(self.graph)
        self.pushButtonPlot.clicked.connect(self.replay)
        #self.addToolBar(NavigationToolbar(self.canvas, self))
        self.navi_toolbar = NavigationToolbar(self.canvas, self)
        self.navi_toolbar2 = NavigationToolbar(self.canvasEDA, self)
        self.verticalLayout.addWidget(self.navi_toolbar)
        self.verticalLayout_2.addWidget(self.navi_toolbar2)
        
        self.pushButtonStartRecording.clicked.connect(self.startRecordAllModality)
        self.pushButtonStopRecording.clicked.connect(self.stopRecordAllModality)
        self.pushButtonExit.clicked.connect(self.toExit)
        self.pushButtonTrOn.clicked.connect(self.turnOnMachine)
        self.pushButtonTrOf.clicked.connect(self.turnOffMachine)
        self.pushButtonDel.clicked.connect(self.delSinglePatient)
        self.pushPlayback.clicked.connect(self.adjustPlayback)
        self.listWidget.clicked.connect(self.getListInfo)
        self.listWidgetE.clicked.connect(self.getListInfoE)
        self.pushButtonToEx.clicked.connect(self.transferToEx)
        self.pushButtonToIn.clicked.connect(self.transferToIn)
        
        self.spinBoxFPS.valueChanged.connect(self.updateFPS)
        self.spinBoxDPS.valueChanged.connect(self.updateDPS)
        self.spinBoxBSR.valueChanged.connect(self.updateBSR)
        self.listWidgetView.clicked.connect(self.updateToDisplay)

        global recordingFPS
        recordingFPS = int(self.spinBoxFPS.text())
        
        global recordingDPS
        recordingDPS = int(self.spinBoxDPS.text())
        
        global camera;
        camera = CameraThread(self)
        
        global Bio
        Bio = BioThread(self)
        
        global labelTimeImage
        labelTimeImage = self.labelTimeImage
        
        global labelTimeBio
        labelTimeBio = self.labelTimeBio

        camera.startThread()
        Bio.startThread()

        self.toRefresh = True
        
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.showlcd)
        timer.start(100)
        self.showlcd()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.updateVis)
        self.timer.start(1000/50)


        self.timerG = QtCore.QTimer(self)
        self.timerG.timeout.connect(self.updateGraph)
        self.timerG.start(1000/500)


        self.timerGC = QtCore.QTimer(self)
        self.timerGC.timeout.connect(self.updateGraphECG)
        #self.timerGC.start(1000/300)#300dps

        self.timerGD = QtCore.QTimer(self)
        self.timerGD.timeout.connect(self.updateGraphEDA)
        #self.timerGD.start(1000/300)
        

        self.timerCRecorder = QtCore.QTimer(self)
        self.timerCRecorder.timeout.connect(self.fetchSaveImage)

        self.timerBRecorder = QtCore.QTimer(self)
        self.timerBRecorder.timeout.connect(self.fetchSaveBio)
        self.BCounter = 0
        self.listBios = []
        
        self.samplingDisplayFPS = 30
        self.samplingDisplayDPS = 100
        
        global runningCount
        runningCount = 0
        global visRunningCount
        visRunningCount = 0
        
        
        global displayECG
        self.listWidgetView.item(0).setSelected(True)
        displayECG = True

        global visBio
        visBio=[]

        self.runningCountECG = 0
        self.runningCountEDA= 0

        global gvECG
        gvECG = self.gvECG

        
        global gvEDA
        gvEDA = self.gvEDA

        self.visRunningCountECG = 0
        self.visRunningCountEDA = 0
        self.visECG=[]
        self.visEDA=[]

        self.ECGMinMax = [9999,-9999]
        self.EDAMinMax = [9999,-9999]
        self.ax = self.canvas.figure.add_subplot(111)
        
        self.displayEDA = True
        
        if self.displayEDA : 
            self.ax2 = self.canvasEDA.figure.add_subplot(111)
        
        self.isRecording = False


        global CCounter
        CCounter = 0
        global listImages
        listImages = []
        
        global displayEvery
        displayEvery =int(self.spinBoxBSR.text())

        global labelCamera
        labelCamera = self.labelCamera

        self.cq = CameraQThread()

        self.ax = self.canvas.figure.add_subplot(111)

        #self.CameraQThread.start()
        #self.FetchingThreadClass = FetchingThreadClass(self)
        #self.FetchingThreadClass.run()


        #metadata
        self.dirFolder = "C:\\Users\\cmtech\Documents\\PythonScripts\\"
        self.dirFolderE = "C:\\Users\\cmtech\Documents\\Out\\"

        #Reload the form
        self.reloadForm()

        self.stopCameraWritingThread = True
        self.isViewing = False
        
        self.allowReplayOutside = True
    
    def updateToDisplay(self):
        
        global displayECG
        selRow = self.listWidgetView.currentRow()
        if selRow == 0 : 
            displayECG = True 
        else : 
            displayECG = False 
    
    def updateBSR(self):
        self.displayEvery = int(self.spinBoxBSR.text())
        global displayEvery
        displayEvery = self.displayEvery
    
    def updateUsedDisk(self) :
        obj_Disk = psutil.disk_usage('/')
        free =(obj_Disk.free / (1024.0 ** 3))
        oneMin = 1.5
        av = truediv(free,oneMin)
        self.labelStorage.setText(str(round(av))+" Min Available")
               
    def updateFPS(self):
        global recordingFPS
        recordingFPS = int(self.spinBoxFPS.text())
    
    def updateDPS(self):
        global recordingDPS
        recordingDPS = int(self.spinBoxDPS.text())
        
        #stop old Bio thread
        global Bio
        Bio.stopThread()
        
        isUpdated=False
        while not isUpdated : 
            app.processEvents()
            try :
                #start new thread
                Bio = BioThread(self)
                Bio.startThread()
                isUpdated = True
            except : 
                print('failed to reload')
    
    def getFileName(self,fileName):
        head, tail = os.path.split(fileName)
        return tail;
    
    
    def getDirName(self,fileName):
        head, tail = os.path.split(fileName)
        return head;
    
    
    def transferToIn(self):
        selRow = self.listWidgetE.currentRow()
        meta = self.metaDataE[selRow]
        
        csvFile = meta[0]
        npyFile = meta[1]
        metaFile = meta[2]
        
        dirName = os.path.dirname(meta[0])
        
        #print(str(dirName.split('\\')[-1]))
        ptName = str(dirName.split('\\')[-1])
        newFolder = self.dirFolder+ptName+"\\"
        
        #print(newFolder)
        #print(meta)
        self.sendInfo(dirName+'->'+newFolder)
        #return
        #first create the folder
        if not os.path.exists(newFolder) :
            os.makedirs(newFolder)
            os.makedirs(newFolder+"\\imgs\\")
        
        #second saving
        self.sendInfo("Now transferring the files")
        #CSV
        newCsvFile = newFolder+self.getFileName(csvFile)
        
        with open(newCsvFile, mode='w') as cf:
            cfWriter = csv.writer(cf, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
            #now read the image and make new csv
            with open(csvFile) as csvfile :
                csvReader  = csv.reader(csvfile, delimiter = ',', quotechar = '|')
                for row in csvReader :
                    #print(row)
                    
                    oldName = row[0]
                    fileName = newFolder+"\\imgs\\"+self.getFileName(oldName)
                    time = row[1]
                    
                    #print([fileName,time])
                    cfWriter.writerow([fileName,time])
                    os.rename(oldName, fileName)
        
        #print(metaFile,npyFile,newCsvFile)
        #return
        #txt
        os.rename(metaFile, newFolder+self.getFileName(metaFile))
        
        #npy
        os.rename(npyFile, newFolder+self.getFileName(npyFile))
        #self.dirFolderE = "C:\\Users\\cmtech\Documents\\Out\\"
        
        #delete
        shutil.rmtree(dirName) 
        
        self.sendInfo('Transfer completed')
        
        self.updateList()
        self.updateListE()
    

    def transferToEx(self):
        selRow = self.listWidget.currentRow()
        meta = self.metaData[selRow]
        
        csvFile = meta[0]
        npyFile = meta[1]
        metaFile = meta[2]
        
        dirName = os.path.dirname(meta[0])
        
        #print(str(dirName.split('\\')[-1]))
        ptName = str(dirName.split('\\')[-1])+'_backup\\'
        
        newFolder = self.dirFolderE+ptName
        
        print(newFolder)
        print(meta)
        
        #first create the folder
        if not os.path.exists(newFolder) :
            os.makedirs(newFolder)
            os.makedirs(newFolder+"\\imgs\\")
        
        #second saving
        self.sendInfo("Now transferring the files")
        #CSV
        newCsvFile = newFolder+self.getFileName(csvFile)
        
        with open(newCsvFile, mode='w') as cf:
            cfWriter = csv.writer(cf, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
            #now read the image and make new csv
            with open(csvFile) as csvfile :
                csvReader  = csv.reader(csvfile, delimiter = ',', quotechar = '|')
                for row in csvReader :
                    #print(row)
                    
                    oldName = row[0]
                    fileName = newFolder+"\\imgs\\"+self.getFileName(oldName)
                    time = row[1]
                    
                    #print([fileName,time])
                    cfWriter.writerow([fileName,time])
                    os.rename(oldName, fileName)
    
        #txt
        os.rename(metaFile, newFolder+self.getFileName(metaFile))
        
        #npy
        os.rename(npyFile, newFolder+self.getFileName(npyFile))
        #self.dirFolderE = "C:\\Users\\cmtech\Documents\\Out\\"
        
        #delete
        shutil.rmtree(dirName) 
        
        self.sendInfo('Transfer completed')
        
        self.updateList()
        self.updateListE()
    
    def sendInfo(self,text):
        self.labelInfo.setText(text)

    def delSinglePatient(self):
        qm = QtGui.QMessageBox
        ret = qm.question(self,'', "Are you sure to delete this record", qm.Yes | qm.No)

        if ret == qm.No : 
            return 
        
        if(not self.selectExternal): 
            selRow = self.listWidget.currentRow()
            folderName = os.path.dirname(self.metaData[selRow][0])
            updateIn = True
        else : 
            selRow = self.listWidgetE.currentRow()
            folderName = os.path.dirname(self.metaDataE[selRow][0])
            updateIn = False 
        #print(folderName)
        if False : 
            os.rename(folderName, folderName+'-DEL')
        else : 
            shutil.rmtree(folderName)
        if updateIn : 
            self.updateList()
        else : 
            self.updateListE()
        self.noImage()

    def getListInfoE(self):
        self.selectExternal = True
        
        selRow = self.listWidgetE.currentRow()
        self.listWidget.clearSelection()
        self.listWidget.clearFocus()

        self.csvTemp = self.metaDataE[selRow][0]
        with open(self.metaDataE[selRow][0]) as csvfile :
            csvReader  = csv.reader(csvfile, delimiter = ',', quotechar = '|')
            i = 0
            for row in csvReader :
                print(row)
                data = row[0]
                i+=1
                if i > 2 :
                    break
        #print(data)
        img = cv2.imread(data)
        h, w, c = img.shape

        date = datetime.datetime.strptime(str(row[1]), '%Y-%m-%d %H:%M:%S.%f')

        bytesPerLine = 3 * w
        qImg = QtGui.QImage(img.data, w, h, bytesPerLine, QtGui.QImage.Format_RGB888).rgbSwapped()
        pixmap = QtGui.QPixmap.fromImage(qImg)
        labelCamera.setPixmap(pixmap)
        self.isReplaying = False
        
        if self.allowReplayOutside : 
            self.graphBio(self.metaDataE[selRow][1])
        
    def getListInfo(self):
        self.selectExternal = False
        selRow = self.listWidget.currentRow()
        #self.turnOffMachine()
        
        self.listWidgetE.clearSelection()
        self.listWidgetE.clearFocus()

        self.csvTemp = self.metaData[selRow][0]
        with open(self.metaData[selRow][0]) as csvfile :
            csvReader  = csv.reader(csvfile, delimiter = ',', quotechar = '|')
            i = 0
            for row in csvReader :
                print(row)
                data = row[0]
                i+=1
                if i > 2 :
                    break
        #print(data)
        img = cv2.imread(data)
        h, w, c = img.shape

        date = datetime.datetime.strptime(str(row[1]), '%Y-%m-%d %H:%M:%S.%f')

        bytesPerLine = 3 * w
        qImg = QtGui.QImage(img.data, w, h, bytesPerLine, QtGui.QImage.Format_RGB888).rgbSwapped()
        pixmap = QtGui.QPixmap.fromImage(qImg)
        labelCamera.setPixmap(pixmap)
        self.isReplaying = False
        
        self.graphBio(self.metaData[selRow][1])

    def setPatientButtons(self,isReplaying):
        self.pushButtonDel.setEnabled(not isReplaying)
        self.pushButtonToIn.setEnabled(not isReplaying)
        self.pushButtonToEx.setEnabled(not isReplaying)
        self.pushPlayback.setEnabled(not isReplaying)
        self.listWidget.setEnabled(not isReplaying)

    def replay(self):
        if self.isReplaying : 
            self.stopReplay()
            self.isReplaying = False
            self.pushButtonPlot.setText("Play")
        else :  
            self.doReplay()
            self.isReplaying = True
            self.pushButtonPlot.setText("Stop")
        self.setPatientButtons(self.isReplaying)
    
    def stopReplay(self):
        self.VIQ.terminate()
        self.VBQ.terminate()
        self.timerReplayImage.stop()
        self.timerReplayBio.stop()
        self.endIR = True
        self.endBR = True
        self.pushButtonPlot.setText("Play")
        
    def doReplay(self):
        #first get the image list and time, calculate fps
        self.labelInfo.setText('Now Replaying')
        listImgs = []
        listTimes = []
        dateStart = None
        dateEnd = None
        
        print(self.csvTemp)
        
        '''if (self.listWidget.selectedItems().size() != 0) : 
            csvData = self.csvTemp
            bioData = self.tempBio
        else : 
            csvData = self.csvTempE
            bioData = self.tempBioE'''
        
        with open(self.csvTemp) as csvfile:
            csvReader  = csv.reader(csvfile, delimiter = ',', quotechar = '|')
            for row in csvReader:
                listImgs.append(row[0])
                #print(row[0],row[1])
                try :
                    dateD = datetime.datetime.strptime(str(row[1]), '%Y-%m-%d %H:%M:%S.%f')
                except :
                    dateD = datetime.datetime.strptime(str(row[1]), '%Y-%m-%d %H:%M:%S')
                    #print(dateD)

                listTimes.append(dateD)
                if dateStart is None :
                    dateStart = dateD
                dateEnd = dateD

        print(dateStart,'-',dateEnd)
        FPS = truediv(len(listImgs),(dateEnd - dateStart).total_seconds())
        print('FPS was ',FPS)

        #the bio
        time1 = self.tempBio[0][0]#'2012-10-05 04:45:18'
        time2 = self.tempBio[0][-1]#'2012-10-05 04:44:13'
        print(time1)
        dt = np.datetime64(time1) - np.datetime64(time2)
        DPS = truediv(len(self.tempBio[0]),(time2 - time1).item().total_seconds())
        print(time1,'-',time2)
        print('DPS was ',DPS)
        
        
        self.labelInfo.setText('FPS was '+str(FPS)+'/DPS was '+str(DPS))

        #first find the common starting point.
        time1I = np.datetime64(dateStart)
        time2I = np.datetime64(dateEnd)

        print(time1,time1I)

        istart = [0,0]
        iend = [len(listImgs)-1,len(self.tempBio[0])-1]

        if time1 < time1I :
            print('bio is started earlier')
            for i in range(0,len(self.tempBio[0])):
                bioTime = self.tempBio[0][i]
                if bioTime >= time1I:
                    istart[1] = i
                    print('starting img found',bioTime)
                    break
        else :
            print('img is started earlier')
            for i in range(0,len(listImgs)):
                imgTime = listTimes[i]
                if np.datetime64(imgTime) >= time1:
                    istart[0] = i
                    print('starting bio found',np.datetime64(imgTime))
                    break

        if time2 > time2I :
            print('bio is ended earlier')
            for i in range(len(listTimes)-1,0,-1):
                imgTime = listTimes[i]
                if np.datetime64(imgTime) <= time2I:
                    iend[0] = i
                    print('ending img found',np.datetime64(imgTime))
                    break
        else :
            print('img is ended earlier')
            for i in range(len(self.tempBio[0])-1,0,-1):
                bioTime = self.tempBio[0][i]
                if bioTime <= time2I:
                    iend[1] = i
                    print('ending bio found',bioTime)
                    break

        print(istart,listTimes[istart[0]],self.tempBio[0][istart[1]])
        print(iend,listTimes[iend[0]],self.tempBio[0][iend[1]])

        self.toDisplayBioData = np.stack([self.tempBio[1][istart[1]:iend[1]],self.tempBio[2][istart[1]:iend[1]]])
        self.toDisplayImgData = listImgs[istart[0]:iend[0]]

        self.toDisplayBioTime = self.tempBio[0][istart[1]:iend[1]]
        self.toDisplayImgTime = listTimes[istart[0]:iend[0]]

        print('from',len(listImgs),len(self.tempBio[0]))
        print('to',len(self.toDisplayImgData),self.toDisplayBioData.shape)

        FPS = truediv(len(self.toDisplayImgData),(self.toDisplayImgTime[-1] - self.toDisplayImgTime[0]).total_seconds())
        DPS = truediv(len(self.toDisplayBioData[0]),(self.toDisplayBioTime[-1] - self.toDisplayBioTime[0]).item().total_seconds())

        print('New FPS : ', FPS)
        print('New DPS : ',DPS)
        
        self.labelInfo.setText('Now replaying...')

        #now define fps and dps for displaying
        global displayFPS
        displayFPS = 30#int(round(truediv(FPS,2)))#30
        #displayFPS = self.samplingDisplayFPS

        global displayDPS
        displayDPS = 100#int(round(truediv(DPS,10)))#100
        #displayDPS = self.samplingDisplayDPS
        
        
        print('dfps',displayFPS,'ddps',displayDPS)
        
        #now sample it
        self.timerReplayImage = QtCore.QTimer(self)
        self.timerReplayImage.timeout.connect(self.checkIR)
        self.timerReplayImage.start(1000 / displayFPS)


        self.timerReplayBio = QtCore.QTimer(self)
        self.timerReplayBio.timeout.connect(self.checkBR)
        self.timerReplayBio.start(1000 / displayDPS)

        global toDisplayBioData
        global toDisplayBioTime
        
        toDisplayBioData = self.toDisplayBioData
        toDisplayBioTime = self.toDisplayBioTime

        global toDisplayImgData
        global toDisplayImgTime
        
        toDisplayImgData = self.toDisplayImgData
        toDisplayImgTime = self.toDisplayImgTime

        self.runningIndexImage = 0
        self.runningIndexBio = 0

        global stepImage, stepBio
        stepImage = int(round(truediv(FPS,displayFPS)))
        stepBio = int(round(truediv(DPS,displayDPS)))

        self.visReplay()
        self.bioReplay()
        self.endIR = False
        self.endBR = False

    def checkIR(self):
        if self.VIQ.getStatus():
            self.VIQ.terminate()
            self.timerReplayImage.stop()
            self.labelInfo.setText('End of Image Data')
            self.endIR = True
            if self.endBR : 
                self.setPatientButtons(False)
                self.isReplaying = False
                self.pushButtonPlot.setText("Play")

    def checkBR(self):
        if self.VBQ.getStatus():
            self.VBQ.terminate()
            self.timerReplayBio.stop()
            self.labelInfo.setText('End of Bio Data')
            self.endBR = True
            if self.endIR : 
                self.setPatientButtons(False)
                self.isReplaying = False
                self.pushButtonPlot.setText("Play")

    def visReplay(self):
        self.VIQ = visImageThread()
        self.VIQ.start()
        self.timerReplayImage.start()

        '''theIndex = self.runningIndexImage*stepImage
        if theIndex < len(self.toDisplayImgData):
            self.runningIndexImage+= 1
            self.updateVisReplay(cv2.imread(self.toDisplayImgData[theIndex]))
        else :
            self.timerReplayImage.stop()
            self.runningIndexImage = 0
        self.runningIndexImage+=1'''

    def bioReplay(self):
        self.VBQ = visBioThread()
        self.VBQ.start()
        self.timerReplayBio.start()
        '''theIndex = self.runningIndexBio*self.stepBio
        if theIndex < len(self.toDisplayBioData[0]):
            self.runningIndexBio+= 1
            self.updateGraphReplay([self.toDisplayBioData[0][theIndex],self.toDisplayBioData[0][theIndex]])
        else :
            self.timerReplayBio.stop()
            self.runningIndexBio = 0
        self.runningIndexBio+=1'''


    def adjustPlayback(self):
        print(self.isViewing)
        if self.isViewing :
            self.isViewing = False
            self.pushPlayback.setText('Enter Playback')
            self.groupBoxPatients.setEnabled(False)
            self.groupBox.setEnabled(True)
            self.turnOnMachine()
            self.noImage()
        else :
            self.isViewing = True
            self.pushPlayback.setText('Leave Playback')
            self.groupBoxPatients.setEnabled(True)
            self.groupBox.setEnabled(False)
            self.turnOffMachine()
        print('after',self.isViewing)

    def setButton(self,isRecording):
        self.pushPlayback.setEnabled(not isRecording)
        self.pushButtonStartRecording.setEnabled(not isRecording)
        self.pushButtonExit.setEnabled(not isRecording)
        #self.groupBoxMisc.setEnabled(not isRecording)
        self.pushButtonStopRecording.setEnabled(isRecording)

    def reloadForm(self) :
        self.updateList()
        self.updateListE()
        self.lineEditPN.setText('XXX')
        self.groupBoxPatients.setEnabled(False)#!#
        self.setButton(False)
        self.isViewing = False

    def updateListE(self):
        self.metaDataE = []
        self.listWidgetE.clear()

        listFolder = []
        for x in os.listdir(self.dirFolderE ):
            if os.path.isdir(self.dirFolderE+'\\'+x) and 'DEL' not in (x) and 'Pat' in (x):
                listFolder.append(self.dirFolderE+'\\'+x)
        
        print(listFolder)
        listFolder.sort()
        if len(listFolder) <=0:
            self.listWidgetE.addItem("No Data")
        else:
            for directory in listFolder:
                for y in os.listdir(directory) :
                    if '.npy' in y:
                        bioName = directory+"\\"+y
                    if '.txt' in y:
                        fileName = directory+"\\"+y
                    if '.csv' in y:
                        imgCsvName = directory+"\\"+y

                basicName = str(directory.split('\\')[-1])
                md = [line.rstrip() for line in open(fileName,'r')]
                if len(md) > 0:
                    print(md,fileName)
                    ptNumber = md[0].split(',')
                    ptStartA = md[1].split(',')
                    ptEndA = md[2].split(',')
                    print(ptNumber,ptStartA,ptEndA)
                    print(ptNumber[1],ptStartA[1],ptEndA[1])
                    basicName+="-["+ptNumber[1]+"]"

                    #tm_year=9999, tm_mon=12, tm_mday=31, tm_hour=23, tm_min=59, tm_sec=59, tm_wday=4, tm_yday=365, tm_isdst=-1
                    st = float(ptStartA[1])
                    en = float(ptEndA[1])
                    dur = str(round(abs(st - en)))

                    startTime  = datetime.datetime.fromtimestamp(st).timetuple()
                    endTime  = datetime.datetime.fromtimestamp(en).timetuple()
                    basicName+="--["+str(startTime.tm_mday)+"/"+str(startTime.tm_mon)+"/"+str(startTime.tm_year)+" "+str(startTime.tm_hour)+":"+str(startTime.tm_min)+"]["+dur+" Sec]"

                    self.metaDataE.append([
                        imgCsvName,#csv
                        bioName,#bio
                        fileName#meta
                    ])
                print(fileName)
                self.listWidgetE.addItem(basicName)


    def updateList(self):
        self.metaData = []
        self.listWidget.clear()

        listFolder = []
        for x in os.listdir(self.dirFolder ):
            if os.path.isdir(self.dirFolder+'\\'+x) and 'DEL' not in (x) and 'Pat' in (x):
                listFolder.append(self.dirFolder+'\\'+x)

        listFolder.sort()
        print(listFolder)
        if len(listFolder) <=0:
            self.listWidget.addItem("No Data")
        else:
            for directory in listFolder:
                for y in os.listdir(directory) :
                    if '.npy' in y:
                        bioName = directory+"\\"+y
                    if '.txt' in y:
                        fileName = directory+"\\"+y
                    if '.csv' in y:
                        imgCsvName = directory+"\\"+y

                basicName = str(directory.split('\\')[-1])
                #fileName  = self.dirFolder + 'Patient_' + str(j)+'\\meta_'+str(j)+".txt"
                #imgCsvName  = self.dirFolder + 'Patient_' + str(j)+'\\listImages_'+str(j)+".csv"
                #bioName  = self.dirFolder + 'Patient_' + str(j)+'\\bio_'+str(j)+".npy"

                #Read the metaData
                md = [line.rstrip() for line in open(fileName,'r')]
                if len(md) > 0:
                    print(md,fileName)
                    ptNumber = md[0].split(',')
                    ptStartA = md[1].split(',')
                    ptEndA = md[2].split(',')
                    print(ptNumber,ptStartA,ptEndA)
                    print(ptNumber[1],ptStartA[1],ptEndA[1])
                    basicName+="-["+ptNumber[1]+"]"

                    #tm_year=9999, tm_mon=12, tm_mday=31, tm_hour=23, tm_min=59, tm_sec=59, tm_wday=4, tm_yday=365, tm_isdst=-1
                    st = float(ptStartA[1])
                    en = float(ptEndA[1])
                    dur = str(round(abs(st - en)))

                    startTime  = datetime.datetime.fromtimestamp(st).timetuple()
                    endTime  = datetime.datetime.fromtimestamp(en).timetuple()
                    basicName+="--["+str(startTime.tm_mday)+"/"+str(startTime.tm_mon)+"/"+str(startTime.tm_year)+" "+str(startTime.tm_hour)+":"+str(startTime.tm_min)+"]["+dur+" Sec]"

                    self.metaData.append([
                        imgCsvName,#csv
                        bioName,#bio
                        fileName#meta
                    ])


                #print(md[0])
                print(fileName)
                self.listWidget.addItem(basicName)

    def starting(self):
        self.cq.start()

    def stopping(self):
        self.cq.terminate()

    def graphBio(self,filedata):
        self.labelInfo.setText("Opening the Data, it may take some time")
        filedata = str(filedata)
        data = np.load(filedata)
        
        #data = data[::4]
        #self.tempBio =data
        print(data.shape)

        datetime = data[:, 1]

        dataB = np.stack(data[:, 0])
        print(dataB.shape)

        ecg = dataB[:,0]
        eda = dataB[:,1]

        self.tempBio =[datetime,ecg,eda]

        '''
        datetime = data[:, 1]
        data = data[:, 0]
        ecg = []
        eda = []
        
        for i in range(data.shape[0]):
            sample1 = data[i][0]
            ecg.append(sample1)
            sample2 = data[i][1]
            eda.append(sample2)'''


        dt = datetime[-1] - datetime[0]
        seconds = dt.item().total_seconds()
        time = np.linspace(0, seconds, len(ecg))

        self.ax.clear()
        self.ax.plot(time, ecg, '-')
        self.canvas.draw()
        
        
        if self.displayEDA :
            self.ax2.clear()
            self.ax2.plot(time, eda, '-')
            self.canvasEDA.draw()


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

        #print(ecg)
        #print(len(ecg))

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
        #QMessageBox.information(None, 'Installer', 'Installation complete.', QMessageBox.Ok, QMessageBox.Ok)
        # display it to the qt
        self.close()


    def turnOnMachine(self):
        '''global camera
        camera = CameraThread()
        global Bio
        Bio = BioThread()
        camera.startThread()
        Bio.startThread()'''
        '''self.timer.start(100)
        self.timerG.start(100)'''
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.updateVis)
        self.timer.start(1000 / 50)

        self.timerG = QtCore.QTimer(self)
        self.timerG.timeout.connect(self.updateGraph)
        self.timerG.start(1000 / 500)

        self.toRefresh = True
        runningCount = 0
        visRunningCount = 0
        visBio=[]

    def turnOffMachine(self):
        runningCount = 0
        #camera.stopThread()
        #Bio.stopThread()
        self.timer.stop()
        self.timerG.stop()
        self.toRefresh = False
        self.noImage()
    
    def noImage(self):
        global gvE
        img = cv2.imread(self.dirFolder+"noimage.png")
        h, w, c = img.shape
        bytesPerLine = 3 * w
        try :
            self.qImg = QtGui.QImage(img.data, w, h, bytesPerLine, QtGui.QImage.Format_RGB888).rgbSwapped()
            self.pixmap = QtGui.QPixmap.fromImage(self.qImg)
            labelCamera.setPixmap(self.pixmap)
        except :
            print('problem on drawing')
        pass
        gvECG.clear()
        self.ax.clear()
        self.canvas.draw()
    
        
    def updateVisReplay(self,img):
        h, w, c = img.shape
        bytesPerLine = 3 * w
        try :
            self.qImg = QtGui.QImage(img.data, w, h, bytesPerLine, QtGui.QImage.Format_RGB888).rgbSwapped()
            self.pixmap = QtGui.QPixmap.fromImage(self.qImg)
            labelCamera.setPixmap(self.pixmap)
        except :
            print('problem on drawing')
        pass


    def updateGraphReplay(self,bio):
        global runningCount,visRunningCount
        global gvECG
        runningCount+=1
        visRunningCount+=1

        displayEvery = 100

        if visRunningCount % (displayEvery * 2) == 0:
            visBio = visBio[visRunningCount - displayEvery:]
            visRunningCount = 0

        visBio.append([runningCount, bio[0], bio[1]])  # i,time,ecg,eda
        vData = np.asarray(visBio)

        x = vData[:,0]  # [runningCount]#random.normal(size = 10)
        yECG = vData[:,1]
        yEDA = vData[:,2]

        if runningCount > displayEvery:
            left = runningCount - displayEvery
            right = runningCount
        else:
            left = 0
            right = runningCount

        gvECG.clear()
        gvECG.setYRange(np.min(yECG), np.max(yECG))
        gvECG.setXRange(left, right)
        gvECG.plot(x,yECG)

    def updateVis(self):
        #print('updating')
        data = camera.temp
        img = data[0]
        self.labelTimeImage.setText(str(data[1]))

        h, w, c = img.shape
        bytesPerLine = 3 * w
        try :
            self.qImg = QtGui.QImage(img.data, w, h, bytesPerLine, QtGui.QImage.Format_RGB888).rgbSwapped()
            self.pixmap = QtGui.QPixmap.fromImage(self.qImg)
            labelCamera.setPixmap(self.pixmap)
        except :
            print('problem on drawing')

        bio = Bio.temp
        
        self.labelECG.setText(str(bio))
        self.labelTimeBio.setText(str(bio[1]))

        self.labelSpeed.setText('FPS:'+str(round(camera.fps))+' - DPS:'+str(round(Bio.fps)))
        if self.isRecording :
            self.labelInfo.setText(
                'Now Recording...,' + str(round(abs(self.startTimeR - time.time()))) + ' Seconds Elapsed')
        #self.updateGraph()
        #t = Thread(target=self.updateGraph, args=()).start()
        #t = Thread(target=self.updateGraphOptim, args=()).start()
        pass

    def updateGraphOptim(self):
        runningCount+=1
        visRunningCount+=1
        bio = Bio.temp

        #if visRunningCount % (self.displayEvery * 2) == 0:
            #visBio = visBio[visRunningCount - self.displayEvery:]
            #visRunningCount = 0

        data = [runningCount, bio[1], bio[0][0], bio[0][1]]  # i,time,ecg,eda

        # print(vData.shape)
        x = [data[0]]  # [runningCount]#random.normal(size = 10)
        yECG = [data[2]]
        yEDA = [data[3]]

        if runningCount > self.displayEvery:
            left = runningCount - self.displayEvery
            right = runningCount
        else:
            left = 0
            right = runningCount

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

        bio = Bio.temp
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

        bio = Bio.temp
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
        global visRunningCount,runningCount,visBio
        runningCount+=1
        visRunningCount+=1

        bio = Bio.temp
        
        global displayEvery,displayECG

        if visRunningCount % (displayEvery * 2) == 0:
            visBio = visBio[len(visBio) - displayEvery:]
            visRunningCount = 0

        visBio.append([runningCount, bio[1], bio[0][0], bio[0][1]])  # i,time,ecg,eda
        vData = np.asarray(visBio)

        x = vData[:,0]  # [runningCount]#random.normal(size = 10)
        yECG = vData[:,2]
        yEDA = vData[:,3]

        if runningCount > displayEvery:
            left = runningCount - displayEvery
            right = runningCount
        else:
            left = 0
            right = runningCount
        
        '''
        if displayECG : 
            self.gvECG.clear()
            self.gvECG.setYRange(np.min(yECG), np.max(yECG))
            self.gvECG.setXRange(left, right)
            #print(yECG.shape)
            self.gvECG.plot(x,yECG)
        else : 
            self.gvEDA.clear()
            self.gvEDA.setYRange(np.min(yEDA),np.max(yEDA))
            self.gvEDA.setXRange(left,right)
            self.gvEDA.plot(x,yEDA)
        '''
        
        if displayECG : 
            data = yECG 
        else : 
            data = yEDA
        
        self.gvECG.clear()
        self.gvECG.setYRange(np.min(data),np.max(data))
        self.gvECG.setXRange(left,right)
        self.gvECG.plot(x,data)
        
        # self.ax.set_ylim([np.min(yECG),np.max(yECG)])
        # self.ax.set_xlim([left,right])
        # self.ax.plot(x, yECG, '-')
        # self.canvas.draw()


    def showlcd(self):
        text =datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.timeData.setText(text)
        self.updateUsedDisk() 

    def startRecordAllModality(self):
        j = 0
        directory = self.dirFolder+'Patient_' + str(j)
        if not os.path.exists(directory):
            os.makedirs(directory)
            os.makedirs(directory+'\\imgs')
        else:
            while os.path.exists(self.dirFolder+'Patient_' + str(j) ):
                j += 1
            directory = self.dirFolder+'Patient_' + str(j)
            os.makedirs(directory)
            os.makedirs(directory+'\\imgs')

        global dirName;
        dirName = directory  +'\\imgs'
        
        global csvName;
        csvName = directory + '/listImages_' + str(j) + '.csv'
        self.bioName = directory + '/' + 'bio_' + str(j) + '.npy'
        self.metafile = directory + '/meta_' + str(j) + '.txt'
        self.startRecordCamera()
        self.startRecordBio()
        self.setButton(True)
        self.labelInfo.setText('Now Recording...')
        self.startTimeR = time.time()
        self.isRecording = True

    def stopRecordAllModality(self):
        endTime = time.time()
        totalTime = endTime-self.startTimeR

        limages = len(listImages)
        self.stopRecordCamera()

        lbios = self.stopRecordBio()
        self.setButton(False)

        fps = round(truediv(limages,totalTime))
        dps = round(truediv(lbios,totalTime))

        file = open(self.metafile, 'w')
        file.write('addName,'+str(self.lineEditPN.text())+'\n')
        file.write('startTime,'+str(self.startTimeR)+'\n')
        file.write('endTime,'+str(endTime)+'\n')
        file.close()

        self.labelInfo.setText(str(limages)+' Images and '+str(lbios)+' ECG/EDA Saved. For '+str(totalTime)+' ['+str(fps)+' FPS/'+str(dps)+' DPS]')
        self.isRecording  = False
        self.reloadForm()

    def startRecordCamera(self):

        global CCounter
        CCounter = 0
        global listImages
        listImages = []

        self.cq.start()
        #self.fps = 1200
        #self.timerCRecorder.start(1000/(self.fps))#120fps
        '''self.stopCameraWritingThread = False
        t = Thread(target=self.fetchSaveImage(), args=()).start()'''

    def stopRecordCamera(self):
        global listImages,csvName
        self.cq.terminate()
        #self.timerCRecorder.stop()
        #self.stopCameraWritingThread = True
        #print(self.listImages)
        #write csv
        
        t = Thread(target=self.recordToCSV, args=()).start()
        CCounter = 0
        
    def recordToCSV(self):
        global listImages,csvName
        with open(csvName, mode='w') as cf:
            cfWriter = csv.writer(cf, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for data in listImages:
                cfWriter.writerow([data[0], data[1]])

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
        Bio.startRecording()
        pass
        self.bps = 1500 #1000 acq per second. mean running every .001 = dps*1000
        self.timerBRecorder.start(1000/self.bps)#1000fps

    def stopRecordBio(self):
        Bio.stopRecording()
        #write npy
        global listBios;
        listBios = Bio.retrieveResult()
        saved = len(listBios)
        
        t = Thread(target=self.saveBioToNpy(), args=()).start()
        
        self.BCounter = 0
        return(saved)

        pass
        self.timerBRecorder.stop()
    
    def saveBioToNpy(self):
        global listBios
        np.save(self.bioName, np.stack(listBios))
        # print('saved : ',len(self.listImages))

    def fetchSaveBio(self):
        pass
        self.listBios.append(Bio.temp)


    def startRecording(self):
        Bio.startRecording()
        camera.startRecording()
        self.timerRecorder.start(5000)#save every 1000/10 second

    def stopRecording(self):
        Bio.stopRecording()
        camera.stopRecording()
        self.timerRecorder.stop()


    def saveBioToFolder(self,listData):
        for x in listData:
            cv2.imwrite(str(x[0]+'.png'), x[0][0])

    def closeEvent(self, event):
        print "Exiting"

        camera.stopThread()
        Bio.stopThread()
        event.accept()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
