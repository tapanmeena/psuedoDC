#livestatus port number : 12121
#broadcasting port number : 44444
# addFile() sharing port : 9005
# supernode to supernode communication PORT : 9999

import os, sys, threading, socket, time, csv, pickle, subprocess

ipAddr = ''
numChunks = 4

# --------------file splitting utility--------------------

class FileSplitterException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

def usage():
    return """\nUsage: FileSplitter.py -i <inputfile> -n <chunksize> [option]\n
    Options:\n
    -s, --split  Split file into chunks
    -j, --join   Join chunks back to file.
    """

class FileSplitter:
    """ File splitter class """

    def __init__(self):

        # cache filename
        self.__filename = ''
        # number of equal sized chunks
        self.__numchunks = 4
        # Size of each chunk
        self.__chunksize = 0
        # Optional postfix string for the chunk filename
        self.__postfix = ''
        # Program name
        self.__progname = "FileSplitter.py"
        
    def doWork(self, fileName, action):
        self.__numchunks = int(numChunks)
        self.__filename = fileName
        if not self.__filename:
            sys.exit("Error: filename not given")
            return
        if action == 'split':
            self.split()
        elif action =='join':
            self.combine()
        
    def split(self):
        """ Split the file and save chunks
        to separate files """

        print 'Splitting file', self.__filename
        print 'Number of chunks', self.__numchunks, '\n'
        
        try:
            f = open(self.__filename, 'rb')
        except (OSError, IOError), e:
            raise FileSplitterException, str(e)

        bname = (os.path.split(self.__filename))[1]
        # Get the file size
        fsize = os.path.getsize(self.__filename)
        # Get size of each chunk
        self.__chunksize = int(float(fsize)/float(self.__numchunks))

        chunksz = self.__chunksize
        total_bytes = 0

        for x in range(self.__numchunks):
            chunkfilename = bname + '-' + str(x+1) + self.__postfix

            # if reading the last section, calculate correct
            # chunk size.
            if x == self.__numchunks - 1:
                chunksz = fsize - total_bytes

            try:
                print 'Writing file',chunkfilename
                data = f.read(chunksz)
                total_bytes += len(data)
                chunkf = file(chunkfilename, 'wb')
                chunkf.write(data)
                chunkf.close()
            except (OSError, IOError), e:
                print e
                continue
            except EOFError, e:
                print e
                break

        print 'Done.'

    def sort_index(self, f1, f2):

        index1 = f1.rfind('-')
        index2 = f2.rfind('-')
        
        if index1 != -1 and index2 != -1:
            i1 = int(f1[index1:len(f1)])
            i2 = int(f2[index2:len(f2)])
            return i2 - i1
        
    def combine(self):
        """ Combine existing chunks to recreate the file.
        The chunks must be present in the cwd. The new file
        will be written to cwd. """

        import re
        
        print 'Creating file', self.__filename
        
        bname = (os.path.split(self.__filename))[1]
        bname2 = bname
        
        # bugfix: if file contains characters like +,.,[]
        # properly escape them, otherwise re will fail to match.
        for a, b in zip(['+', '.', '[', ']','$', '(', ')'],
                        ['\+','\.','\[','\]','\$', '\(', '\)']):
            bname2 = bname2.replace(a, b)
            
        chunkre = re.compile(bname2 + '-' + '[0-9]+')
        
        chunkfiles = []
        for f in os.listdir("."):
            print f
            if chunkre.match(f):
                chunkfiles.append(f)


        print 'Number of chunks', len(chunkfiles), '\n'
        chunkfiles.sort(self.sort_index)

        data=''
        for f in chunkfiles:

            try:
                print 'Appending chunk', os.path.join(".", f)
                data += open(f, 'rb').read()
            except (OSError, IOError, EOFError), e:
                print e
                continue

        try:
            f = open(bname, 'wb')
            f.write(data)
            f.close()
        except (OSError, IOError, EOFError), e:
            raise FileSplitterException, str(e)

        print 'Wrote file', bname

#--------------------------------------------------------- 

def aliveChecker():
    time.sleep(8)
    while True:
        TCP_IP = str(ipAddr)
        TCP_PORT = 12121
        BUFFER_SIZE = 1024
        # print "TCP->" + TCP_IP

        p = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            p.connect((str(TCP_IP), TCP_PORT))
            msg = "Alive"
            print msg
            p.send(msg)
            p.close()
            print "I'm Alive BRO!!!"
            time.sleep(100)
        except socket.error , exc:
            # print "Error Caught : ",exc
            time.sleep(20)

def superNodeAssign():
    global ipAddr
    broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Set a timeout so the socket does not block
    # indefinitely when trying to receive data.
    broadcast.settimeout(0.2)
    broadcast.bind(("", 44444))

    #to get it's own IP Address
    # bashCommand = "hostname -I | awk '{print $1}'"
    # message = subprocess.check_output(['bash','-c', bashCommand])
    message = "Hi, I want to connect!!"
    while True:
        broadcast.sendto(message, ('<broadcast>', 37020))
        # print("message sent!")
        data,addr = broadcast.recvfrom(1024)
        if data is not None:
            ipAddr = str(data)
            ipAddr = ipAddr.strip('\n')
            break
        time.sleep(1)
    print "Super Node Ip Address : "+ str(ipAddr)
    listFiles()

#assumption a list of fileName is coming
def fileRequest(fileList):
    fileList.sort()
    tempList = []
    while True:
        i = 1
        for item in fileList:
            print i, item

def sharing():
    #for sending filename and receiving File from server(sender)
    TCP_IP = 'localhost' #sender ip address
    TCP_PORT = 9001
    BUFFER_SIZE = 1024

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))
    filename = raw_input("Give File Name : ")
    s.send(filename)
    with open(filename, 'wb') as f:
        print 'file opened'
        while True:
            #print('receiving data...')
            data = s.recv(BUFFER_SIZE)
            # print('data=%s', (data))
            if not data:
                f.close()
                print 'file close()'
                break
            # write data to a file
            f.write(data)

    print('Successfully get the file')
    s.close()
    print('connection closed')

def computeHash(filename):
    hashList = []
    for i in range(1,numChunks+1):
        bashcommand = "md5sum "+str(filename)+"-"+str(i)
        Hash = subprocess.check_output(['bash','-c', bashcommand])
        Hash = Hash.split(' ')
        hashList.append(Hash[0])
    return hashList

def dumpContent(filename):
    fileContent = []
    with open(filename, 'rb') as f:
        reader = csv.reader(f)

        # read file row by row
        for row in reader:
            fileContent.append(row)

    return fileContent

def removeSplittedFiles(filename):
    command = "rm "+str(filename)+"-*"
    os.system(command)

def Diff(li1, li2):
    li_dif = [i for i in li1 + li2 if i not in li1 or i not in li2] 
    return li_dif
    # return (list(set(list1) - set(list2)))

def listFiles():
    filename = 'listFiles.csv'
    fileDump = []
    fileExist = False
    if(os.path.exists(filename)):
        fileExist = True

    bashCommand = "ls -l | awk '{print $6, $7, $8, $9}'"
    fileList = subprocess.check_output(['bash','-c', bashCommand])
    fileList = fileList.split('\n')
    numFiles = len(fileList)

    if not fileExist:
        with open(filename, 'wb') as csvfile:
            filewriter = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for i in range(1, numFiles-1):
                item = fileList[i].split(' ')
                date = str(item[0]) + str(item[1])
                time =  str(item[2])
                fileName = str(item[3])
                fsp = FileSplitter()
                fsp.doWork(fileName, 'split')
                hashes = computeHash(fileName)

                removeSplittedFiles(fileName)
                # print hashes
                filewriter.writerow([fileName, hashes[0], hashes[1], hashes[2], hashes[3],"add", date, time])
                fileDump.append([fileName, hashes[0], hashes[1], hashes[2], hashes[3], date, time])
    else:
        print("-------> If List Files Exist <-------")
        originalFileContent = dumpContent(filename)
        # fileDump = []
        print originalFileContent
        os.remove('listFiles.csv')
        fileNameList = []
        newFileNameList = []
        timeStampList = []
        dateStampList = []
        hashesList = []
        with open(filename, 'wb') as csvfile:
            filewriter = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)

            for fileN in originalFileContent:
                fileNameList.append(fileN[0])
                hashesList.append([fileN[1], fileN[2], fileN[3], fileN[4]])
                dateStampList.append(fileN[5])
                timeStampList.append(fileN[6])

            for i in range(1,numFiles-1):
                item = fileList[i].split(' ')
                date = str(item[0]) + str(item[1])
                time = str(item[2])
                fileN = str(item[3])
                newFileNameList.append(fileN)

                #check if file exist and its time stamp with recorded LOG
                if(fileN in fileNameList):
                    index = fileNameList.index(fileN)
                    #checking if timestamp are same or not
                    print "###############################"
                    print "File Name :" + fileN
                    
                    if dateStampList[index] < date:
                        print dateStampList[index] + date
                        # print "gandu"
                        fsp = FileSplitter()
                        fsp.doWork(fileN, 'split')
                        hashes = computeHash(fileN)
                        filewriter.writerow([fileN, hashes[0], hashes[1], hashes[2], hashes[3],"add", date, time])
                        fileDump.append([fileN, hashes[0], hashes[1], hashes[2], hashes[3], date, time])
                        removeSplittedFiles(fileN)

                    elif dateStampList[index] == date:
                        if timeStampList[index] < time:
                            print timeStampList[index] + time
                            fsp = FileSplitter()
                            fsp.doWork(fileN, 'split')
                            hashes = computeHash(fileN)
                            filewriter.writerow([fileN, hashes[0], hashes[1], hashes[2], hashes[3],"add", date, time])
                            fileDump.append([fileN, hashes[0], hashes[1], hashes[2], hashes[3], date, time])
                            removeSplittedFiles(fileN)
                        else:
                            fileDump.append([fileN, hashesList[index][0], hashesList[index][1], hashesList[index][2], hashesList[index][3], date, time])
                    else:
                        fileDump.append([fileN, hashesList[index][0], hashesList[index][1], hashesList[index][2], hashesList[index][3], date, time])
                else:
                    print "File Not Present"
                    fsp = FileSplitter()
                    fsp.doWork(fileN, 'split')
                    hashes = computeHash(fileN)
                    filewriter.writerow([fileN, hashes[0], hashes[1], hashes[2], hashes[3],"add", date, time])
                    fileDump.append([fileN, hashes[0], hashes[1], hashes[2], hashes[3], date, time])
                    removeSplittedFiles(fileN)

            ## Get filename that need to be delete from SuperNode
            fileNotNeeded = Diff(fileNameList, newFileNameList)
            print  "--------------------------------"
            print fileNotNeeded
            print  "--------------------------------"
            for names in fileNotNeeded:
                filewriter.writerow([names,'0','0','0','0',"delete",'0','0'])
    fileContents = dumpContent('listFiles.csv')
    print fileContents

    os.remove('listFiles.csv')
    # print "--> printing file Dump <--"
    # print fileDump
    with open('listFiles.csv', 'wb') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for i in fileDump:
            filewriter.writerow(i)

    # sending csv file to supernode
    msg = pickle.dumps(fileContents)
    TCP_IP = str(ipAddr)
    TCP_PORT = 9005 
    BUFFER_SIZE = 1024
    print "TCP->" + TCP_IP

    p = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    p.connect((str(TCP_IP), TCP_PORT))
    p.send(msg)
    p.close()
    print "__Updated File List Sent__"
    return

if __name__ == '__main__':
    #for Initial SuperNode assigning
    superNodeAssign()
    #For Checking Node Status

    alive = threading.Thread(target = aliveChecker, name = 'alive')
    alive.start()


    #for file sharing between sender and receiver
    # sharing()



############
#TODO TIME STAMP COMPARISION IN SEND NEW FILES TO SUPERNODE
############