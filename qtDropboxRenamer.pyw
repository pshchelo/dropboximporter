#!/usr/bin/env python
"""Dropbox CameraUpload renamer

"""
import os
import sys
try:
    from PySide import QtGui
except:
    from PyQt4 import QtGui

import dropboxrename


class DropboxRenamerWindow(QtGui.QWidget):
    """Main window for the application"""

    def __init__(self):
        super(DropboxRenamerWindow, self).__init__()
        # Add widgets
        addbtn = QtGui.QPushButton("Add files", self)
        delbtn = QtGui.QPushButton("Remove files", self)

        self.filelist = QtGui.QListWidget(self)

        dirlabel = QtGui.QLabel("Import to ...", self)
        self.dirname = QtGui.QLineEdit(self)
        dirbtn = QtGui.QPushButton('...', self)
        tzlabel = QtGui.QLabel("Timeshift", self)
        self.tzcbox = QtGui.QComboBox(self)
        importbtn = QtGui.QPushButton("Import", self)

        # Connect signals
        addbtn.clicked.connect(self.OnAddFiles)
        delbtn.clicked.connect(self.OnRemoveFiles)
        dirbtn.clicked.connect(self.OnChooseDir)
        importbtn.clicked.connect(self.OnRenameFiles)

        # Init widgets
        self.init_gui_values()

        # Do layout
        mainbox = QtGui.QVBoxLayout()
        filesbox = QtGui.QHBoxLayout()
        dirbox = QtGui.QHBoxLayout()
        timebox = QtGui.QHBoxLayout()

        filesbox.addWidget(addbtn)
        filesbox.addWidget(delbtn)
        mainbox.addLayout(filesbox)
        mainbox.addWidget(self.filelist)
        dirbox.addWidget(dirlabel)
        dirbox.addWidget(self.dirname)
        dirbox.addWidget(dirbtn)
        mainbox.addLayout(dirbox)
        timebox.addWidget(tzlabel)
        timebox.addWidget(self.tzcbox)
        mainbox.addLayout(timebox)
        mainbox.addWidget(importbtn)

        self.setLayout(mainbox)

        self.setWindowTitle("Dropbox photo import")

    def init_gui_values(self):
        if len(sys.argv) > 1:
            self.filelist.addItems(sys.argv[1:])
        self.dirname.setText(os.path.expanduser("~/Dropbox/Camera Uploads"))
        self.tzcbox.addItems(["UTC{:+0d}".format(x) for x in range(-12, 13)])

    def OnAddFiles(self):
        pass

    def OnRemoveFiles(self):
        pass

    def OnChooseDir(self):
        dlg = QtGui.QFileDialog(self)
        dlg.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
        dlg.setFileMode(QtGui.QFileDialog.Directory)
        dlg.setOption(QtGui.QFileDialog.ShowDirsOnly, True)
        dlg.setDirectory(os.path.abspath(self.dirname.text()))
        if dlg.exec_():
            self.dirname.setText(dlg.selectedFiles()[0])

    def OnRenameFiles(self):
        for index in range(self.filelist.count() - 1, -1, -1):
            filename = self.filelist.item(index).text()
            status = dropboxrename.rename(filename)
            if not status:
                self.filelist.takeItem(index)
        if self.filelist.count() > 0:
            icon = QtGui.QMessageBox.Warning
            title = "Warning"
            text = 'Could not rename some files!'
            infotext = 'Check files remained in the list'
        else:
            icon = QtGui.QMessageBox.Information
            title = "Note"
            text = 'Processing complete.'
            infotext = 'No errors occured.'
        mesg = QtGui.QMessageBox(icon, title, text)
        mesg.setInformativeText(infotext)
        mesg.exec_()

app = QtGui.QApplication(sys.argv)
window = DropboxRenamerWindow()
window.show()
sys.exit(app.exec_())
