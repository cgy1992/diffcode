#!/usr/bin/env python
# -*- coding: utf-8 -*-
import filecmp
import difflib
import ConfigParser
import re,random,urllib2,json,urllib,logging
import os,sys
import subprocess
from datetime import date
import time

ENVERONMENT = "dev"

LOG_FILE_PATH =   os.path.join( os.getcwd(), "log","foldercmp_"+date.today().strftime("%Y%m%d")+'.log')
logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename=LOG_FILE_PATH)


def log(m):
    stime = time.strftime( '%Y-%m-%d %X' , time.localtime() )
    logging.debug(stime+" "+str(m))

def assertSuccessShell(shellerroutput):
    if shellerroutput != "":
        log(shellerroutput)
        raise Exception(shellerroutput)
    pass

class FileSystem:
    def __init__(self,ns,param):
        #self.uri = config.get('cmomon','')
        pass

    def readyFiles(self,toFilePath):
        pass

    def getFilePath(self):
        return ''


class LocalFileSystem(FileSystem):
    def __init__(self,session,ns,param):
        self.uri = param[ns]['uri'] #config.get('common',ns+'.uri')
        #print self.uri

    def getFilePath(self):
        return self.uri

class SVNFileSystem(FileSystem):
    '''svn的子模块'''

    def __init__(self,session,ns,param):
        ''' @param ns 左边或者右边，是一个命名空间，看session怎么得调用 '''
        self.uri = param[ns]['uri'] #config.get('common',ns+'.uri')
        self.username = param[ns]['username'] #config.get('common',ns+'.username')
        self.password = param[ns]['password'] #config.get('common',ns+'.password')

    def readyFiles(self,toFilePath):
        log("svn readyFiles")
        p = subprocess.Popen("rm -rf {0}".format(toFilePath), stdout=subprocess.PIPE, shell=True)
        log("rm -rf {0}".format(toFilePath))
        (output, err) = p.communicate()

        self.__exportFile(toFilePath)

    def __exportFile(self,toFilePath):
        cmd = "svn export --username {username} --password {password} {uri} {toFilepath}".format(
                   username=self.username,password=self.password,uri=self.uri, toFilepath=toFilePath)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
        log(cmd)
        (output, err) = p.communicate()
        assertSuccessShell(err)
        #print "Revision is", output
        pass

class SSHFileSystem(FileSystem):
    PROXY = "http://192.168.195.128:8899/"
    def __init__(self,session,ns,param):
        self.session = session

        self.uri = param[ns]['uri']
        #self.uri = config.get('common',ns+'.uri')
        self.host = param[ns]['host']   #config.get('common',ns+".host")
        self.username = param[ns]['username'] #config.get('common',ns+'.username')
        self.password = param[ns]['password'] #config.get('common',ns+'.password')
        self.filename = session+date.today().strftime("%Y%m%d")+str(random.randint(100,1000))+".tar"

        self.exclude = param[ns]['exclude'].replace(" ","")

        ##TODO(需要解决，不赋值)
        if ENVERONMENT == 'dev':
            self.__class__.PROXY = "http://192.168.195.128:8899/download"
        elif ENVERONMENT == 'product':
            self.__class__.PROXY = "http://gz.proxy.diffcode.isd.com/download"


    def readyFiles(self,toFilePath):
        p = subprocess.Popen("rm -rf {0}; mkdir -p {0}".format(toFilePath), stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
        log("rm -rf {0}".format(toFilePath))
        (output, err) = p.communicate()
        assertSuccessShell(err)
        
        log("ssh readyFiles")
        self.__download()
        #print "tar xf ./download/{0} -C {1}".format(self.filename,toFilePath)
        cmd = "tar xf ./download/{filename} -C {toFilePath}".format(filename = self.filename,toFilePath=toFilePath)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
        log(cmd)
        (output, err) = p.communicate()
        assertSuccessShell(err)

        pass
    def __download(self):
        data = dict(username=self.username,host=self.host,password=self.password,
                    filepath=self.uri,filename=self.filename,exclude=self.exclude)
        #print data
        #p = {"paramjsonstring":json.dumps(data)}
        log("download url = "+self.__class__.PROXY)
        ##TODO 超时的问题
        r= urllib2.urlopen(self.__class__.PROXY, data=urllib.urlencode(data))
        #print len(r.read())
        log("access url to download")
        output = open("./download/"+self.filename,'w')
        output.write(r.read())
        output.close()
        '''
        output = {}
        try:
            #print os.access("./download/"+self.filename, os.W_OK)
            
        except Exception,e:
            #print e
            log(str(e))
        finally:
            try:
                output.close()
            except Exception,e:
                log("close file error "+str(e))
        '''
        log("save file done")
        
        if os.path.getsize("./download/"+self.filename) == 0 : 
            raise Exception("从现网下载的代码文件大小为0，下载异常。")
        pass



#config = ConfigParser.ConfigParser()
#config.read("config/session/trade.ini")
#configpath = "config/session/trade.ini"

#projCmpObj = filecmp.dircmp(left,right)
#print projCmpObj.diff_files

class CompareSession:
    filesystemMap = {'ssh':SSHFileSystem , 'system': LocalFileSystem , 'svn':SVNFileSystem}
    BASE_DIR = os.getcwd()
    def __init__(self,param):
        #self.configpath = param['configPath']
        # TODO(dondonchen)
        #self.sessionName = self.configpath.split('/')[-1][0:-4]
        self.sessionName = param['sessionName']
        #config = param['config']
        #left,leftNS = config.get('common','left').split(',')
        #right,rightNS = config.get('common','right').split(',')
        leftType = param['leftType']   # value = svn
        rightType = param['rightType'] # value = ssh

        self.leftSystem = self.__class__.filesystemMap[leftType](self.sessionName,'left', param)
        self.rightSystem = self.__class__.filesystemMap[rightType](self.sessionName,'right',param)

        self.ignore = param['ignore'].replace(" ","").split(',') #sessionConfig.get(session,'ignore') #config.get('common','ignore').replace(" ","").split(',')


    def newSessionFolder(self):
        #self.baseDir =
        leftfolder = os.path.join(self.__class__.BASE_DIR,"cmpfolder",self.sessionName,"left")
        rightfolder = os.path.join(self.__class__.BASE_DIR,"cmpfolder",self.sessionName,"right")

        if not os.path.exists(leftfolder):
            log(leftfolder+" not exists ,create it")
            os.makedirs(leftfolder)

        if not os.path.exists(rightfolder):
            log(rightfolder+" not exists ,create it")
            os.makedirs(rightfolder)
        pass

    def readyFiles(self):
        self.newSessionFolder()
        self.leftSystem.readyFiles(self.__class__.BASE_DIR+"/cmpfolder/"+self.sessionName+"/left/")
        self.rightSystem.readyFiles(self.__class__.BASE_DIR+"/cmpfolder/"+self.sessionName+"/right/")
        
        '''dos2unix to solve line breaker'''
        cmd = '''cd %s ; find -type f  -exec echo '"{}"' \; | xargs dos2unix --safe -q ''' % (self.__class__.BASE_DIR+"/cmpfolder/"+self.sessionName,)
        log("cmd = "+cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()

    def cmpFiles(self):
        self.cmpFiles = FolderCompare(left = self.__class__.BASE_DIR+"/cmpfolder/"+self.sessionName+"/left/",
                                        right = self.__class__.BASE_DIR+"/cmpfolder/"+self.sessionName+"/right/",
                                        ignore = self.ignore )

        self.cmpFiles.cmpFiles()

    def getDiffFiles(self):
        return self.cmpFiles.difflist

##-----------------------------
class FolderCompare:
    def __init__(self,left,right,ignore=None):
        self.leftdir = left
        self.rightdir = right
        self.ignore = ignore

        self.regex = re.compile("|".join(ignore).replace("*", ".*"))


    def __cmpStep1(self,dcmp):
        #    使用dircmp对目录下的所有文件进行对比，简单的过滤一次
        #print dcmp.diff_files
        diffile = []

        for name in dcmp.diff_files:
            ##TODO
            #print name
            diffile.append("/"+name)

        for sub_dcmp in dcmp.subdirs.values():

            subdirName = sub_dcmp.left.split(r"/")[-1]

            dif_list = self.__cmpStep1(sub_dcmp)
            #print dif_list
            for name in dif_list:
                filename = "/"+subdirName+name
                diffile.append(filename)

        return diffile


    def __cmpStep2(self,step1list):
        '''根据文本进行第二次过滤
            @param step1list: 第一次过滤的结果
        '''
        pass
        for file in step1list:
            leftfile = self.leftdir+file
            rightfile = self.rightdir+file
            #print leftfile,rightfile
            diff = difflib.SequenceMatcher(lambda x: x in " \t\r", open(leftfile).readlines(), open(rightfile).readlines())
            print diff.get_matching_blocks()
            print diff.ratio()

            d = difflib.ndiff(open(leftfile).readlines(), open(rightfile).readlines())
            #print ''.join(d),

    def __fileIgnore(self,files):
        '''过滤忽略的文件 '''
        diffiles = []
        for filename in files:
            if not self.regex.match(filename):
                diffiles.append(filename)
        return diffiles

    '''
    比较两个文件夹
    '''
    def cmpFiles(self):
        #ignore = filecmp.DEFAULT_IGNORES +  self.ignore
        self.dircmp = filecmp.dircmp(a=self.leftdir,b=self.rightdir,ignore = self.ignore)


        #print self.dircmp.diff_files
        #print self.dircmp.__dict__

        stemp1list = self.__fileIgnore(self.__cmpStep1(self.dircmp))
        self.difflist = sorted(stemp1list)   ## 排序一下
        
        
        #print 23
        #self.__cmpStep2(stemp1list)


####------------------------------------
class CmpSessionManage:
    """
        单例模式
    """
    def __init__(self):
        pass

    @staticmethod
    def newInstance1(inipath):
        if inipath:
            config = CmpSessionManage.__readConfig(inipath)
            return CompareSession(config=config,configPath=inipath)


    @staticmethod
    def __readConfig(inipath):
        config = ConfigParser.ConfigParser()
        config.read(inipath)
        return config

    @staticmethod
    def newInstance(param):
        #sessionName = param['sessionName']
        #leftType = param['leftType'] # svn
        #rightType=param['rightType'] # ssh
        return CompareSession(param)


'''

a= {"sessionName":"trade",
    "ignore" : [".svn"],
    "leftType": "svn",
    "rightType": "ssh",
    "left" : {"uri" : "file:///home/dong/svnrepo/test/trunk" , "username" : "username" , "password":"password"},
    "right": {"uri" : "/home/dong/develop/svnproject/left" , "username" : "username" , "password":"password", "host":"127.0.0.1"}
    }

'''
a= json.loads(sys.argv[1])
def main():
    try:
        session = CmpSessionManage.newInstance(a)
        session.readyFiles()
        session.cmpFiles()
        #print session.getDiffFiles()
        ret = {"retcode":0,"difflist" : session.getDiffFiles()}
        return ret
    except Exception,e:
        #print e
        #log(repr(e))
        import traceback, os.path
        top = traceback.extract_stack()[-1]
        log( ', '.join([type(e).__name__, os.path.basename(top[0]), str(top[1])])  )
        ret = {"retcode":-1,"message" : str(e)}
        return ret
    finally:
        pass
         
    #print 1


if __name__ == '__main__':

    #print json.dumps({"11":"11"})
    log("------------------start------------------")
    s = main()
    b =  json.dumps(s)
    print b
    log("response="+b)
    log("------------------end--------------------")
#fcmp = FolderCompare(left,right)
#fcmp.getDiffFiles(projCmpObj)
    #print sys.argv[1]
    pass



