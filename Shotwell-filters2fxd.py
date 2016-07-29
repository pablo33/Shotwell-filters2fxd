#!/usr/bin/python3

import sqlite3, os, shutil  #, sys, , logging, re


# ------- Set Variables ---------

DBpath = os.path.join(os.getenv('HOME'),".local/share/shotwell/data/photo.db")



# Error Handling
class OutOfRangeError(ValueError):
	pass
class NotIntegerError(ValueError):
	pass
class NotStringError(ValueError):
	pass
class MalformedPathError(ValueError):
	pass
class EmptyStringError(ValueError):
	pass



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
	def __init__(self, DBpath):
		self.DBpath = DBpath
		print ("Class ShotwellSearch initialized")
		# Copying DBfile
		if itemcheck (DBpath) != 'file':
			print ('Can\'t locate Shotwell Database.', DBpath)
			exit()
		self.tmpDB = 'TempDB.sqlite3'
		if itemcheck (self.tmpDB) == 'file':
			os.remove(self.tmpDB)
		shutil.copy (self.DBpath, self.tmpDB)
		self.con = sqlite3.connect (self.tmpDB)
		
		# id, filename, photo-Comment, date, flagstate, photostate, rating, title      eventname, event_comment,     tag, 


		self.con.execute ("CREATE TABLE results (\
			id INTEGER PRIMARY KEY, \
			fullfilepath TEXT UNIQUE NOT NULL, \
			exposure_time INTEGER, \
			event_id INTEGER, \
			flags INTEGER DEFAULT 0, \
			rating INTEGER DEFAULT 0, \
			file_format INTEGER DEFAULT 0, \
			title TEXT, \
			comment TEXT, \
			filename TEXT, \
			event_name TEXT, \
			event_comment TEXT, \
			tags TEXT \
			)")
		
		# Insert photo and event data into results table.
		self.con.execute ("INSERT INTO results \
			SELECT \
				phototable.id as id,\
				filename as fullfilepath,\
				exposure_time,\
				event_id,\
				flags,\
				rating,\
				file_format,\
				title,\
				phototable.comment as comment,\
				null as filename,\
				eventtable.name as event_name,\
				eventtable.comment as event_comment,\
				null as tags\
			FROM phototable JOIN eventtable \
			ON phototable.event_id = eventtable.id")

		# adding "No event files" to pictures with event id = -1 and timestamp = 0
		self.con.execute ("INSERT INTO results\
			SELECT \
				id,\
				filename as fullfilepath,\
				exposure_time,\
				event_id,\
				flags,\
				rating,\
				file_format,\
				title,\
				comment,\
				null as filename,\
				null as event_name,\
				null as event_comment,\
				null as tags\
			FROM phototable\
			WHERE event_id = -1 and exposure_time = 0")
		self.con.commit ()
		
		# Extracting and setting filenames
		cursor = self.con.cursor()
		cursor.execute ("SELECT id, fullfilepath FROM results ORDER BY id")

		for ID, Fullfilepath in cursor:
			print (ID, Fullfilepath)
			Filename = os.path.splitext(os.path.basename(Fullfilepath))[0]
			# Finding tags  (thumb000000000000000f,)
			thumb = u"'%"+"thumb%016x,"%ID+u"%'"
			tagstring = ''
			for entry in self.con.execute ("SELECT name FROM tagtable WHERE photo_id_list LIKE %s"%thumb):
				tagstring+= ' '+entry[0][1:].split ("/").pop()  # fetchs the last tag
			print (tagstring)
			if tagstring == '':
				tagstring = None
			self.con.execute("UPDATE results SET filename = ?, tags = ? WHERE id = ?", (Filename,tagstring,ID))

		self.con.commit()


	def filtertext(self, Field, Searchtype, Text):
		# self.querymode = self.con.execute ("SELECT operator FROM SavedSearchDBTable WHERE id= %s"%Nsearch).fetchone()[0]
		if Field not in ('filename','comment'):
			print ('field not allowed')
			return
		if Searchtype == 'CONTAINS':
			Operator, Text = 'LIKE', u"'%"+Text+u"%'"

			print (Operator)
		if self.querymode == 'ANY':
			self.con.execute ("INSERT INTO results (id) SELECT id FROM phototable WHERE %(field)s %(operator)s %(value)s"%({'field':Field, 'operator':Operator, 'value':Text}))
		self.con.commit()


	# para resultados únicos, emplear: "SELECT DISTINCT id FROM results"

if __name__ == '__main__':
	search = ShotwellSearch(DBpath)
	#search.filtertext ('comment','CONTAINS','Super')
	#search.filtertext ('filename','CONTAINS','Last')



