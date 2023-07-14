# -*- coding: utf-8 -*-
"""
Created on Sat Oct 29 11:54:36 2022

@author: marvin
"""

import traceback
import CameraControl
import datetime
import time
# import bver_algorithm as Off
from Layout_signIn import Ui_Dialog
from PyQt5 import QtWidgets, Qt
from PyQt5.QtWidgets import QWidget, QFileDialog, QApplication
from inspect import currentframe, getframeinfo

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap
from Layout_camError import Error_Ui_Dialog
from Layout_nameFileParamter import nameParameterFileUiDialog
from Layout_confirmLaserOff import confirmLaserOffUi
from queue import Queue
import os
import keyboard

import bver_algorithm_auto_corner
import bver_algorithm_auto_lasercross
import cv2 as cv

from PyQt5.QtGui import QMouseEvent

cnt = 0

cam = CameraControl.camera

class GUI_functions(QWidget):

    def __init__(self):
       super().__init__()
        
       self.scale = 1   
       self.lastFrame = 1
       self.retryCnt = 0
       self.averageCnt = 0
           
       self.Timer = QTimer()
       self.Timer.setInterval(1)
       self.Timer.timeout.connect(self.update)
       self.Timer.start()
        
       self.Timer2 = QTimer()
       self.Timer2.setInterval(1000)
       self.Timer2.timeout.connect(self.rasptime)
       self.Timer2.start()
       
       self.q = Queue(maxsize=100)
       self.total_sum = 0
       
       self.enableMouseMove = False
       
       self.start_x = 0
       self.start_y = 0
       
    def getActualTime(self):
        """
        Retrieves the current date and time of the operating system.
        Returns
        -------
        rightdatetime : TYPE
            DESCRIPTION.

        """
        try:
            now = datetime.datetime.now()
            rightdatetime = now.strftime("%d.%m.%Y; %H:%M:%S; ")
            return rightdatetime
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to load current date and time. Backend, function in line: "
            self.ErrorOut.setText(self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
            
    def getActualTimeFilename(self):
        """
        Retrieves the current date and time of the operating system.
        Returns
        -------
        rightdatetime : TYPE
            DESCRIPTION.

        """
        try:
            now = datetime.datetime.now()
            rightdatetime = now.strftime("%d%m%Y%H%M%S")
            return rightdatetime
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to load current date and time for filename. Backend, function in line: "
            self.ErrorOut.setText(self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
    
    def update(self):
         """
         Allows to generate the Streams of frames and to display them on the aproppriate
         Qlabel in the interface.
         Every 5 frames the watchdog will signal a flashing light
         :return: Frame for Qlabel
         """
         try:
             start_time = time.time()
             global cnt
             cnt = cnt + 1
             
             if (CameraControl.cameraModel == 'VCXG-13M'):
                 Frame = CameraControl.getimageMono()
             else:
                 Frame = CameraControl.getimageBGR()
                 
             # Region of interest             
             self.Img = Frame.scaled(self.VideoStream.size() * self.scale)
             h = int(self.verticalScrollBar.value())
             w = int(self.horizontalScrollBar.value())
             moved = self.Img.copy(w, h, 750, 600)                         #Muss gleich sein wie die Werte in Layout.py in Zeile 61 und 62
             self.verticalScrollBar.setMaximum(abs(self.Img.height()-self.Img.height()*self.scale)/2)
             self.horizontalScrollBar.setMaximum(abs(self.Img.width()-self.Img.width()*self.scale)/2)
             self.verticalScrollBar.setPageStep(self.VideoStream.height()/self.scale)
             self.horizontalScrollBar.setPageStep(self.VideoStream.width()/self.scale)
             self.VideoStream.setPixmap(QPixmap.fromImage(moved))
             
             self.retryCnt = 0
             
             if cnt > 9999:
                 cnt = 0
             if cnt % 50 == 0: # Watchdogfrequenz
                 self.flashing()
                             
             fps = 1/(time.time()-start_time)
             
             self.averageCnt = self.averageCnt + fps
                          
             # Calculating fps
             self.q.put(fps)
             self.total_sum += fps
             if self.q.full():
                 average = self.total_sum / 100
                 # print(f"Current FPS: {average:.2f}")
                 self.total_sum -= self.q.get()
                 self.Framenumbers.setText(str(int(round(average,0))))  

             # # Disabling camera pictures
             # if average < 20: # Value has to be changed in error-message!
             #     self.VideoStream.setEnabled(False)
             #     self.ErrorOut.setText(self.getActualTime() + "Error: Fps value is under 1 (Fps too low).")
             # else:
             #     self.VideoStream.setEnabled(True)
                                                   
         except Exception as e:  
            print(type(e))
            traceback.print_exc()
            self.retryCnt = self.retryCnt + 1
            
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Camera disconnected. First: Check connection to camera. Second: Restart program/timer. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
            
            if self.retryCnt >= 5:
                self.windowError = QtWidgets.QDialog()
                self.uiE = Error_Ui_Dialog()
                self.uiE.setupErrorUi(self.windowError)
                self.windowError.show() 
                self.Timer.stop()
                cam.Disconnect()
                
                self.uiE.Hint1.setVisible(True)
                self.uiE.Hint2.setVisible(True)
                self.uiE.Hint3.setVisible(True)
                
                self.uiE.Retrybutton.clicked.connect(self.retryErrorUiClicked)
                
            else:
                print("hello2")
                self.windowError = QtWidgets.QDialog()
                self.uiE = Error_Ui_Dialog()
                self.uiE.setupErrorUi(self.windowError)
                self.windowError.show() 
                self.Timer.stop()
                cam.Disconnect()
                
                self.uiE.Hint1.setVisible(False)
                self.uiE.Hint2.setVisible(False)
                self.uiE.Hint3.setVisible(False)
                
                self.uiE.Retrybutton.clicked.connect(self.retryErrorUiClicked)

    def mousePressed(self, QMouseEvent):
        try:            
            self.start_x = QMouseEvent.x()
            self.start_y = QMouseEvent.y()
            # self.start_x = 1165 # For testing with pictures, coordinates of reference cross
            # self.start_y = 271  # For testing with pictures, coordinates of reference cross
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to get mouse coordinates. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
        
            if keyboard.is_pressed('shift'):
                try:
                    # self.laserImage = 'image0000020.png'
                    self.laserImage = CameraControl.getimageBGR()
                except:
                    frameinfo = getframeinfo(currentframe())
                    self.functionPlace = str(frameinfo.lineno)
                    self.text = "Error: Failed to get camera image for image processing. Backend, function in line: "
                    self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
                    self.updateLogFile(self.text, self.functionPlace)
                try:
                    self.xLaser, self.yLaser = bver_algorithm_auto_lasercross.mainLaserCrossDetection(self.laserImage, self.start_x, self.start_y)
                except:
                    frameinfo = getframeinfo(currentframe())
                    self.functionPlace = str(frameinfo.lineno)
                    self.text = "Error: Failed to detect the centre of the laser cross. Backend, function in line: "
                    self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
                    self.updateLogFile(self.text, self.functionPlace)
                try:
                    self.windowLaser = QtWidgets.QDialog()
                    self.uiL = confirmLaserOffUi()
                    self.uiL.setupErrorUi(self.windowLaser)
                    self.windowLaser.show() 
                    self.uiL.Retrybutton.clicked.connect(self.getMeasuringPhantomImage)
                except:
                    frameinfo = getframeinfo(currentframe())
                    self.functionPlace = str(frameinfo.lineno)
                    self.text = "Error: Failed to open information window 'Switch laser off'. Backend, function in line: "
                    self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
                    self.updateLogFile(self.text, self.functionPlace)
        else:
            self.enableMouseMove = True
    
    def getMeasuringPhantomImage(self):
        self.windowLaser.close()
        try:
            # AutoFeatureRegionSelector
            cam.f.AutoFeatureRegionSelector.SetString('BrightnessAuto')
            cam.f.AutoFeatureRegionMode.SetString('On')
            cam.f.AutoFeatureOffsetX.Set(self.start_x)
            cam.f.AutoFeatureOffsetY.Set(self.start_y)
            cam.f.AutoFeatureWidth.Set(400)
            cam.f.AutoFeatureHeight.Set(400)
            cam.f.AutoFeatureOffsetX.Set(cam.f.AutoFeatureOffsetX.GetMax() // 2 // cam.f.AutoFeatureOffsetX.GetInc() * cam.f.AutoFeatureOffsetX.GetInc()) # centered
            cam.f.AutoFeatureOffsetY.Set(cam.f.AutoFeatureOffsetY.GetMax() // 2 // cam.f.AutoFeatureOffsetY.GetInc() * cam.f.AutoFeatureOffsetY.GetInc()) # centered
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to activate and set AutoFeatureRegionSelector. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
        try:
            measuringArrayImage = CameraControl.getimageBGR()
            # measuringArrayImage = 'image0000021.png'
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to get camera image for image processing. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
        nameImage = self.getActualTimeFilename()
        try:
            distance = bver_algorithm_auto_corner.main(self.start_x, self.start_y, measuringArrayImage, self.laserImage, self.xLaser, self.yLaser, nameImage)
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to detect the centre of the reference cross. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
        try:
            self.TAxisReadOut.setPlainText(str(round(distance[1][1], 2)))
            self.UAxisReadOut.setPlainText(str(round(distance[1][0], 2)))
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to show offset values on GUI. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
        
    def mouseMoved(self, QMouseEvent):
        if self.enableMouseMove == True:
            self.current_x = QMouseEvent.x()
            self.current_y = QMouseEvent.y()
            self.delta_x = self.current_x - self.start_x
            self.delta_y = self.current_y - self.start_y
            # print(self.delta_x)
            # print(self.delta_y)
            self.verticalScrollBar.setValue(self.verticalScrollBar.value() - (self.delta_y / 8))
            self.horizontalScrollBar.setValue(self.horizontalScrollBar.value() - (self.delta_x / 8))
            
    def mouseReleased(self, QMouseEvent):
        print("Released")
        self.enableMouseMove = False
                
    def updateLogFile(self, new_text, placeOfFunction):
        """
        Enters the error messages in data/#LogFile.txt.
        Error messages are provided with the current time, the respective error text and the exact location of the function.
        If the file does not exist, a new one is created.

        Parameters
        ----------
        new_text : String
        placeOfFunction : String

        Returns
        -------
        None.

        """
        # Creating path of relative path to folder data
        absolutepath = os.path.abspath(__file__)  
        # Path of filedirectory
        fileDirectory = os.path.dirname(absolutepath)
        # Navigate to data directory
        newPath = os.path.join(fileDirectory, 'data')
        # Join paths
        LogFilePath = os.path.join(newPath, '#LogFile.txt')
        
        # Read existing text from file
        try:
            with open(LogFilePath, 'r') as file:
                old_text = file.read()
                file.close()
        except:
            pass
        
        # Open the file in write mode and write new text at the beginning of the file
        with open(LogFilePath, 'w') as file:
            file.write(str(self.getActualTime()) + '\t' + new_text + placeOfFunction + '\n')
            file.write(old_text)
            file.close()
    
    def retryErrorUiClicked(self):
        try:
            self.windowError.close()
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to close warning window. Close all windows and restart program. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
        try:
            cam.Connect()
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
        except:
            self.text = "Error: Failed to connect to camera. Close all windows and restart program. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
        try:
            self.Timer.start()
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to restart Timer. Close all windows and restart program. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
    
    def manualchange(self):
        try:
            if self.Manual.isChecked():
                self.Auto.setChecked(False)
            elif not self.Manual.isChecked():
                self.Auto.setChecked(True)
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to change manual. Try again. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
            
    def autoexptime(self):
        try:
            if self.Auto.isChecked():
                CameraControl.AutoExpTime(True)
                self.Manual.setChecked(False)
                self.Exposure_Time.setDisabled(True)
                self.Exposure_Box.setDisabled(True)
                self.TargetBrightnessbox.setDisabled(False)
                self.TargetBrightnessslider.setDisabled(False)
                self.Exposure_Box.setValue(CameraControl.getval("ExposureTime"))
                self.Exposure_Time.setValue(CameraControl.getval("ExposureTime"))
        
            elif not self.Auto.isChecked():
                CameraControl.AutoExpTime(False)
                self.Manual.setChecked(True)
                self.Exposure_Time.setDisabled(False)
                self.Exposure_Box.setDisabled(False)
                self.TargetBrightnessbox.setDisabled(True)
                self.TargetBrightnessslider.setDisabled(True)
                self.Exposure_Box.setValue(CameraControl.getval("ExposureTime"))
                self.Exposure_Time.setValue(CameraControl.getval("ExposureTime"))
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to set exposure time parameters for automatic mode. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
    
    def setexptime(self):
        if not self.Auto.isChecked():
            try:
                CameraControl.SetExpTime(self.Exposure_Time.value())
                print(CameraControl.GetExptime())
            except Exception as e:
                print(type(e))
                traceback.print_exc()
                frameinfo = getframeinfo(currentframe())
                self.functionPlace = str(frameinfo.lineno)
                self.text = "Error: Failed to set exposure time in manual mode. Backend, function in line: "
                self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
                self.updateLogFile(self.text, self.functionPlace)
            return
    
    def getexptime(self):
        try:
            exptime = CameraControl.GetExptime()
            self.Gain.setValue(exptime)
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to get exposure time and to set gain value. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
        
    def autogain(self):
        try:
            if self.Auto.isChecked():
                CameraControl.AutoGain(True)
                self.Gain.setDisabled(True)
                self.Gain_Box.setDisabled(True)
                self.Gain_Box.setValue(CameraControl.getval("Gain"))
                self.Gain.setValue(CameraControl.getval("Gain"))
    
            elif not self.Auto.isChecked():
                CameraControl.AutoGain(False)
                self.Gain.setDisabled(False)
                self.Gain_Box.setDisabled(False)
                self.Gain_Box.setValue(CameraControl.getval("Gain"))
                self.Gain.setValue(CameraControl.getval("Gain"))
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to set gain parameters for automatic mode. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)

    def setgain(self):
        if not self.Auto.isChecked():
            try:
                CameraControl.SetGain(self.Gain.value())
                print(CameraControl.GetGain())
            except Exception as e:
                print(type(e))
                traceback.print_exc()
                frameinfo = getframeinfo(currentframe())
                self.functionPlace = str(frameinfo.lineno)
                self.text = "Error: Failed to set gain parameters in manual mode. Backend, function in line: "
                self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
                self.updateLogFile(self.text, self.functionPlace)
            return

    def getgain(self):
        try:
            gain = CameraControl.GetGain()
            self.Gain.setValue(gain)
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to get gain value. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
        
    def setbrightness(self):
        if self.Auto.isChecked():
            try:
                CameraControl.SetBrightness(self.TargetBrightnessslider.value())
                print(CameraControl.getval("TargetBrightness"))
            except Exception as e:
                print(type(e))
                traceback.print_exc()
                frameinfo = getframeinfo(currentframe())
                self.functionPlace = str(frameinfo.lineno)
                self.text = "Error: Failed to set brightness value. Backend, function in line: "
                self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
                self.updateLogFile(self.text, self.functionPlace)
            return
    
    def flashing(self):
        try:
            if self.flag:
                self.Frames.setStyleSheet('background-color: none; font-size: 15px')
            else:
                self.Frames.setStyleSheet('background-color: green; font-size: 15px')
            self.flag = not self.flag
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Flashing 'Frames/s' failed. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)

    def Captureimage(self):
        try:
            CameraControl.save()
        except Exception as e:
            print(type(e))
            traceback.print_exc()
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to save image. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
        return
    
    def openimage(self):
        try:
            CameraControl.OpenImage()
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to open image. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
    
    def openParameterDialog(self):
        try:    
            # Creating path of relative path to folder data
            absolutepath = os.path.abspath(__file__)  
            #Path of filedirectory
            fileDirectory = os.path.dirname(absolutepath)
            #Navigate to data directory
            newPath = os.path.join(fileDirectory, 'data')
            
            file_dialog = QFileDialog()
            file_dialog.setDirectory(newPath)
            file_dialog.setNameFilter("Parameter Files (*.cmprms)")
            file_dialog.exec()
            opendialogpath = file_dialog.selectedFiles()[0]
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to open file explorer or/and to get filepath. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
        # Set Parameters of camera
        try:
            self.Timer.stop()
            CameraControl.readSettingsOutOfFile(opendialogpath)
            self.Timer.start()
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to load custom parameters. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
        
        try:
            # Setting the right values into the interface by checking the camera
            self.Exposure_Box.setValue(CameraControl.getval("ExposureTime"))
            self.Exposure_Time.setValue(CameraControl.getval("ExposureTime"))
            self.Gain_Box.setValue(CameraControl.getval("Gain"))
            self.Gain.setValue(CameraControl.getval("Gain"))
            self.TargetBrightnessbox.setValue(CameraControl.getval("TargetBrightness"))
            self.TargetBrightnessslider.setValue(CameraControl.getval("TargetBrightness"))
            self.loginstate = False
    
            if CameraControl.getval("ExposureTimeAuto"):
                self.Auto.setChecked(True)
                self.Manual.setChecked(False)
                self.autoexptime()
                self.autogain()
                self.TargetBrightnessbox.setDisabled(False)
                self.TargetBrightnessslider.setDisabled(False)

            else:
                self.Auto.setChecked(False)
                self.Manual.setChecked(True)
                self.autoexptime()
                self.autogain()
                self.TargetBrightnessbox.setDisabled(True)
                self.TargetBrightnessslider.setDisabled(True)
    
            self.TAxisReadOut.setDisabled(True)
            self.UAxisReadOut.setDisabled(True)
    
            if not self.loginstate:
                self.FeatureBox.setDisabled(True)
                self.LogOut.setDisabled(True)
                self.BoolBox.setDisabled(True)
                self.IntSpinBox.setDisabled(True)
                self.IntSlider.setDisabled(True)
                self.EnumBox.setDisabled(True)
                self.StringBox.setDisabled(True)
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to set GUI-parameters. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
        return (0)
    
    def saveCustomParametersInFile(self):
        try:
            # # Version with window to name file:
            # self.windowNameParameterFile = QtWidgets.QDialog()
            # self.uiNPF = nameParameterFileUiDialog()
            # self.uiNPF.setupNameParameterFileUi(self.windowNameParameterFile)
            # self.windowNameParameterFile.show() 
            # self.uiNPF.SaveButton_savingParam.clicked.connect(self.clickedSaveButton)
            # self.uiNPF.CancelButton_savingParam.clicked.connect(self.clickedCancelButton)
            
            # Version date as filename:
            nameParameter = self.getActualTimeFilename()
            self.Timer.stop()
            CameraControl.saveSettingsInFile(nameParameter)
            self.Timer.start()
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            # Version with window to name file:
            # self.text = "Error: Failed to open filename-ui. Backend, function in line: "
            # Version date as filename:
            self.text = "Error: Failed to call CameraControl. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
        
    def clickedCancelButton(self):
        """
        in addition to saveCustomParametersInFile
        """
        self.uiNPF.textEdit_savingParam.clear()
        self.windowNameParameterFile.close()

        
    def clickedSaveButton(self):
        """
        in addition to saveCustomParametersInFile
        """
        try:  
            textboxValue = self.uiNPF.textEdit_savingParam.toPlainText()
            self.uiNPF.textEdit_savingParam.clear()
            self.windowNameParameterFile.close()
            CameraControl.saveSettingsInFile(textboxValue)
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to save custom parameters. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
    
    def saveDefaultParametersInFile(self):
        try:
            filename = 'Default'
            CameraControl.saveSettingsInFile(filename)
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to save Parameters as 'Default'. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
        
    def readDefaultParametersOutOfFile(self):
        #
        try:
            CameraControl.parainit()
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to initialise default parameters. Check if 'Default' file exists. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
        try:
            # Setting the right values into the interface by checking the camera
            self.Exposure_Box.setValue(CameraControl.getval("ExposureTime"))
            self.Exposure_Time.setValue(CameraControl.getval("ExposureTime"))
            self.Gain_Box.setValue(CameraControl.getval("Gain"))
            self.Gain.setValue(CameraControl.getval("Gain"))
            self.TargetBrightnessbox.setValue(CameraControl.getval("TargetBrightness"))
            self.TargetBrightnessslider.setValue(CameraControl.getval("TargetBrightness"))
            self.loginstate = False
    
            if CameraControl.getval("ExposureTimeAuto"):
                self.Auto.setChecked(True)
                self.Manual.setChecked(False)
                self.autoexptime()
                self.autogain()
                self.TargetBrightnessbox.setDisabled(False)
                self.TargetBrightnessslider.setDisabled(False)
            
            else:
                self.Auto.setChecked(False)
                self.Manual.setChecked(True)
                self.autoexptime()
                self.autogain()
                self.TargetBrightnessbox.setDisabled(True)
                self.TargetBrightnessslider.setDisabled(True)
    
            self.TAxisReadOut.setDisabled(True)
            self.UAxisReadOut.setDisabled(True)
    
            if not self.loginstate:
                self.FeatureBox.setDisabled(True)
                self.LogOut.setDisabled(True)
                self.BoolBox.setDisabled(True)
                self.IntSpinBox.setDisabled(True)
                self.IntSlider.setDisabled(True)
                self.EnumBox.setDisabled(True)
                self.StringBox.setDisabled(True)
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to set GUI-parameters. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
    
    def rasptime(self):
        try:
            now = datetime.datetime.now()
            current_time = now.strftime("%H:%M:%S")
            print("Current Time =", current_time)
            self.Timedisplay.setText(current_time)
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to set get and/or set time. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
            
    def readoffset(self):
            try:
                self.Timer.stop()
                Off.measPoints = []
                dist = Off.offsetread()
                self.Timer.start()
                # if not dist == []:
                self.TAxisReadOut.setPlainText(str(dist[0]))
                self.UAxisReadOut.setPlainText(str(dist[1]))
            except Exception as e:
                print(type(e))
                traceback.print_exc()
                frameinfo = getframeinfo(currentframe())
                self.functionPlace = str(frameinfo.lineno)
                self.text = "Error: Failed to read offset. Backend, function in line: "
                self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
                self.updateLogFile(self.text, self.functionPlace)
            
    def autoguigenerate(self):
        try:
            feature = self.FeatureBox.currentText()
            self.GuruFeatureName.setText(feature)
            featureval, featureinter, featuremax, featuremin, featureenumlist = CameraControl.autogenerategui(feature)
            featuredesc = CameraControl.featuredescrpition(feature)
            self.DescriptionGuru.setText(featuredesc)
    
            if featureinter == "Not Available":
                self.BoolBox.setDisabled(True)
                self.IntSpinBox.setDisabled(True)
                self.IntSlider.setDisabled(True)
                self.EnumBox.setDisabled(True)
                self.StringBox.setDisabled(True)
                self.StringBox.setPlainText(featureval)
    
            if featureinter == "bool":
                self.BoolBox.setDisabled(False)
                self.IntSpinBox.setDisabled(True)
                self.IntSlider.setDisabled(True)
                self.EnumBox.setDisabled(True)
                self.StringBox.setDisabled(True)
                self.BoolBox.setChecked(featureval)
    
            elif featureinter == "int":
                self.BoolBox.setDisabled(True)
                self.IntSpinBox.setDisabled(False)
                self.IntSlider.setDisabled(False)
                self.EnumBox.setDisabled(True)
                self.StringBox.setDisabled(True)
                if featuremax > 2147483647:
                    featuremax = featuremax / 2
                    featuremin = featuremax * -1
                self.IntSpinBox.setMaximum(int(featuremax))
                self.IntSpinBox.setMinimum(int(featuremin))
                self.IntSlider.setMaximum(int(featuremax))
                self.IntSlider.setMinimum(int(featuremin))
                self.IntSpinBox.setValue(int(featureval))
    
            elif featureinter == "float":
                self.BoolBox.setDisabled(True)
                self.IntSpinBox.setDisabled(False)
                self.IntSlider.setDisabled(False)
                self.EnumBox.setDisabled(True)
                self.StringBox.setDisabled(True)
                self.IntSpinBox.setMaximum(int(featuremax))
                self.IntSpinBox.setMinimum(int(featuremin))
                self.IntSlider.setMaximum(int(featuremax))
                self.IntSlider.setMinimum(int(featuremin))
                self.IntSpinBox.setValue(int(featureval))
    
            elif featureinter == "string":
                self.BoolBox.setDisabled(True)
                self.IntSpinBox.setDisabled(True)
                self.IntSlider.setDisabled(True)
                self.EnumBox.setDisabled(True)
                self.StringBox.setDisabled(False)
                self.StringBox.setPlainText(featureval)
    
            elif featureinter == "enum":
                self.EnumBox.clear()
                self.BoolBox.setDisabled(True)
                self.IntSpinBox.setDisabled(True)
                self.IntSlider.setDisabled(True)
                self.EnumBox.setDisabled(False)
                self.StringBox.setDisabled(True)
                self.EnumBox.addItem(featureval)
                for f in featureenumlist:
                    if not f == featureval:
                        self.EnumBox.addItem(f)
    
        except Exception as e:
            print(type(e))
            traceback.print_exc()
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to set up GUI-parameters. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)

    def featureenumset(self):
        try:
            if not self.EnumBox.currentText() is None:
                enum = self.EnumBox.currentText()
                name = self.FeatureBox.currentText()
                CameraControl.enumsetter(name, enum)
        except Exception as e:
            print(type(e))
            traceback.print_exc()
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to set enum-feature. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
    
    def featureboolset(self):
        try:
            name = self.FeatureBox.currentText()
            if self.BoolBox.checkState():
                state = "Continuous"
            elif not self.BoolBox.checkState():
                state = "Off"
            CameraControl.boolset(name, state)
        except Exception as e:
            print(type(e))
            traceback.print_exc()
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to set bool-feature. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
    
    def featurefloatset(self):
        try:
            name = self.FeatureBox.currentText()
            val = self.IntSpinBox.value()
            CameraControl.floatset(name, val)
        except Exception as e:
            print(type(e))
            traceback.print_exc()
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to set float-feature. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
    
    def Description(self, featurename):
        try:
            desc = CameraControl.featuredescrpition(featurename)
            self.DescriptionStandard.setText(desc)
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to get description of feature. Description may not be available. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
    
    def openlog(self):
        try:            
            self.window = QtWidgets.QDialog()
            self.ui = Ui_Dialog()
            self.ui.setupUi(self.window)
            self.window.show()
            self.ui.loginbutton.clicked.connect(self.signedin)
            
            # self.loadingScreen = QtWidgets.QDialog()
            # self.ui = Ui_Dialog_Loading()
            # self.ui.setupUi(self.loadingScreen)
            # self.loadingScreen.show()
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to open login window. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
    
    def signedin(self):
        if self.ui.email.text() == 'admin' and self.ui.password.text() == 'admin':
            self.ui.endmessage.setText('Successfull login')
            print('logdin')
            self.FeatureBox.setDisabled(False)
            self.LogOut.setDisabled(False)
            self.BoolBox.setDisabled(False)
            self.IntSpinBox.setDisabled(False)
            self.IntSlider.setDisabled(False)
            self.EnumBox.setDisabled(False)
            self.StringBox.setDisabled(False)
            self.SignInButton.setDisabled(True)
            self.window.close()
        else:
            print('The email or Password are incorrect')
            self.ui.endmessage.setText('The Email or Password are incorrect. Please try again')
    
    def signedout(self):
        try:
            self.SignInButton.setDisabled(False)
            self.FeatureBox.setDisabled(True)
            self.LogOut.setDisabled(True)
            self.BoolBox.setDisabled(True)
            self.IntSpinBox.setDisabled(True)
            self.IntSlider.setDisabled(True)
            self.EnumBox.setDisabled(True)
            self.StringBox.setDisabled(True)
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to set up GUI-parameters. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
    
    def coordinates(self):
        try:
            if self.Coordinates.isChecked():
                self.opacity_effect.setOpacity(1.0)
                self.CoordinatesDisplay.setGraphicsEffect(self.opacity_effect)
        
            elif not self.Coordinates.isChecked():
                self.opacity_effect.setOpacity(0.0)
                self.CoordinatesDisplay.setGraphicsEffect(self.opacity_effect)
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Coordinates-function failed. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
            
    def zoom_in(self):
        try:
            if self.scale < 2:
                self.scale += 0.1
            self.zoomSlider.setValue(self.scale*10)
            self.update()
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to zoom in. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
            
    def zoom_out(self):
        try:
            if self.scale > 1:
                self.scale -= 0.1         
            self.zoomSlider.setValue(self.scale*10)
            self.update()
        except:
            frameinfo = getframeinfo(currentframe())
            self.functionPlace = str(frameinfo.lineno)
            self.text = "Error: Failed to zoom out. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
            
    def zoom_slide(self):
        try:    
            self.scale = self.zoomSlider.value()/10
            self.update()
        except:
            frameinfo = getframeinfo(currentframe()) 
            self.functionPlace = str(frameinfo.lineno) 
            self.text = "Error: Failed to zoom. Backend, function in line: "
            self.ErrorOut.setText(str(self.getActualTime()) + self.text + self.functionPlace)
            self.updateLogFile(self.text, self.functionPlace)
