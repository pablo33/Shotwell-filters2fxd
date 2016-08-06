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
	ops = {
		'ANY'	:'OR',
		'ALL'	:'AND',
		'NONE'	:'AND NOT'
		}

	fields = {
		'ANY TEXT': 	('comment','event_comment','eventname','title','filename'),
		'COMMENT': 		('comment','event_comment'),
		'DATE': 		('date',),
		'EVENT_NAME': 	('eventname',),
		'FILE_NAME':	('filename',),
		'FLAG STATE':	('flagstate',),
		'MEDIA TYPE':	('',),
		'PHOTO STATE':	('photostate',),
		'RATING':		('rating',),
		'TAG':			('tag',),
		'TITLE':		('title',),
		}

	textoperators = {
		'CONTAINS': u"LIKE '%value%'",
		'IS_EXACTLY': u"= 'value'",
		'STARTS_WITH': u"LIKE 'value%'",
		'ENDS_WITH': u"LIKE '%value'",
		'DOES_NOT_CONTAINS' : u"NOT LIKE '%value%'",
		'IS_SET' : u"IS NOT NULL",
		'IS_NOT_SET' : u"IS NULL",
		}

	print ("Class ShotwellSearch initialized")
	# Copying DBfile
	if itemcheck (DBpath) != 'file':
		print ('Can\'t locate Shotwell Database.', DBpath)
		exit()
	tmpDB = 'TempDB.sqlite3'
	if itemcheck (tmpDB) == 'file':
		os.remove(tmpDB)
	shutil.copy (DBpath, tmpDB)
	con = sqlite3.connect (tmpDB)

	con.execute ("CREATE TABLE results (\
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
	con.execute ("INSERT INTO results \
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
	con.execute ("INSERT INTO results\
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
	con.commit ()
		
	# Extracting and setting filenames
	cursor = con.cursor()
	cursor.execute ("SELECT id, fullfilepath FROM results ORDER BY id")

	for ID, Fullfilepath in cursor:
		print (ID, Fullfilepath)
		Filename = os.path.splitext(os.path.basename(Fullfilepath))[0]
		# Finding tags  (thumb000000000000000f,)
		thumb = u"'%"+"thumb%016x,"%ID+u"%'"
		tagstring = ''
		for entry in con.execute ("SELECT name FROM tagtable WHERE photo_id_list LIKE %s"%thumb):
			tagstring+= ' '+entry[0][1:].split ("/").pop()  # fetchs the last tag
		print (tagstring)
		if tagstring == '':
			tagstring = None
		con.execute("UPDATE results SET filename = ?, tags = ? WHERE id = ?", (Filename,tagstring,ID))

	con.commit()

	def __init__(self, DBpath):
		self.Moperator = None
		self.whereList = list()

	def mainoperator (self, moperator):
		moperator = moperator.upper()
		if moperator not in self.ops:
			raise OutOfRangeError ('This main operator is not allowed (%s)'%moperator)
			return
		self.Moperator = self.ops[moperator]

	def addtextfilter (self, field, operator, value):
		if field not in self.fields:
			raise OutOfRangeError ('Not a valid field %s not in %s'%(field, fields))
		if operator not in self.textoperators:
			raise OutOfRangeError ('Not a valid operator %s not in %s'%(operator, self.textoperators))
		# if self.whereList
		for wherefield in self.fields[field]:
			string = " ".join([wherefield, self.textoperators[operator]])
			if value != None:
				string = string.replace('value',value)
			self.whereList.append (string)
			print (string)
		return string

	def showquery (self):
		if len (self.whereList) == 0:
			print ("no filters where entered.")
			return
		if self.Moperator == None:
			print ("no main operator was entered")
			return
		condition = str(" "+self.Moperator+" ").join(self.whereList)	

		query = "SELECT id, fullfilepath FROM results WHERE %s"%condition
		return query
	

"""
Date operators: 
	'IS EXACTLY' : u"= value",
	'IS AFTER' : u"> value",
	'IS BEFORE' : u"< value",
	'IS BETWEEN' : u"> value and date < value2",

SELECT id, fullfilepath FROM results WHERE %(condition)"%s(condition)

"""

if __name__ == '__main__':
	search = ShotwellSearch(DBpath)
	#search.addfilter ('comment','CONTAINS','Super')
	#search.addfilter ('filename','CONTAINS','Last')



