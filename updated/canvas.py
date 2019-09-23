import os
import sys
from plux_functions import * 
from PyQt4 import QtCore, QtGui, uic
import numpy as np
import csv
from PyQt4 import QtCore, QtGui, uic
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

class Canvas(FigureCanvas):
	def __init__(self,parent=None):
		self.figure = plt.figure()
		FigureCanvas.__init__(self, self.figure)
		self.setParent(parent)