#!/usr/bin/python3
# Test Configuration
import unittest, shutil, os
from ShotwellSearchAPI import ShotwellSearch
import ShotwellSearch2fxd



#####TESTS########

TM = ShotwellSearch
TM2= ShotwellSearch2fxd

class itemcheck_text_values (unittest.TestCase):
	'''testing itemcheck function'''

	def test_emptystring (self):
		''' an empty string returns another empty string'''
		self.assertEqual (TM.__itemcheck__(self, ""),"")

	def test_itemcheck (self):
		''' only text are addmitted as input '''
		sample_bad_values = (True, False, None, 33, 3.5)
		for values in sample_bad_values:
			self.assertRaises (TM.NotStringError, TM.__itemcheck__, self, values)

	def test_malformed_paths (self):
		''' malformed path as inputs are ommited and raises an error '''
		malformed_values = ("///","/home//")
		for inputstring in malformed_values:
			self.assertRaises (TM.MalformedPathError, TM.__itemcheck__, self,inputstring)

class ShotwellSearch_test (unittest.TestCase):
	DBpath = "TESTS/photo.db"
	DBpath = "/home/pablo/.local/share/shotwell/data/photo.db"
	classitem = ShotwellSearch (DBpath)
	classitem.whereList = []  # Needed to initialize some search for this test

	def test___addtextfilter__ (self):
		""" Adding Search filters to the query"""
		known_values = (
			(('FILE_NAME','CONTAINS','valuestring')			,u"filename LIKE '%valuestring%'"),
			(('COMMENT','STARTS_WITH','otherstring')		,u"(comment LIKE 'otherstring%' OR event_comment LIKE 'otherstring%')"),
			(('EVENT_NAME','ENDS_WITH','endingstring')		,u"event_name LIKE '%endingstring'"),
			(('TAG','DOES_NOT_CONTAIN','containing string'),u"tags NOT LIKE '%containing string%'"),
			(('TITLE','IS_NOT_SET',None)					,u"title IS NULL"),
			(('TITLE','IS_SET',None)						,u"title IS NOT NULL"),
			(('ANY_TEXT','CONTAINS','containing text')		,u"(comment LIKE '%containing text%' OR event_comment LIKE '%containing text%' OR event_name LIKE '%containing text%' OR title LIKE '%containing text%' OR filename LIKE '%containing text%' OR tags LIKE '%containing text%')"),
			(('COMMENT','IS_SET', None)						,u"(comment IS NOT NULL OR event_comment IS NOT NULL)"),
			(('COMMENT','IS_NOT_SET',None)					,u"(comment IS NULL OR event_comment IS NULL)"),
			(('FILE_NAME','IS_EXACTLY','filenametext')		,u"filename = 'filenametext'"),
			(('TAG','IS_EXACTLY','tagtext')					,u"tags LIKE '% tagtext%'"),
			)
		for key, match in known_values:
			self.classitem.__addtextfilter__(key[0],key[1],key[2])
			self.assertIn (match, self.classitem.whereList)
			self.classitem.whereList = []

	def test___adddatefilter__ (self):
		""" Adding Search filters to the query"""
		known_values = (
			(('DATE','EXACT',1471212000, 1470607200)					,u"exposure_time = 1471212000"),
			(('DATE','AFTER',1470780000, 1470607200)					,u"exposure_time >= 1470780000"),
			(('DATE','BEFORE',1472076000, 1470607200)					,u"exposure_time <= 1472076000"),
			(('DATE','BETWEEN',1470002400, 1472594400)					,u"(exposure_time >= 1470002400 AND exposure_time <= 1472594400)"),
			(('DATE','IS_NOT_SET',1470607200, 1470607200)				,u"exposure_time = 0"),
			)
		for key, match in known_values:
			self.classitem.__adddatefilter__(key[0],key[1],key[2], key[3])
			self.assertIn (match, self.classitem.whereList)
			self.classitem.whereList = []

	def test___addratingfilter__ (self):
		""" Adding Search filters to the query"""
		known_values = (
			(('RATING',-1 ,'AND_HIGHER')	,"rating >= -1"),
			(('RATING', 0 ,'ONLY')			,"rating = 0"),
			(('RATING', 1 ,'AND_LOWER')		,"rating <= 1"),
			(('RATING', 2 ,'ONLY')			,"rating = 2"),
			(('RATING', 3 ,'AND_LOWER')		,"rating <= 3"),
			(('RATING', 4 ,'AND_HIGHER')	,"rating >= 4"),
			(('RATING', 5 ,'AND_HIGHER')	,"rating >= 5"),
			)
		for key, match in known_values:
			self.classitem.__addratingfilter__(key[0],key[1],key[2])
			self.assertIn (match, self.classitem.whereList)
			self.classitem.whereList = []

	def test__addflagfilter__(self):
		""" Adding Search filters to the query"""
		known_values = (
			(('FLAG_STATE', 'FLAGGED')		,"flags = 16"),
			(('FLAG_STATE', 'UNFLAGGED')	,"flags = 0"),
			)
		for key, match in known_values:
			self.classitem.__addflagfilter__ (key[0],key[1])
			self.assertIn (match, self.classitem.whereList)
			self.classitem.whereList = []

class ShotwellSearch2fxd_test (unittest.TestCase):
	DBpath = "/home/pablo/.local/share/shotwell/data/photo.db"
	testuserpath = "TESTS/fxd/"
	SR = ShotwellSearch (DBpath)
	if os.path.isdir(testuserpath):
		shutil.rmtree(testuserpath)
	os.makedirs (testuserpath)


	def test_Writefxd (self):
		""" Write one fxd file for selected search """
		for entry in self.SR.Searchtable ():
			self.SR.Search (entry[0])  # Selecting the first search, for example.
			TM2.Writefxd (self.SR, self.testuserpath)




if __name__ == '__main__':
	unittest.main()

