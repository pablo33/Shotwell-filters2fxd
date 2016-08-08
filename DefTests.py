#!/usr/bin/python3
# Test Configuration
import unittest
import ShotwellFilters2fxd



#####TESTS########

TM = ShotwellFilters2fxd

class itemcheck_text_values (unittest.TestCase):
	'''testing itemcheck function'''
	def test_emptystring (self):
		''' an empty string returns another empty string'''
		self.assertEqual (TM.itemcheck(""),"")

	def test_itemcheck (self):
		''' only text are addmitted as input '''
		sample_bad_values = (True, False, None, 33, 3.5)
		for values in sample_bad_values:
			self.assertRaises (TM.NotStringError, TM.itemcheck, values)

	def test_malformed_paths (self):
		''' malformed path as inputs are ommited and raises an error '''
		malformed_values = ("///","/home//")
		for inputstring in malformed_values:
			self.assertRaises (TM.MalformedPathError, TM.itemcheck, inputstring)

class ShotwellSearch_test (unittest.TestCase):
	DBpath = "TESTS/photo.db"
	DBpath = "/home/pablo/.local/share/shotwell/data/photo.db"
	classitem = TM.ShotwellSearch (DBpath)
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
			(('ANY TEXT','CONTAINS','containing text')		,u"(comment LIKE '%containing text%' OR event_comment LIKE '%containing text%' OR eventname LIKE '%containing text%' OR title LIKE '%containing text%' OR filename LIKE '%containing text%')"),
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




if __name__ == '__main__':
	unittest.main()

