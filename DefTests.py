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

	def test_mainoperator (self):
		""" Set main SQL operator in Class"""
		known_values = (
			('ALL','AND'),
			('any','OR'),
			('nOnE','AND NOT')
			)

		for key, match in known_values:
			self.classitem.mainoperator(key)
			result = self.classitem.Moperator
			self.assertEqual(match, result)

	def test_addfilter (self):
		""" Set main SQL operator in Class"""
		known_values = (
			(('FILE NAME','CONTAINS','valuestring')		,u"filename like '%value%'"),
			)

		for key, match in known_values:
			self.classitem.addfilter(key[0],key[1],key[2])
			self.assertIn (match, self.classitem.whereList)


if __name__ == '__main__':
	unittest.main()

