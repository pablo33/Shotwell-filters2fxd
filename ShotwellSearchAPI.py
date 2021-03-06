#!/usr/bin/python3
# Dependencies
import sqlite3, os, shutil, sys #logging, re
import unicodedata  # To substitute áéíóú öü ñÑ

class ShotwellSearch:
	""" Handles a Shotwell Database in order to access to its Saved Searches.
		It makes a copy of the Shotwell Database to work with.
		It makes an auxiliar table to perform Shotwell Saved Searches queries.
		It returns the Saved Searches Query as an iterator.
		It returns the file entries of a Saved Search as an iterator.

		Use the iterable method "Searchtable()" to retrieve the Shotwell saved searches.
		Use "Search(id)" to manage this Search id across this class.
		Use the "searchid" property to see the id of the selected search.
		Use the "searchname" property to see the search name.
		Use the "query" property to see the SQL statement on the sqlite3 temp database.
		Use the "Resultentries" method as iterable to iterate across de searched results.
		"""

	# Error Handling
	class NotStringError(ValueError):
		pass
	class MalformedPathError(ValueError):
		pass
	class OutOfRangeError(ValueError):
		pass


	# ------ utils --------
	class Progresspercent:
		''' Show the progression of an activity in percentage
		it is swhon on the same line'''
		def __init__ (self, maxValue, title = '', showpartial=True):
			if title != '':
			    self.title = " " + title + ":"  # Name of the 
			else:
			    self.title = " "
			self.maxValue = maxValue
			self.partial = showpartial

		def showprogress (self, p):
			'''
			Shows the progress in percentage vía stdout, and returns its value again.
			'''
			progressvalue = (p / self.maxValue * 100)
			progresspercent = "%.1f"%progressvalue + "%"
			if self.partial == True:
			        progresspartial = "(" + str(p) + "/" + str (self.maxValue) + ")"
			else:
			        progresspartial = ''
			progresstext = self.title + progresspartial + " " + progresspercent
			sys.stdout.write (progresstext + chr(8)*len(progresstext))
			if p == self.maxValue:
			        sys.stdout.write('\n')
			sys.stdout.flush()
			return progresspercent

	def __itemcheck__ (self, pointer):
		''' returns what kind of a pointer is '''

		if type(pointer) is not str:
			raise ShotwellSearch.NotStringError ('Bad input, it must be a string')
		if pointer.find("//") != -1 :
			raise ShotwellSearch.MalformedPathError ('Malformed Path, it has double slashes')
		
		if os.path.isfile(pointer):
			return 'file'
		if os.path.isdir(pointer):
			return 'folder'
		if os.path.islink(pointer):
			return 'link'
		return ""

	def __elimina_tildes__ (self, s):
	   string = ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))
	   return string.lower ()


	# Main Search operators
	ops = {
		'ANY'	:'OR',
		'ALL'	:'AND',
		'NONE'	:'AND NOT'
		}

	# field Shotwell DB Search conversion to results field,
	fields = {
		'ANY_TEXT': 	('comment','event_comment','event_name','title','filename','tags'),
		'COMMENT': 		('comment','event_comment'),
		'EVENT_NAME': 	('event_name',),
		'FILE_NAME':	('filename',),
		'TAG':			('tags',),
		'TITLE':		('title',),
		'DATE': 		'exposure_time',
		'RATING':		'rating',
		'FLAG_STATE':	'flags',
		}

	# text operators SQL conversion string
	textoperators = {
		'CONTAINS': u"LIKE '%value%'",
		'IS_EXACTLY': u"= 'value'",
		'STARTS_WITH': u"LIKE 'value%'",
		'ENDS_WITH': u"LIKE '%value'",
		'DOES_NOT_CONTAIN' : u"NOT LIKE '%value%'",
		'IS_SET' : u"IS NOT NULL",
		'IS_NOT_SET' : u"IS NULL",
		}

	# date operators SQL conversion string
	dateoperators = {
		'EXACT': 'datefield = d_one',
		'AFTER': 'datefield >= d_one',
		'BEFORE': 'datefield <= d_one',
		'BETWEEN': '(datefield >= d_one AND datefield <= d_two)',
		'IS_NOT_SET': 'datefield = 0',
		}

	# rating operators SQL conversion string
	ratingoperators = {
		'AND_LOWER':	'<=',
		'ONLY': 		'=',
		'AND_HIGHER': 	'>=',
	}

	# Flagged operators SQL conversion string
	flagoperators = {
		'FLAGGED': 	'= 16',
		'UNFLAGGED': 	'= 0',
	}

	


	searchid = None
	searchname = None
	Moperator = None
	query = None


	def __init__(self, DBpath = os.path.join(os.getenv('HOME'),".local/share/shotwell/data/photo.db")):
		""" makes its own tmp DB an works on it """
		# Copying DBfile
		if self.__itemcheck__ (DBpath) != 'file':
			print ('Can\'t locate Shotwell Database.', DBpath)
			exit()
		tmpDB = 'ShotwellCopyTempDB.sqlite3'
		if self.__itemcheck__ (tmpDB) == 'file':
			os.remove(tmpDB)
		shutil.copy (DBpath, tmpDB)
		print ("Don't worry, we are working on a temporal copy of the Shotwell Database.")
		self.con = sqlite3.connect (tmpDB)

		__Schema__, __appversion__ = self.con.execute ("SELECT schema_version, app_version FROM versiontable").fetchone()
		if __Schema__ < 20 :
			print ("This utility may not work properly with an Shotwell DataBase Schema minor than 20")
			print ("It is recomended use Shtwell 0.22.0 or later")
			print ("Actual DB Schema is %s"%__Schema__)
			print ("Actual Shotwell Version %s"%__appversion__)

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
				tags TEXT, \
				editable_id INTEGER, \
				transformations TEXT \
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
					null as tags,\
					editable_id,\
					transformations\
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
					null as tags,\
					editable_id,\
					transformations\
				FROM phototable\
				WHERE event_id = -1 and exposure_time = 0")
		self.con.commit ()
			
		# Extracting and setting tags and filenames // converting to lower, removing tildes, and Rare characters. (ñ >> n)
		Taskname = "Creating the Tag table... this may take a little time..."
		Totalentries = self.con.execute ("SELECT COUNT (id) FROM results").fetchone()[0]
		progressindicator = self.Progresspercent ( Totalentries, title= Taskname, showpartial=True  )
		
		cursor = self.con.cursor()
		cursor.execute ("SELECT id, fullfilepath, title, event_name, event_comment FROM results ORDER BY id")
		i = 0
		for ID, Fullfilepath, Title, Event_name, Event_comment in cursor:
			i += 1
			progressindicator.showprogress (i)
			Filename = os.path.splitext(os.path.basename(Fullfilepath))[0]
			# Finding tags  (thumb000000000000000f,)
			thumb = u"'%"+"thumb%016x,"%ID+u"%'"
			tagstring = ''
			for entry in self.con.execute ("SELECT name FROM tagtable WHERE photo_id_list LIKE %s"%thumb):
				tagstring+= ' '+entry[0][1:].split ("/").pop()  # fetchs the last tag
			if tagstring == '':
				tagstring = None
			else:
				# aplying transformations >> lower and without tildes ..... Well, Shotwell modifies this searches on tags, so lets do it.
				# Tags
				tagstring = self.__elimina_tildes__ (tagstring)
			# Title
			if Title is not None:
				Title = self.__elimina_tildes__ (Title)
			# Event names
			if Event_name is not None: 
				Event_name = self.__elimina_tildes__ (Event_name)
			# Event comments
			if Event_comment is not None:
				Event_comment = self.__elimina_tildes__ (Event_comment)
			# Filename
			Filename = self.__elimina_tildes__(Filename)

			self.con.execute("UPDATE results SET filename = ?, tags = ?, title = ?, event_name = ?, event_comment = ?  WHERE id = ?", (Filename,tagstring,Title,Event_name,Event_comment,ID))
		print ("Done!.")

		self.con.commit()
		print ("Class ShotwellSearch initialized.")

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
		self.searchname, moperator = entry
		moperator = moperator.upper()
		if moperator not in self.ops:
			raise ShotwellSearch.OutOfRangeError ('This main operator is not allowed (%s)'%moperator)
			return
		self.Moperator = self.ops[moperator]
		self.whereList = list()
		# Text filters:
		for entry in self.con.execute ("SELECT search_type, context, text FROM SavedSearchDBTable_Text WHERE search_id = %s"%searchid):
			self.__addtextfilter__ (entry[0],entry[1],entry[2])
		for entry in self.con.execute ("SELECT search_type, context, date_one, date_two FROM SavedSearchDBTable_Date WHERE search_id = %s"%searchid):
			self.__adddatefilter__ (entry[0],entry[1],entry[2], entry[3])
		for entry in self.con.execute ("SELECT search_type, rating, context FROM SavedSearchDBTable_Rating WHERE search_id = %s"%searchid):
			self.__addratingfilter__ (entry[0],entry[1],entry[2])
		for entry in self.con.execute ("SELECT search_type, flag_state FROM SavedSearchDBTable_Flagged WHERE search_id = %s"%searchid):
			self.__addflagfilter__ (entry[0],entry[1])


		self.__constructquery__()

	def __addtextfilter__ (self, field, operator, value):
		if field not in self.fields:
			raise ShotwellSearch.OutOfRangeError ('Not a valid field %s not in %s'%(field, self.fields))
		if operator not in self.textoperators:
			raise ShotwellSearch.OutOfRangeError ('Not a valid operator %s not in %s'%(operator, self.textoperators))
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
		if field != 'DATE':
			raise ShotwellSearch.OutOfRangeError ('Not a valid field %s not in %s'%(field, self.fields))
		if context not in self.dateoperators:
			raise ShotwellSearch.OutOfRangeError ('Not a valid operator %s not in %s'%(context, self.dateoperators))
		string = self.dateoperators[context].replace('datefield',self.fields [field])
		string = string.replace('d_one', str(dateone))
		string = string.replace('d_two', str(datetwo))
		self.whereList.append (string)

	def __addratingfilter__ (self, field, rating, context ):
		if field != 'RATING':
			raise ShotwellSearch.OutOfRangeError ('Not a valid field %s not in %s'%(field, self.fields))
		if context not in self.ratingoperators:
			raise ShotwellSearch.OutOfRangeError ('Not a valid operator %s not in %s'%(context, self.ratingoperators))
		string = self.fields [field] + " " + self.ratingoperators[context] + " " + str(rating)
		self.whereList.append (string)

	def __addflagfilter__ (self, field, context):
		if field != 'FLAG_STATE':
			raise ShotwellSearch.OutOfRangeError ('Not a valid field %s not in %s'%(field, self.fields))
		if context not in self.flagoperators:
			raise ShotwellSearch.OutOfRangeError ('Not a valid operator %s not in %s'%(context, self.flagoperators))
		string = self.fields [field] + " " + self.flagoperators[context]
		self.whereList.append (string)



	def __constructquery__ (self):
		if len (self.whereList) >= 1:
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