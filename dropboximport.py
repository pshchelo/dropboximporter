#!/usr/bin/env python
"""Rename files like Dropbox Camera upload does

"""

import time
import os.path
import shutil

from PIL import Image
from PIL import ExifTags
import enzyme

DATEEXIFKEY = [key for (key, value) in ExifTags.TAGS.items()
               if value == 'DateTimeOriginal'][0]
FMT = "%Y-%m-%d %H.%M.%S"

VIDEOFILES = ['.mp4', '.3gp', '.mov', '.mkv', '.webm', '.avi', '.ogm', '.ogv']
IMAGEFILES = ['.jpg', '.jpeg']


def import_file(filename, targetdir='', fmt=FMT):
    """Rename file according to metadata date/time."""
    dir, name = os.path.split(filename)
    filetime = get_time(filename)
    if filetime:
        datestring = time.strftime(fmt, filetime)
        newname = datestring + os.path.splitext(name)[1]
        if targetdir == '':
            targetdir = os.path.dirname(filename)
        newfilename = os.path.join(targetdir, newname)
        if os.path.exists(newfilename):
            return filename
        try:
            shutil.copy2(filename, newfilename)
        except IOError:
            return filename
        else:
            return None
    else:
        return filename


def get_time(filename):
    """Get file date, from metadata or file system."""
    ext = os.path.splitext(filename)[1]
    if ext.lower() in IMAGEFILES:
        return get_exif_time(filename)
    elif ext.lower() in VIDEOFILES:
        return get_video_time(filename)
    else:
        return get_file_time(filename)


def get_exif_time(filename):
    """Get time from EXIF metadata."""
    img = Image.open(filename)
    exf = img._getexif()
    if exf:
        timestr = exf.get(DATEEXIFKEY, None)
        if timestr:
            return time.strptime(timestr, "%Y:%m:%d %H:%M:%S")
    return get_file_time(filename)


def get_video_time(filename):
    try:
        mdata = enzyme.parse(filename)
    except enzyme.exceptions.NoParserError:
        return get_file_time(filename)
    tmepoch = mdata.timestamp
    # here is the place where too old (erroneous) date is not supported
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
