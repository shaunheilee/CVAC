# before interpreting this file, make sure this is set:
# export PYTHONPATH="/opt/Ice-3.4.2/python:test/UnitTests/python"
from __future__ import print_function
import sys, traceback
#sys.path.append('''c:\Program Files (x86)\Zeroc\Ice-3.4.2\python''')
#sys.path.append('''C:\Users\tomb\Documents\nps\git\myCVAC\CVACvisualStudio\test\UnitTests\python''')
#sys.path.append('''C:\Users\tomb\Documents\nps\git\myCVAC\CVACvisualStudio\test\UnitTests\python\cvac''')
sys.path.append('''.''')
import Ice
if "C:\Program Files (x86)\ZeroC_Ice\python" not in sys.path:
    sys.path.append("C:\Program Files (x86)\ZeroC_Ice\python")
import Ice
import IcePy
import cvac
import unittest


def getRelPath(cvacPath):
    path = cvacPath.directory.relativePath+"/"+cvacPath.filename
    return path

#
#  open a Corpus of labeled data
#
ic = Ice.initialize(sys.argv)
cs_base = ic.stringToProxy("CorpusServer:default -p 10011")
cs = cvac.CorpusServicePrx.checkedCast(cs_base)
if not cs:
    raise RuntimeError("Invalid CorpusServer proxy")

dataRoot = cvac.DirectoryPath( "corpus" );
corpusConfigFile = cvac.FilePath( dataRoot, "CvacCorpusTest.properties" )
corpus = cs.openCorpus( corpusConfigFile )

#trainCorpusDir = cvac.DirectoryPath( "corporate_logos" );
trainCorpusDir = cvac.DirectoryPath( "trainImg" );
corpus = cs.createCorpus( trainCorpusDir )
if not corpus:
    raise RuntimeError("Could not create corpus from path '"
                       +dataRoot.relativePath+"/"+trainCorpusDir+"'")

lablist = cs.getDataSet( corpus )
categories = {}
for lb in lablist:
    if lb.lab.name in categories:
        categories[lb.lab.name].append( lb )
    else:
        categories[lb.lab.name] = [lb]

# print information about this corpus
sys.stdout.softspace=False;
print('Obtained {0} labeled artifact{1} from corpus "{2}":'.format(
    len(lablist), ("s","")[len(lablist)==1], corpus.name ));
for key in sorted( categories.keys() ):
    klen = len( categories[key] )
    print("{0} ({1} artifact{2})".format( key, klen, ("s","")[klen==1] ))

#
# add some samples to a RunSet
#
pur_categories = []
pur_categories_keys = sorted( categories.keys() )
cnt = 0
for key in pur_categories_keys:
    purpose = cvac.Purpose( cvac.PurposeType.MULTICLASS, cnt )
    pur_categories.append( cvac.PurposedLabelableSeq( purpose, categories[key] ) )
    cnt = cnt+1
runset = cvac.RunSet( pur_categories )

#
# Make sure all files in the RunSet are available on the remote site;
# it is the client's responsibility to upload them if not.
#
fileserver_base = ic.stringToProxy("FileServer:default -p 10013")
fileserver = cvac.FileServicePrx.checkedCast( fileserver_base )
if not fileserver:
    raise RuntimeError("Invalid FileServer proxy")
# collect all "substrates"
substrates = set()
for plist in runset.purposedLists:
    if type(plist) is cvac.PurposedDirectory:
        raise RuntimeException("cannot deal with PurposedDirectory yet")
    elif type(plist) is cvac.PurposedLabelableSeq:
        for lab in plist.labeledArtifacts:
            if not lab.sub in substrates:
                substrates.add( lab.sub )
    else:
        raise RuntimeException("unexpected subclass of PurposedList")
# upload if not present
for sub in substrates:
    if not fileserver.exists( sub.path ):
        print('uploading file to server: ' + getRelPath( sub.path ))
        fileserver.putFile( sub.path )
    else:
        print('file already exists on server: ' + getRelPath( sub.path ))

#
# Connect to a trainer service, train on the RunSet
#
trainer_base = ic.stringToProxy("bowTrain:default -p 10003")
#trainer_base = ic.stringToProxy("BOW_Trainer:default -p 10003")
trainer = cvac.DetectorTrainerPrx.checkedCast(trainer_base)
if not trainer:
    raise RuntimeError("Invalid DetectorTrainer proxy")

# this will get called once the training is done
class TrainerCallbackReceiverI(cvac.TrainerCallbackHandler):
    detectorData = None
    def createdDetector(self, detData, current=None):
        self.detectorData = detData
        print("Finished training, obtained DetectorData of type", self.detectorData.type)

# ICE functionality to enable bidirectional connection for callback
adapter = ic.createObjectAdapter("")
callback = Ice.Identity()
callback.name = Ice.generateUUID()
callback.category = ""
tcbrec = TrainerCallbackReceiverI()
adapter.add( tcbrec, callback)
adapter.activate()
trainer.ice_getConnection().setAdapter(adapter)

# connect to trainer, initialize with a verbosity value, and train
trainer.initialize( 3 )
trainer.process( callback, runset )

if tcbrec.detectorData.type == cvac.DetectorDataType.FILE:
    print("received file: {0}/{1}".format(tcbrec.detectorData.file.directory.relativePath,
                                          tcbrec.detectorData.file.filename))
elif tcbrec.detectorData.type == cvac.DetectorDataType.BYTES:
    print("received bytes")
elif tcbrec.detectorData.type == cvac.DetectorDataType.PROVIDER:
    print("received a reference to a DetectorData provider")

#
# Connect to a detector service,
# test on the training RunSet for validation purposes
#
detector_base = ic.stringToProxy("bowTest:default -p 10004")
detector = cvac.DetectorPrx.checkedCast(detector_base)
if not detector:
    raise RuntimeError("Invalid Detector service proxy")

# this will get called when results have been found;
# replace the multiclass-ID label with the string label
class DetectorCallbackReceiverI(cvac.DetectorCallbackHandler):
    allResults = []
    def foundNewResults(self, r2, current=None):
        for res in r2.results:
            # replace ordinal class number with string
            for lbl in res.foundLabels:
                lbl.lab.name = pur_categories_keys[int(lbl.lab.name)]
        self.allResults.extend( r2.results )

# ICE functionality to enable bidirectional connection for callback
adapter = ic.createObjectAdapter("")
callback = Ice.Identity()
callback.name = Ice.generateUUID()
callback.category = ""
dcbrec = DetectorCallbackReceiverI();
adapter.add( dcbrec, callback)
adapter.activate()
detector.ice_getConnection().setAdapter(adapter)

# connect to detector, initialize with a verbosity value
# and the trained model, and run the detection on the runset
detector.initialize( 3, tcbrec.detectorData )
detector.process( callback, runset )

# print the results
print('received a total of {0} results:'.format( len( dcbrec.allResults ) ))
for res in dcbrec.allResults:
    names = []
    for lbl in res.foundLabels:
        names.append(lbl.lab.name)
    numfound = len(res.foundLabels)
    origname = ("unlabeled", res.original.lab.name)[res.original.lab.hasLabel==True]
    print("result for {0} ({1}): found {2} label{3}: {4}".format(
    res.original.sub.path.filename, origname,
        numfound, ("s","")[numfound==1], ', '.join(names) ))

quit()
