#!/usr/bin/python3
# import xml.etree.ElementTree as etree
import os, shutil
from ShotwellSearchAPI import ShotwellSearch

freevofxduserpath = os.path.join(os.getenv('HOME'),".freevo/fxd/photos/")

def writesound (f, soundfolderpath = "", ramdom = 0, recursive = 0):
	f.write ('\t\t<background-music random="%s">\n'%ramdom)
	f.write ('\t\t\t<directory recursive="%(recursive)s">%(dpath)s</directory>\n'% {'recursive': recursive, 'dpath': soundfolderpath})
	#f.write ('\t\t\t<file>filename</file>\n'
	f.write('\t\t</background-music>\n')


def writecover (f, coverfilepath = ""):
	f.write ('\t\t<cover-img>%s</cover-img>\n'%coverfilepath)

def writefilesentries (f, SR, duration = 0):
	""" Writes a block of files-entries in an fxd file """
	f.write ("\t\t<files>\n")
	for Id, entry in SR.Resultentries():
		f.write('\t\t\t<file duration="%(duration)s">%(file)s</file>\n'%{'duration': duration, 'file': entry})
	f.write ("\t\t</files>\n")
	return

def	writeslideshowblock (f, SR, ramdom = 0, repeat = 0):
	""" Writes a slideshow fxd block """
	f.write('\t<slideshow title="%(title)s" random="%(ramdom)s" repeat="%(repeat)s">\n'%{'title':SR.searchname, 'ramdom':ramdom, 'repeat': repeat})
	writecover (f)
	writesound (f)
	writefilesentries (f, SR)
	f.write('\t</slideshow>\n')
	return


def Writefxd (SR, folderpath):
	""" Given a Shotwell Search connection, and a destination, it writes a fxd slideshow file"""
	fxdfilename = os.path.join(folderpath,SR.searchname + '.fxd')
	f = open(fxdfilename,'a')
	f.write('<?xml version="1.0" ?>\n<freevo>\n')
	writeslideshowblock (f, SR)
	f.write('</freevo>')
	f.close()
	return

if __name__ == '__main__':
	SR = ShotwellSearch()
	for SearchId, searchname, foo in SR.Searchtable():
		SR.Search(SearchId)
		Writefxd (SR, freevofxduserpath)



