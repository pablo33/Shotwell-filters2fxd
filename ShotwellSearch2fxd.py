#!/usr/bin/python3
# import xml.etree.ElementTree as etree
import os, shutil

freevofxduserpath = os.path.join(os.getenv('HOME'),".freevo/fxd/photos/")

from ShotwellSearchAPI import ShotwellSearch


def writefilesentries (f, SR, duration = 0):
	f.write ("\t\t<files>\n")
	for Id, entry in SR.Resultentries():
		f.write('\t\t\t<file duration="%(duration)s">%(file)s</file>\n'%{'duration': duration, 'file': entry})
	f.write ("\t\t</files>\n")
	return

def	writeslideshowblock (f, SR, ramdom = 0, repeat = 0):
	f.write('\t<slideshow title="%(title)s" random="%(ramdom)s" repeat="%(repeat)s">\n'%{'title':SR.searchname, 'ramdom':ramdom, 'repeat': repeat})
	writefilesentries (f, SR)
	f.write('\t</slideshow>\n')
	return


def Writefxd (SR, folderpath):
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
		print (SR.searchid, SR.searchname, SR.query)
		Writefxd (SR, freevofxduserpath)



