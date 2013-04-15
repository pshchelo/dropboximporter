#!/usr/bin/env python
"""
Rename images as Dropbox "Camera Upload" feature does.

File name format is "year-month-day hours.minutes.seconds".
Tries to extract creation date from EXIF or video metadata,
if not available uses file modification time from file system.

Does not support video metadata earlier than Epoch time 0
(earlier than 1970-01-01 00:00:00 UTC).


"""
import sys
import os
import time

from PIL import Image
from PIL import ExifTags
import enzyme

import wx

dateexifkey = [key for (key, value) in ExifTags.TAGS.items()
               if value == 'DateTimeOriginal'][0]
FMT = "%Y-%m-%d %H.%M.%S"


class FileListDropTarget(wx.FileDropTarget):
    """ This object implements Drop Target functionality
    for Files droped to ListBox

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

        addfilebtn = wx.Button(self, -1, 'Add files',
                               style=wx.ID_OPEN |
                               wx.BU_EXACTFIT |
                               wx.BU_LEFT |
                               wx.BU_RIGHT)
        self.Bind(wx.EVT_BUTTON, self.OnAddFiles, addfilebtn)
        btnsizer.Add(addfilebtn, 1, wx.GROW)

        rmfilebtn = wx.Button(self, -1, 'Remove files',
                              style=wx.ID_CLOSE |
                              wx.BU_EXACTFIT |
                              wx.BU_LEFT |
                              wx.BU_RIGHT)
        self.Bind(wx.EVT_BUTTON, self.OnRmFiles, rmfilebtn)
        btnsizer.Add(rmfilebtn, 1, wx.GROW)

        vsizer.Add(btnsizer, 0, wx.GROW)

        self.filelist = wx.ListBox(self, -1, size=(300, 200),
                                   choices=filenames,
                                   style=wx.LB_EXTENDED |
                                   wx.LB_HSCROLL |
                                   wx.LB_NEEDED_SB |
                                   wx.LB_SORT)

        vsizer.Add(self.filelist, 1, wx.GROW)

        self.SetSizer(vsizer)
        self.Fit()

        # Create a File Drop Target object
        droptarget = FileListDropTarget(self.filelist)
        # Link the Drop Target Object to the ListBox
        self.filelist.SetDropTarget(droptarget)

    def OnAddFiles(self, evt):
        fileDlg = wx.FileDialog(self, 'Choose files',
                                style=wx.OPEN |
                                wx.FD_MULTIPLE |
                                wx.FD_CHANGE_DIR,
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
                                style=wx.ID_OPEN |
                                wx.BU_EXACTFIT |
                                wx.BU_LEFT |
                                wx.BU_RIGHT)
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
        wx.MessageDialog(self, text, 'Report', wx.OK | icon).ShowModal()

    def RenameFiles(self, filenames):
        mesg = []
        filenames.reverse()
        for index, filename in enumerate(filenames):
            dir, name = os.path.split(filename)
            filetime = get_time(filename)
            if filetime:
                datestring = time.strftime(FMT, filetime)
                newname = datestring + os.path.splitext(name)[1]
                newfilename = os.path.join(dir, newname)
                try:
                    os.renames(filename, newfilename)
                    self.filelist.RemoveFile(len(filenames) - index - 1)
                except OSError:
                    mesg.append(filename)
            else:
                mesg.append(filename)
        return mesg


def get_time(filename):
    """Get file date, from metadata or file system."""
    ext = os.path.splitext(filename)[1]
    if ext.lower() in ('jpeg', 'jpg'):
        return get_exif_time(filename)
    elif ext.lower() in ('mp4', '3gp', 'mov', 'avi'):
        return get_video_time(filename)
    else:
        return get_file_time(filename)


def get_exif_time(filename):
    """Get time from EXIF metadata."""
    img = Image.open(filename)
    exf = img._getexif()
    if exf:
        timestr = exf.get(36867, None)  # according to PILExifTags.TAGS
        if timestr:
            return time.strptime(timestr, "%Y:%m:%d %H:%M:%S")
    return get_file_time()


def get_video_time(filename):
    mdata = enzyme.parse(filename)
    tmepoch = mdata.timestamp
    if tmepoch and tmepoch > 0:
        return time.ctime(mdata.timestamp)
    else:
        return get_file_time(filename)


def get_file_time(filename):
    try:
        mtime = os.path.getmtime(filename)
    except OSError:
        return None
    return time.localtime(mtime)


app = wx.App()
frame = RenamerFrame(None, -1, sys.argv[1:])
frame.Show()
app.MainLoop()
