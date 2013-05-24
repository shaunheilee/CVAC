#
# A demo for the Easy Computer Vision library.
#

import sys

#Add the lib/python directory to get packages
sys.path.append('''../../lib/python''')
import paths
import cvac

import easy


#
# First, a super quick and easy teaser:
#
# TODO: doesn't work yet because the image file argument doesn't get turned into a RunSet yet.
#detector = easy.getDetector( "bowTest:default -p 10004" )
#results = easy.detect( detector, "detectors/bowUSKOCA.zip", "testImg/TestCaFlag.jpg" )
#easy.printResults( results )

#
# Obtain a set of labeled data from a Corpus,
# print dataset information about this corpus
#
cs = easy.getCorpusServer("CorpusServer:default -p 10011")
#corpus = easy.openCorpus( cs, "corpus/CvacCorpusTest.properties" )
#corpus = easy.openCorpus( cs, "corporate_logos" );
corpus = easy.openCorpus( cs, "trainImg" );
categories, lablist = easy.getDataSet( cs, corpus )
print 'Obtained {0} labeled artifact{1} from corpus "{2}":'.format(
    len(lablist), ("s","")[len(lablist)==1], corpus.name );
easy.printCategoryInfo( categories )

#
# add all samples from corpus to a RunSet,
# also obtain a mapping from class ID to label name
#
res = easy.createRunSet( categories )
runset = res['runset']
classmap = res['classmap']

#
# Make sure all files in the RunSet are available on the remote site;
# it is the client's responsibility to upload them if not.
#
fileserver = easy.getFileServer( "FileService:default -p 10110" )
easy.putAllFiles( fileserver, runset )

#
# Connect to a trainer service, train on the RunSet
#
trainer = easy.getTrainer( "bowTrain:default -p 10003" )
trainedModel = easy.train( trainer, runset )
print "Training model stored in file: " + easy.getFSPath( trainedModel.file )

#
# Connect to a detector service,
# test on the training RunSet for validation purposes;
# The detect call takes the detector, the trained model, the
# runset, and a mapping from purpose to label name
#
detector = easy.getDetector( "bowTest:default -p 10004" )
results = easy.detect( detector, trainedModel, runset, classmap )
easy.printResults( results )

quit()