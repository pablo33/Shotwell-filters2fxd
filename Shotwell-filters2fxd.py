#!/usr/bin/python3

import sqlite3, os, shutil  #, sys, , logging, re


# ------- Set Variables ---------

DBpath = os.path.join(os.getenv('HOME'),".local/share/shotwell/data/photo.db")

# ------ utils --------
def itemcheck(pointer):
	''' returns what kind of a pointer is '''
	if type(pointer) is not str:
		raise NotStringError ('Bad input, it must be a string')
	if pointer.find("//") != -1 :
		raise MalformedPathError ('Malformed Path, it has double slashes')
	
	if os.path.isfile(pointer):
		return 'file'
	if os.path.isdir(pointer):
		return 'folder'
	if os.path.islink(pointer):
		return 'link'
	return ""


class ShotwellSearch:
	def __init__(self, DBpath, Nsearch):
		self.DBpath = DBpath
		self.Nsearch = Nsearch
		print ("Class ShotwellSearch initialized for Search nº %s"%self.Nsearch)
		# Copying DBfile
		if itemcheck (self.DBpath) != 'file':
			print ('Can\'t locate Shotwell Database.', self.DBpath)
			exit()
		self.tmpDB = 'TempDB.sqlite3'
		if itemcheck (self.tmpDB) == 'file':
			os.remove(self.tmpDB)
		shutil.copy (self.DBpath, self.tmpDB)


if __name__ == '__main__':
	search = ShotwellSearch(DBpath, 1)
