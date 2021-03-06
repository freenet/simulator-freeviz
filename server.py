import sys
sys.path+=['/home/freeviz//freeviz/SQLObject/']
sys.path+=['/home/freeviz/freeviz/FormEncode/']
import socket
import threading
import handler
import db
import time

PORT=23415
NRCONS=100
HANDLER_DELAY=10
MAXCONNS=300


class Base(threading.Thread):
	vlock = threading.Lock()
	chunks=[]
	id=0
	conns = 0 

class Handler(Base):
	chunks = []	

	def run(self):
		con = db.get_con()		
		trans = con.transaction()
		while 1:
			Base.vlock.acquire()
			self.chunks = Base.chunks
			Base.chunks = []
			Base.vlock.release()
			print "Hanlding harvested data(%d)" % len(self.chunks)
			for chunk in self.chunks:
				try:
					handler.handle(chunk,trans)
				except Exception:
					print "ERROR IN %s" % chunk

			if self.chunks: 
				trans.commit()
				print "COMMITED (%d)" % len(self.chunks)
			else:
				print "NOTHING"

			self.chunks=[]
			time.sleep(HANDLER_DELAY)			

class serv(Base):
	chunk=''
	def __init__(self,clnsock):
		threading.Thread.__init__(self)
		self.clnsock=clnsock
		self.myid=Base.id
		Base.id+=1


	def run(self):
		self.clnsock.settimeout(60.0)
		while 1:
			try:
				k = self.clnsock.recv(1024)
				if k == '': break
				self.chunk+=k
			except:
				Base.vlock.acquire()
				Base.conns -=1
				Base.vlock.release()
				return
#		self.clnsock.shutdown(socket.SHUT_RDWR)
		self.clnsock.close()
		Base.vlock.acquire()
		Base.chunks.append(self.chunk)
		Base.conns -= 1
		Base.vlock.release()	
		#print "%s\n________\n" % self.chunk



lstn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lstn.bind(('',PORT))
lstn.listen(MAXCONNS)
h = Handler()
h.start()
conns=0
while 1:
	threading.Lock().acquire()
	conns = Base.conns
	threading.Lock().release
	print "conns running %d" % conns

	if conns < MAXCONNS:
		(clnt,ap) = lstn.accept()
		s = serv(clnt)
		threading.Lock().acquire()
		Base.conns += 1
		threading.Lock().release
		s.start()	
	else:
		print "DELAY!"
		time.sleep(HANDLER_DELAY)
