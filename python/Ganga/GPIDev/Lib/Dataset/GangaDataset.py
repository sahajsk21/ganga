#\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\#

import tempfile
import fnmatch
from Ganga.GPIDev.Lib.Dataset import Dataset
from Ganga.GPIDev.Schema import *
from Ganga.GPIDev.Base import GangaObject
from Ganga.Utility.Config import getConfig, ConfigError
import Ganga.Utility.logging
from Ganga.GPIDev.Base.Proxy import GPIProxyObjectFactory
from Ganga.GPIDev.Lib.Job.Job import Job,JobTemplate
from GangaDirac.Lib.Backends.DiracUtils import get_result
logger = Ganga.Utility.logging.getLogger()

#\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\#

class GangaDataset(Dataset):
    '''Class for handling generic datasets of input files
    '''
    schema = {}
    docstr = 'List of File objects'
    schema['files'] = GangaFileItem(defvalue=[],typelist=['str','Ganga.GPIDev.Lib.File.IGangaFile.IGangaFile'],sequence=1,doc="list of file objects that will be the inputdata for the job")
    schema['treat_as_inputfiles'] = SimpleItem(defvalue=False,doc="Treat the inputdata as inputfiles, i.e. copy the inputdata to the WN")
    _schema = Schema(Version(3,0), schema)
    _category = 'datasets'
    _name = "GangaDataset"
    _exportmethods = [ ]

    def __init__(self, files=[]):
        super(GangaDataset, self).__init__()
        self.files = files

    def __len__(self):
        """The number of files in the dataset."""
        result = 0
        if self.files: result = len(self.files)
        return result

    def __nonzero__(self):
        """This is always True, as with an object."""
        return True

    def __getitem__(self,i):
        '''Proivdes scripting (e.g. ds[2] returns the 3rd file) '''
        if type(i) == type(slice(0)):
            ds = GangaDataset(files=self.files[i])
            return GPIProxyObjectFactory(ds)
        else:
            return GPIProxyObjectFactory(self.files[i])

    def isEmpty(self): return not bool(self.files)

    def extend(self,files,unique=False):
        '''Extend the dataset. If unique, then only add files which are not
        already in the dataset.'''
        from Ganga.GPIDev.Base import ReadOnlyObjectError
        if not hasattr(files,"__getitem__"):
            raise GangaException('Argument "files" must be a iterable.')
        if self._parent is not None and self._parent._readonly():
            raise ReadOnlyObjectError('object Job#%s  is read-only and attribute "%s/inputdata" cannot be modified now'%(self._parent.id, self._name))
        names = self.getFileNames()
        files = [f for f in files] # just in case they extend w/ self
        for f in files:
            file = getDataFile(f)
            if file is None: file = f
            if unique and file.name in names: continue
            self.files.append(file)

    def getFilenameList(self):
        "return a list of filenames to be created as input.txt on the WN"
        filelist = []
        for f in self.files:
            try:
                filelist += f.getFilenameList()
            except NotImplementedError:
                logger.warning("getFilenameList not implemented for File '%s'" % sf._name)

        return filelist

    def difference(self,other):
        '''Returns a new data set w/ files in this that are not in other.'''
        other_files = other.getFullFileNames()
        files = set(self.getFullFileNames()).difference(other_files)
        data = GangaDataset()
        data.__construct__([list(files)])
        data.depth = self.depth
        return GPIProxyObjectFactory(data)

    def isSubset(self,other):
        '''Is every file in this data set in other?'''
        return set(self.getFileNames()).issubset(other.getFileNames())

    def isSuperset(self,other):
        '''Is every file in other in this data set?'''
        return set(self.getFileNames()).issuperset(other.getFileNames())

    def symmetricDifference(self,other):
        '''Returns a new data set w/ files in either this or other but not
        both.'''
        other_files = other.getFullFileNames()
        files = set(self.getFullFileNames()).symmetric_difference(other_files)
        data = GangaDataset()
        data.__construct__([list(files)])
        data.depth = self.depth
        return GPIProxyObjectFactory(data)

    def intersection(self,other):
        '''Returns a new data set w/ files common to this and other.'''
        other_files = other.getFullFileNames()
        files = set(self.getFullFileNames()).intersection(other_files)
        data = GangaDataset()
        data.__construct__([list(files)])
        data.depth = self.depth
        return GPIProxyObjectFactory(data)

    def union(self,other):
        '''Returns a new data set w/ files from this and other.'''
        files = set(self.getFullFileNames()).union(other.getFullFileNames())
        data = GangaDataset()
        data.__construct__([list(files)])
        data.depth = self.depth
        return GPIProxyObjectFactory(data)

#\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\#