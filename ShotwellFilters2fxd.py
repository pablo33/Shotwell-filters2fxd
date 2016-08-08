#!/usr/bin/python3

import sqlite3, os, shutil  #, sys, , logging, re
import unicodedata  # To eliminate áéíóú öü ñÑ


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

def elimina_tildes(s):
   return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))


class ShotwellSearch:
	""" Handles a Shotwell Database in order to access to its Saved Searches.
		It makes a copy of the Shotwell Database to work with.
		It makes an auxiliar table to perform Shotwell Saved Searches queries.
		It returns the Saved Searches Query as an iterator.
		It returns the file entries of a Saved Search as an iterator.
		"""
	ops = {
		'ANY'	:'OR',
		'ALL'	:'AND',
		'NONE'	:'AND NOT'
		}

	fields = {
		'ANY TEXT': 	('comment','event_comment','eventname','title','filename'),
		'COMMENT': 		('comment','event_comment'),
		'EVENT_NAME': 	('event_name',),
		'FILE_NAME':	('filename',),
		'TAG':			('tags',),
		'TITLE':		('title',),

		'DATE': 		'exposure_time',

		'RATING':		'rating',

		'FLAG STATE':	'flagstate',
		'MEDIA TYPE':	'',
		'PHOTO STATE':	'photostate',
		}

	textoperators = {
		'CONTAINS': u"LIKE '%value%'",
		'IS_EXACTLY': u"= 'value'",
		'STARTS_WITH': u"LIKE 'value%'",
		'ENDS_WITH': u"LIKE '%value'",
		'DOES_NOT_CONTAIN' : u"NOT LIKE '%value%'",
		'IS_SET' : u"IS NOT NULL",
		'IS_NOT_SET' : u"IS NULL",
		}

	dateoperators = {
		'EXACT': 'datefield = d_one',
		'AFTER': 'datefield >= d_one',
		'BEFORE': 'datefield <= d_one',
		'BETWEEN': '(datefield >= d_one AND datefield <= d_two)',
		'IS_NOT_SET': 'datefield = 0',
		}

	searchid = None
	Moperator = None
	Searchname = None
	query = None


	def __init__(self, DBpath):
		""" Makes its own tmp DB """
		# Copying DBfile
		if itemcheck (DBpath) != 'file':
			print ('Can\'t locate Shotwell Database.', DBpath)
			exit()
		tmpDB = 'TempDB.sqlite3'
		if itemcheck (tmpDB) == 'file':
			os.remove(tmpDB)
		shutil.copy (DBpath, tmpDB)
		self.con = sqlite3.connect (tmpDB)

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
			if tagstring == '':
				tagstring = None
			else:
				# aplying transformations >> lower and without tildes
				tagstring = tagstring.lower()
				tagstring = elimina_tildes(tagstring)
			print (tagstring)
			self.con.execute("UPDATE results SET filename = ?, tags = ? WHERE id = ?", (Filename,tagstring,ID))

		self.con.commit()
		print ("Class ShotwellSearch initialized, we are working on a temporal copy of the Shotwell Database.")

	def Searchtable (self):
		tablelist = self.con.execute ("SELECT id, name, operator FROM SavedSearchDBTable ORDER BY id")
		return tablelist

	def Search (self, searchid):
		""" Solve a query for this search ID
			You can access to the SQL query statement by the query attribute.
		"""
		self.searchid = searchid
		entry = self.con.execute ("SELECT name, operator FROM SavedSearchDBTable WHERE id = %s"%searchid).fetchone()
		if entry == None:
			print ("Search id out of Searchtable.")
			return 
		self.Searchname, moperator = entry
		moperator = moperator.upper()
		if moperator not in self.ops:
			raise OutOfRangeError ('This main operator is not allowed (%s)'%moperator)
			return
		self.Moperator = self.ops[moperator]
		self.whereList = list()
		# Text filters:
		for entry in self.con.execute ("SELECT search_type, context, text FROM SavedSearchDBTable_Text WHERE search_id = %s"%searchid):
			self.__addtextfilter__ (entry[0],entry[1],entry[2])
		for entry in self.con.execute ("SELECT search_type, context, date_one, date_two FROM SavedSearchDBTable_Date WHERE search_id = %s"%searchid):
			self.__adddatefilter__ (entry[0],entry[1],entry[2], entry[3])


		self.__constructquery__()

	def __addtextfilter__ (self, field, operator, value):
		if field not in self.fields:
			raise OutOfRangeError ('Not a valid field %s not in %s'%(field, fields))
		if operator not in self.textoperators:
			raise OutOfRangeError ('Not a valid operator %s not in %s'%(operator, self.textoperators))
		subwhereList = []
		for wherefield in self.fields[field]:
			if wherefield == 'tags' and operator == 'IS_EXACTLY':
				operator, value = 'CONTAINS', " "+value
			string = " ".join([wherefield, self.textoperators[operator]])
			subwhereList.append (string)
		if len (self.fields[field]) > 1:
			string = "(" + " OR ".join(subwhereList) + ")"
		if value != None:
			string = string.replace('value',value)
		self.whereList.append (string)

	def __adddatefilter__ (self, field, context, dateone, datetwo):
		if field not in self.fields:
			raise OutOfRangeError ('Not a valid field %s not in %s'%(field, fields))
		if context not in self.dateoperators:
			raise OutOfRangeError ('Not a valid operator %s not in %s'%(context, self.textoperators))
		string = self.dateoperators[context].replace('datefield',self.fields [field])
		string = string.replace('d_one', str(dateone))
		string = string.replace('d_two', str(datetwo))

		self.whereList.append (string)


	def __constructquery__ (self):
		condition = str(" "+self.Moperator+" ").join(self.whereList)	
		self.query = "SELECT id, fullfilepath FROM results WHERE %s ORDER BY exposure_time"%condition

	def Resultentries (self):
		""" Result table iterator.
			"""
		if self.Moperator == None:
			print ("no Search was selected.\n","You have to select one search among this Saved Searches in Shotwell:")
			for entry in self.Searchtable():
				print ("\t",entry)
			return
		return self.con.execute (self.query)
	

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



