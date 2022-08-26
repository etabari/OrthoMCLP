#!/usr/bin/env python
from datetime import datetime
from collections import namedtuple
import sys, os
import gzip
import random, math
from optparse import OptionParser



options = None

## User for Orthology
best_query_taxon_score = {}
## Used for the Paralogy
BestInterTaxonScore = {}
BetterHit = {}


# class SimilarSequenceLine:
# 	def __init__(self, line):
# 		column = line.strip().split('\t')

# 		self.query_id = column[0]
# 		(self.query_taxon, self.query_seq) = column[0].split('|')

# 		self.subject_id = column[1]
# 		(self.subject_taxon,self.subject_seq)  = column[1].split('|')

# 		self.evalue_mant = float(column[2])
# 		self.evalue_exp = int(column[3])

# 		#self.percent_ident = column[4]
# 		self.percent_match = float(column[4])

class SimilarSequenceLine(namedtuple('SimilarSequenceLine', 'query_id,query_taxon,query_seq,subject_id,subject_taxon,subject_seq,evalue_mant,evalue_exp,percent_match')):
	__slots__ = ()
	@classmethod
	def _fromLine(cls, line, new=tuple.__new__, len=len):
		'Make a new SimilarSequenceLine object from a sequence or iterable'
		column = line.strip().split('\t')
		(query_taxon, query_seq) = column[0].split('|')
		(subject_taxon, subject_seq) = column[1].split('|')
		iterable = (column[0], query_taxon, query_seq, column[1], subject_taxon, subject_seq, float(column[2]), int(column[3]), float(column[4]))
		result = new(cls, iterable)
		if len(result) != 9:
			raise TypeError('Expected 9 arguments, got %d' % len(result))
		return result


def readTaxonList(filename):

	taxon_list = []
	taxon_list_file = open(filename)
	for line in taxon_list_file:
		line = line.strip()
		if line:
			taxon_list += [line]
	taxon_list_file.close()
	return taxon_list

def memory_usage_resource():
	import resource
	rusage_denom = 1024.
	if sys.platform == 'darwin':
		# ... it seems that in OSX the output is different units ...
		rusage_denom = rusage_denom * rusage_denom
	mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / rusage_denom
	return round(mem, 0)


def log(s):
	global options
	print >> sys.stderr, s
	if options.logfile:
		l = open(options.logfile, 'a')
		l.write(s+'\n')
		l.close()


def writeStoOutputFiles(s, out_bh_file):
	global best_query_taxon_score, BestInterTaxonScore, options
	try:
		(cutoff_exp, cutoff_mant) = best_query_taxon_score[(s.query_id, s.subject_taxon)]

		if (
			s.query_taxon != s.subject_taxon and
			(s.evalue_exp == 0 or s.evalue_exp < options.evalueExponentCutoff) and
			s.percent_match > options.percentMatchCutoff and
			(s.evalue_mant < 0.01 or s.evalue_exp==cutoff_exp and s.evalue_mant==cutoff_mant)
		   ):
			out_bh_file.write('{0}\t{1}\t{2}\t{3}\n'.format(s.query_seq, s.subject_id, s.evalue_exp, s.evalue_mant))

	except KeyError:
		pass

	if options.outInParalogTempFolder:
		try:
			(cutoff_exp, cutoff_mant) = BestInterTaxonScore[s.query_id]

			if (s.query_taxon == s.subject_taxon and
				s.query_id != s.subject_id and
                (s.evalue_exp== 0 or s.evalue_exp <= options.evalueExponentCutoff) and
				s.percent_match >= options.percentMatchCutoff and
				(s.evalue_mant < 0.01 or s.evalue_exp<cutoff_exp or (s.evalue_exp == cutoff_exp and s.evalue_mant<=cutoff_mant))
			   ):

				# try:
				# 	BetterHit[(s.query_seq, s.subject_seq)] += [(s.evalue_exp, s.evalue_mant)]
				# except KeyError:
				BetterHit[(s.query_seq, s.subject_seq)] = (s.evalue_exp, s.evalue_mant)

		except KeyError:
			# Include the ones with
			if (
				s.query_taxon == s.subject_taxon and
				(options.keepOrthoMCLBug or s.query_id != s.subject_id) and  #### THIS IS an OrthoMCL bug
				(s.evalue_exp == 0 or s.evalue_exp <= options.evalueExponentCutoff) and
				s.percent_match >= options.percentMatchCutoff
			   ):
				# try:
				# 	BetterHit[(s.query_seq, s.subject_seq)] += [(s.evalue_exp, s.evalue_mant)]
				# except KeyError:
				BetterHit[(s.query_seq, s.subject_seq)] = (s.evalue_exp, s.evalue_mant)


if __name__ == '__main__':
	usage = "This is STEP 5.1 of PorthoMCL.\n\nusage: %prog options\n"
	parser = OptionParser(usage)

	parser.add_option("-t", "--taxonlist", dest="taxonlistfile", help="A single column file containing the list of taxon to work with")
	parser.add_option("-x", "--index", dest="index", help="An integer number identifying which taxon to work on [1-size_of_taxon_list]", type='int')

	parser.add_option('-s', '--inSimSeq', dest='inSimSeq', help='Input folder that contains split similar sequences files (ss files)')

	parser.add_option('-b', '--outBestHitFolder', dest='outBestHitFolder', help='folder that will stores Best Hit files (If not set, current folder)')
	parser.add_option('-q', '--outInParalogTempFolder', dest='outInParalogTempFolder', help='folder to generate best InParalogTemp evalue scores (pt files) (required only for Paralogs)')
	parser.add_option("-l", "--logfile", dest="logfile", help="log file (optional, if not supplied STDERR will be used)")


	parser.add_option('', '--evalueExponentCutoff', dest='evalueExponentCutoff', help='evalue Exponent Cutoff (a nebative value, default=-5)', default=-5, type='int')
	parser.add_option('', '--percentMatchCutoff', dest='percentMatchCutoff', help='percent Match Cutoff (integer value, default=50)', default=50, type='int')
	parser.add_option('', '--cacheInputFile', dest='cacheInputFile', help='Cache input file or read it again. (Only use if I/O is very slow)', default=False, action="store_true")
	parser.add_option('', '--keepOrthoMCLBug', dest='keepOrthoMCLBug', help='Keep the OrthoMCL bug in creating Temporary Paralogs files (pt files) where self hits are included', default=False, action="store_true")

	#

	(options, args) = parser.parse_args()


	if len(args) != 0 or not options.taxonlistfile or not options.inSimSeq or not options.index:
		parser.error("incorrect arguments.\n\t\tUse -h to get more information or refer to the MANUAL.md")


	log('{2} | Best Hit | {0} | {1} | {3} | {4} MB | {5}'.format(1, 'reading taxon list', options.index, '', memory_usage_resource(), datetime.now()))
	taxon_list = readTaxonList(options.taxonlistfile)

	if options.index <= 0 or options.index > len(taxon_list):
		log('{2} | Best Hit | {0} | {1} | {3} | {4} MB | {5}'.format('ERROR', 'Error in index', options.index, '', memory_usage_resource(), datetime.now()))
		exit()

	taxon1s = taxon_list[options.index - 1]


	if options.cacheInputFile:
		log('{2} | Best Hit | {0} | {1} | {3} | {4} MB | {5}'.format('OPTION', 'Caching Input files', options.index, taxon1s, memory_usage_resource(), datetime.now()))


	log('{2} | Best Hit | {0} | {1} | {3} | {4} MB | {5}'.format(2, 'Reading similar sequences (ss file)', options.index, taxon1s, memory_usage_resource(), datetime.now()))


	if options.outBestHitFolder and not os.path.exists(options.outBestHitFolder):
		os.makedirs(options.outBestHitFolder)

	if options.outInParalogTempFolder and not os.path.exists(options.outInParalogTempFolder):
		os.makedirs(options.outInParalogTempFolder)

	input_file_cache = []

	with open(os.path.join(options.inSimSeq, taxon1s+'.ss.tsv')) as input_file:
		for line in input_file:

			ss = SimilarSequenceLine._fromLine(line)


			if options.cacheInputFile:
				input_file_cache += [ss]


			if ss.query_taxon != ss.subject_taxon:

				try:
					best_query_taxon_score[(ss.query_id, ss.subject_taxon)] += [(ss.evalue_mant, ss.evalue_exp)]
				except:
					best_query_taxon_score[(ss.query_id, ss.subject_taxon)] = [(ss.evalue_mant, ss.evalue_exp)]


	for (query_id,subject_taxon) in best_query_taxon_score:

		evalues = best_query_taxon_score[(query_id, subject_taxon)]
		
		min_exp = sys.maxint  #min(evalues, key = lambda t: t[1])

		min_mants = []

		for (evalue_mant, evalue_exp) in evalues:
			if evalue_exp < min_exp:
				min_exp = evalue_exp
				min_mants += [evalue_mant]

			if evalue_mant == 0 and evalue_exp == 0:
				#min_mants += [evalue_mant]
				min_exp = 0
				min_mants = [0]
				break

		best_query_taxon_score[(query_id,subject_taxon)] = (min_exp, min(min_mants))


	if options.outInParalogTempFolder:


		# log('{2} | Best Hit | {0} | {1} | * | {3} MB | {4}'.format(3 , 'Creating bestQueryTaxonScore (q-t file)', options.index, memory_usage_resource(), datetime.now() ))
		# with open(os.path.join(options.outQueryTaxonScoreFolder, taxon1s+'.q-t.tsv'), 'w') as out_file:
		# 	for (query_id,subject_taxon) in sorted(best_query_taxon_score):
		# 		(ev_exp, ev_mant) = best_query_taxon_score[(query_id,subject_taxon)]
		# 		out_file.write('{0}\t{1}\t{2}\t{3}\n'.format(query_id, subject_taxon, ev_exp, ev_mant))


		log('{2} | Best Hit | {0} | {1} | {3} | {4} MB | {5}'.format(3 , 'Creating BestInterTaxonScore Matirx', options.index,taxon1s, memory_usage_resource(), datetime.now() ))


		for (query_id,subject_taxon) in best_query_taxon_score:

			(ev_exp, ev_mant) = best_query_taxon_score[(query_id,subject_taxon)]
			
			try:
				(min_exp, mants) = BestInterTaxonScore[query_id]
				
				if min_exp == 0 and mants[0] == 0:
					pass
				elif ev_exp < min_exp:
					BestInterTaxonScore[query_id] = (ev_exp, [ev_mant])
				elif ev_exp == min_exp:
					BestInterTaxonScore[query_id] = (ev_exp, mants+[ev_mant])
			except:
				BestInterTaxonScore[query_id] = (ev_exp, [ev_mant])


		for query_id in BestInterTaxonScore:

			(ev_exp, ev_mants) = BestInterTaxonScore[query_id]
			BestInterTaxonScore[query_id] = (ev_exp, min(ev_mants))


	log('{2} | Best Hit | {0} | {1} | {3} | {4} MB | {5}'.format(4 , 'Creating BestHit file needed for Orthology (bh file)', options.index, taxon1s, memory_usage_resource(), datetime.now() ))

	BestHit = {}

	if not options.outBestHitFolder:
		options.outBestHitFolder = '.'

	out_bh_file = open(os.path.join(options.outBestHitFolder, taxon1s+'.bh.tsv') ,'w')

	if not options.cacheInputFile:
		with open(os.path.join(options.inSimSeq, taxon1s+'.ss.tsv')) as input_file:
			for line in input_file:
				s = SimilarSequenceLine._fromLine(line)
				writeStoOutputFiles(s, out_bh_file)


	else:

		for s in input_file_cache:
			writeStoOutputFiles(s, out_bh_file)


	out_bh_file.close()



	if options.outInParalogTempFolder:
		log('{2} | Best Hit | {0} | {1} | {3} | {4} MB | {5}'.format(5 , 'Creating InParalogTemp file needed for InParalogs (pt file)', options.index, taxon1s, memory_usage_resource(), datetime.now() ))

		out_pt_file = open(os.path.join(options.outInParalogTempFolder, taxon1s+'.pt.tsv') ,'w')

		for (seq1, seq2) in BetterHit:
			
			if seq1 < seq2:

				(bh1_evalue_exp, bh1_evalue_mant) = BetterHit[(seq1, seq2)]

				try:
					(bh2_evalue_exp, bh2_evalue_mant) =  BetterHit[(seq2, seq1)]
				except:
					continue

				if bh1_evalue_mant < 0.01 or bh2_evalue_mant < 0.01:
					unnormalized_score = (bh1_evalue_exp + bh2_evalue_exp) / -2 
				else:
					unnormalized_score = (math.log10(bh1_evalue_mant * bh2_evalue_mant) + bh1_evalue_exp + bh2_evalue_exp) / -2


				out_pt_file.write('{0}\t{1}\t{2}\n'.format(seq1, seq2, unnormalized_score))


		out_pt_file.close()








	log('{2} | Best Hit | {0} | {1} | {3} | {4} MB | {5}'.format(6 , 'Done', options.index, taxon1s, memory_usage_resource(), datetime.now() ))







	



