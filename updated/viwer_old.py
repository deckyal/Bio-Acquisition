import os
from os import getcwd
import sys
from plux_functions import *
from PyQt4 import QtCore, QtGui, uic
import numpy as np, random
from pypylon import pylon
import cv2
import csv
from threading import Thread
import matplotlib
from time import sleep

matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar

qtCreatorFile = "viewer.ui"  # Enter file here.

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


from PyQt4.QtCore import QThread


class CameraThread:
    def __init__(self):
        self.stream = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        self.data = []
        self.temp = None
        self.toStopThread = True
        self.nowRecording = True

        self.converter = pylon.ImageFormatConverter()

        # converting to opencv bgr format
        self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

    def clean(self):
        self.data = []

    def startThread(self):
        self.stream.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        self.toStopThread = False
        Thread(target=self.update, args=()).start()
        return self

    def stopThread(self):
        self.toStopThread = True

    def update(self):
        while self.stream.IsGrabbing():
            if self.toStopThread:
                self.stream.StopGrabbing()
                return;
            else:
                grabResult = self.stream.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                if grabResult.GrabSucceeded():
                    # Access the image data
                    image = self.converter.Convert(grabResult)
                    self.temp = image.GetArray()
                grabResult.Release()
                print(self.temp)
                if self.nowRecording:
                    self.data.append(self.temp)

    def startRecording(self):
        self.nowRecording = True

    def stopRecording(self):
        self.nowRecording = False


class BioThread:
    def __init__(self):
        self.stream = MyDevice("BTH00:07:80:46:E0:64")
        self.data = []
        self.temp = None
        self.toStopThread = True
        self.nowRecording = True

    def clean(self):
        self.data = []

    def startThread(self):
        self.stream.start(1000, 0xFF, 16)
        self.toStopThread = False
        Thread(target=self.update, args=()).start()
        return self

    def stopThread(self):
        self.toStopThread = True

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
                print(self.temp)
                if self.nowRecording:
                    self.data.append(self.temp)

    def startRecording(self):
        self.nowRecording = True

    def stopRecording(self):
        self.nowRecording = False

class WebcamVideoThread(QThread):
    def __init__(self):
        QThread.__init__(self)
        self.stream = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        self.stream.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        #Thread(target=self.update, args=()).start()
        self.data = None

    def __del__(self):
        self.stream.StopGrabbing()
        self.wait()

    def run(self):
        # otherwise, read the next frame from the stream
        self.data = self.stream.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

class WebcamVideoStream:
    def __init__(self):

        self.stream = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        self.data = None
        # self.data = self.stream.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

        self.stopped = True

    def start(self):
        self.stopped = False
        # start the thread to read frames from the video stream
        self.stream.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        Thread(target=self.update, args=()).start()
        return self

    def update(self):
        # keep looping infinitely until the thread is stopped
        while True:
            # if the thread indicator variable is set, stop the thread
            if self.stopped:
                self.stream.StopGrabbing()
                return

            # otherwise, read the next frame from the stream
            self.data = self.stream.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

    def read(self):
        # return the frame most recently read
        return self.data

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True


class ECGStream:
    def __init__(self, src=0):

        self.stream = MyDevice("BTH00:07:80:46:E0:64")
        self.data = None
        # self.data = self.stream.read()

        self.stopped = True

    def start(self):
        # start the thread to read frames from the video stream
        self.stopped = False
        self.stream.start(1000, 0xFF, 16)
        Thread(target=self.update, args=()).start()
        return self

    def update(self):
        # keep looping infinitely until the thread is stopped
        while True:
            # if the thread indicator variable is set, stop the thread
            if self.stopped:
                self.stream.stop()
                self.stream.close()
                return

            # otherwise, read the next frame from the stream
            self.stream.loop()
            self.data = self.stream.inter

    def read(self):
        return self.data

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True


class MyApp(QtGui.QMainWindow, Ui_MainWindow):
    def setStop(self):
        self.toStop = True

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

    def acquire_BothT(self):
        self.camera = CameraThread()
        self.ECG = BioThread()  # MAC address of device
        # Grabing Continusely (video) with minimal delay


        self.camera.startThread()
        self.ECG.startThread()

        i = 0
        csvFile = 'test.csv'
        listName = []
        listECGData = []
        while True:
            grabResult = self.camera.read()
            grabECG = self.ecg.read()

            if grabResult.GrabSucceeded():
                # Access the image data
                image = converter.Convert(grabResult)
                img = image.GetArray()

                # display it to the qt
                h, w, c = img.shape
                bytesPerLine = 3 * w

                qImg = QtGui.QImage(img.data, w, h, bytesPerLine, QtGui.QImage.Format_RGB888).rgbSwapped()
                pixmap = QtGui.QPixmap.fromImage(qImg)
                self.labelCamera.setPixmap(pixmap)
                cv2.imwrite(str(i) + '.png', img)
                listName.append([str(i) + '.png', datetime.datetime.now()])

                self.labelECG.setText(str(grabECG))
                listECGData.append(grabECG)

                i += 1
                cv2.namedWindow('title', cv2.WINDOW_NORMAL)
                cv2.imshow('title', img)
                k = cv2.waitKey(1)
                if k == 27:
                    self.camera.stop()
                    self.ECG.stop()
                    break
            grabResult.Release()

        print('saving image data')
        # Releasing the resource
        with open(csvFile, mode='w') as cf:
            cfWriter = csv.writer(cf, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for data in listName:
                cfWriter.writerow([data[0], data[1]])
        print('saving ecg data')
        np.save('ecg.npy', np.asarray(listECGData))

        cv2.destroyAllWindows()

    def acquire_Both(self):
        j = 0
        directory = 'Patient_' + str(j)
        if not os.path.exists(directory):
            os.makedirs(directory)
        else:
            while os.path.exists("Patient_%s" % j):
                j += 1
            directory = 'Patient_' + str(j)
            os.makedirs(directory)

        # conecting to the first available camera
        camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())

        # Grabing Continusely (video) with minimal delay
        camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        converter = pylon.ImageFormatConverter()

        # converting to opencv bgr format
        converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        i = 0
        dev = MyDevice("BTH00:07:80:46:E0:64")  # MAC address of device
        props = dev.getProperties()
        print 'Properties:', props
        dev.start(2000, 0xFF, 16)  # 1000 Hz, ports 1-8, 16 bits

        csvFile = directory + '/test' + str(j) + '.csv'
        listName = []
        while True:
            grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

            if grabResult.GrabSucceeded():
                # Access the image data
                image = converter.Convert(grabResult)
                img = image.GetArray()

                # display it to the qt
                h, w, c = img.shape
                bytesPerLine = 3 * w

                qImg = QtGui.QImage(img.data, w, h, bytesPerLine, QtGui.QImage.Format_RGB888).rgbSwapped()
                pixmap = QtGui.QPixmap.fromImage(qImg)
                self.labelCamera.setPixmap(pixmap)
                cv2.imwrite(directory + '/' + str(i) + '.png', img)
                listName.append([directory + '/' + str(i) + '.png', datetime.datetime.now()])

                print(dev.loop())  # returns after receiving 10000 frames (onRawFrame() returns True)
                # print(dev.onRawFrame())
                # self.labelECG.setText(str(dev.data2))
                self.labelECG.setText(str(dev.inter))

                i += 1
                cv2.namedWindow('title', cv2.WINDOW_NORMAL)
                cv2.imshow('title', img)
                k = cv2.waitKey(1)
                if self.toStop:
                    j += 1
                if k == 27 or self.toStop:
                    self.toStop = False
                    break

            grabResult.Release()

        # Releasing the resource
        camera.StopGrabbing()
        with open(csvFile, mode='w') as cf:
            cfWriter = csv.writer(cf, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for data in listName:
                cfWriter.writerow([data[0], data[1]])

        dev.stop()
        dev.close()
        np.save(directory + '/' + 'ecg_' + str(j - 1) + '.npy', np.asarray(dev.data2))
        j += 1
        data = np.asarray(dev.data2)
        cv2.destroyAllWindows()

    def acquire_ECG(self):
        dev = None
        try:
            dev = MyDevice("BTH00:07:80:46:E0:64")  # MAC address of device
            props = dev.getProperties()
            print 'Properties:', props
            dev.start(1000, 0xFF, 16)  # 1000 Hz, ports 1-8, 16 bits
            print(dev.loop())  # returns after receiving 10000 frames (onRawFrame() returns True)
            # print(dev.onRawFrame())
            dev.stop()
            dev.close()
            print(dev.data2)
            self.labelECG.setText(str(dev.data2))
            np.save('ecg.npy', np.asarray(dev.data2))
        except Exception as e:
            print e
            if (dev):
                dev.close()

    def acquire_image(self):
        # conecting to the first available camera
        camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())

        # Grabing Continusely (video) with minimal delay
        camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        converter = pylon.ImageFormatConverter()

        # converting to opencv bgr format
        converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

        i = 0
        csvFile = 'test.csv'
        listName = []
        while camera.IsGrabbing():
            grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

            if grabResult.GrabSucceeded():
                # Access the image data
                image = converter.Convert(grabResult)
                img = image.GetArray()

                # display it to the qt
                h, w, c = img.shape
                bytesPerLine = 3 * w

                qImg = QtGui.QImage(img.data, w, h, bytesPerLine, QtGui.QImage.Format_RGB888).rgbSwapped()
                pixmap = QtGui.QPixmap.fromImage(qImg)
                self.labelCamera.setPixmap(pixmap)
                listName.append([str(i) + '.png', datetime.datetime.now()])
                # cv2.imwrite(str(i)+'.png',img)

                i += 1
                cv2.namedWindow('title', cv2.WINDOW_NORMAL)
                cv2.imshow('title', img)
                k = cv2.waitKey(1)
                if k == 27:
                    break
            grabResult.Release()

        # Releasing the resource
        camera.StopGrabbing()
        with open(csvFile, mode='w') as cf:
            cfWriter = csv.writer(cf, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for data in listName:
                cfWriter.writerow([data[0], data[1]])
        cv2.destroyAllWindows()

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        # self.pushButtonECG.clicked.connect(self.acquire_ECG)
        # self.pushButtonCamera.clicked.connect(self.acquire_image)
        self.pushButtonBoth.clicked.connect(self.acquire_Both)
        self.pushButtonPlot.clicked.connect(self.graph)
        self.addToolBar(NavigationToolbar(self.canvas, self))
        self.pushButtonT.clicked.connect(self.acquire_BothT)
        self.pushButtonStop.clicked.connect(self.setStop)
        self.toStop = False


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
