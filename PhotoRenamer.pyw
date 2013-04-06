#!/usr/bin/env python
"""
Renames images and videos from digital camera
according to their EXIF (or other tag) creation date.
If such info is abscent,it uses file creation date.

Rename scheme is the same as Dropbox Camera Upload feature uses:
    YYYY-MM-DD hh.mm.ss

Depends on `ExifTool by Phil Harvey 
<http://www.sno.phy.queensu.ca/~phil/exiftool/>`_

You shoud have ``exiftool`` executable somewhere in the path.


As I have never seen AVI files from cameras having metadata
with creation time, this combination is untested/unsupported

"""

import sys
import os, time, subprocess, calendar
import wx

class FileListDropTarget(wx.FileDropTarget):
    """ This object implements Drop Target functionality for Files droped to ListBox

    (and in fact any subclass of wx.ItemContainer

    """
    def __init__(self, obj):
        """ Initialize the Drop Target, passing in the Object Reference to
        indicate what should receive the dropped files """
        # Initialize the wsFileDropTarget Object
        wx.FileDropTarget.__init__(self)
        # Store the Object Reference for dropped files
        self.obj = obj

    def OnDropFiles(self, x, y, filenames):
        """ Implement File Drop """
        # append a list of the file names to ListBox items
        self.obj.AppendItems(filenames)

class GatherFilesPanel(wx.Panel):
    """Panel that displays a list of files

    and allows adding and removing files or groups of files

    """
    def __init__(self, parent, id, filenames, wildcard="All files (*.*)|*.*"):
        wx.Panel.__init__(self, parent, id)
        
        self.wildcard = wildcard
        vsizer = wx.BoxSizer(wx.VERTICAL)
        
        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        
        addfilebtn = wx.Button(self, -1, 'Add files', style = wx.ID_OPEN|wx.BU_EXACTFIT|wx.BU_LEFT|wx.BU_RIGHT)
        self.Bind(wx.EVT_BUTTON, self.OnAddFiles, addfilebtn)
        btnsizer.Add(addfilebtn, 1, wx.GROW)
        
        rmfilebtn = wx.Button(self, -1, 'Remove files', style = wx.ID_CLOSE|wx.BU_EXACTFIT|wx.BU_LEFT|wx.BU_RIGHT)
        self.Bind(wx.EVT_BUTTON, self.OnRmFiles, rmfilebtn)
        btnsizer.Add(rmfilebtn, 1, wx.GROW)
        
        vsizer.Add(btnsizer, 0, wx.GROW)
        
        self.filelist= wx.ListBox(self, -1, size = (300,200), choices = filenames, 
                style = wx.LB_EXTENDED|wx.LB_HSCROLL|wx.LB_NEEDED_SB|wx.LB_SORT)
        
        vsizer.Add(self.filelist, 1, wx.GROW)
        
        self.SetSizer(vsizer)
        self.Fit()
        
        # Create a File Drop Target object
        droptarget = FileListDropTarget(self.filelist)
        # Link the Drop Target Object to the ListBox
        self.filelist.SetDropTarget(droptarget)
        
    def OnAddFiles(self, evt):
        fileDlg = wx.FileDialog(self, 'Choose files',
                                style=wx.OPEN|wx.FD_MULTIPLE|wx.FD_CHANGE_DIR,
                                wildcard=self.wildcard)
        if fileDlg.ShowModal() == wx.ID_OK:
            self.filelist.AppendItems(fileDlg.GetPaths())
            ## self.fileslist.Set(self.filenames)
        fileDlg.Destroy()
        evt.Skip()
    
    def RemoveFile(self, index):
        self.filelist.Delete(index)   
    
    def OnRmFiles(self, evt):
        selected = sorted(self.filelist.GetSelections())
        selected.reverse()
        for index in selected:
            self.RemoveFile(index)
        evt.Skip()
        pass
    
    def GetFiles(self):
        return self.filelist.GetItems()
    
    def SetWildcard(self, wildcard):
        self.wildcard = wildcard
        
class RenamerFrame(wx.Frame):
    def __init__(self, parent, id, filenames, title='Rename Camera Files'):
        wx.Frame.__init__(self, parent, id, title)
        panel = wx.Panel(self, -1)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.filelist = GatherFilesPanel(panel, -1, filenames)
        ## self.filelist.SetWildcard = 'jpeg, mp4, avi, mov'
        sizer.Add(self.filelist, 1, wx.GROW)
        self.rnmbtn = wx.Button(panel, -1, 'Rename',
                       style = wx.ID_OPEN|wx.BU_EXACTFIT|wx.BU_LEFT|wx.BU_RIGHT)
        self.Bind(wx.EVT_BUTTON, self.OnRename, self.rnmbtn)
        sizer.Add(self.rnmbtn, 0, wx.GROW)
        panel.SetSizer(sizer)
        panel.Fit()
        self.Fit()
    
    def OnRename(self, evt):
        mesg = self.RenameFiles(self.filelist.GetFiles())
        if mesg:
            icon = wx.ICON_ERROR
            text = 'Could not rename the following files:\n'
            text += '\n'.join(mesg)
        else:
            icon = wx.ICON_INFORMATION
            text = 'Processing complete.\nNo errors occured.'
        wx.MessageDialog(self, text, 'Report', wx.OK|icon).ShowModal()
    
    def RenameFiles(self, filenames):
        mesg = []
        filenames.reverse()
        for index, filename in enumerate(filenames):
            dir, name = os.path.split(filename)
            filetime = self.GetTime(filename)
            if filetime:
                datestring = time.strftime("%Y-%m-%d %H.%M.%S", filetime)
                newname = datestring + os.path.splitext(name)[1]
                newfilename = os.path.join(dir, newname)
                try:
                    os.renames(filename, newfilename)
                    self.filelist.RemoveFile(len(filenames)-index-1)
                except OSError:
                    mesg.append(filename)
            else:
                mesg.append(filename)
        return mesg
        
    def GetTime(self,filename):
        exiftool = ['exiftool', '-CreateDate', filename]
        exiftoolout = subprocess.check_output(exiftool)
        if not exiftoolout:  # if no "Create Date" meta-tag present
            return get_modif_time(filename)
        datestr = exiftoolout.strip().split(" : ")[1]
        try:
            createtime = time.strptime(datestr, '%Y:%m:%d %H:%M:%S')
        except ValueError:  # if "Create Date" tag is malformed
            return get_modif_time(filename)
        else:
            # convert from UTC to local time
            # as MP4 tag stores creation time in UTC
            if os.path.splitext(filename)[1] in ('3gp','mov','mp4'):
                return time.localtime(calendar.timegm(createtime))
            else: # EXIF tag stores local time
                return createtime

def get_modif_time(filename):
    try:
        mtime = os.path.getmtime(filename)
        return time.localtime(mtime)
    except OSError:
        return None

app = wx.App()
frame = RenamerFrame(None, -1, sys.argv[1:])
frame.Show()
app.MainLoop()
