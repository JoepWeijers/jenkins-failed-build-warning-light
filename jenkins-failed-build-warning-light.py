import datetime
import requests
import time
import sys
import os
import ctypes

POLL_INTERVAL_SECONDS = 3
FAILED_JOB_COLORS = ['yellow', 'red']
ON = True
OFF = False
WORKDAY_START_TIME = datetime.time(8, 45)
WORKDAY_END_TIME = datetime.time(18, 0)
print("Running on Python v." + str(sys.version))
print("%d-bit mode" % ({4:32, 8:64}[ctypes.sizeof(ctypes.c_void_p)]) )

# Fix the path below if the library is not in current dir.
libpath = "."

if sys.version_info.major >= 3:
  def charpToString(charp):
     return str(ctypes.string_at(charp), 'ascii')
  def stringToCharp(s) :   
    return bytes(s, "ascii")
else:
  def charpToString(charp) :
     return str(ctypes.string_at(charp))
  def stringToCharp(s) :   
    return bytes(s)  #bytes(s, "ascii")
 
libfile = {'nt':   "usb_relay_device.dll", 
           'posix': "usb_relay_device.so",
           'darwin':"usb_relay_device.dylib",
           } [os.name]

#?? MAC => os.name == "posix" and sys.platform == "darwin"

devids = []
hdev = None

def exc(msg):  return Exception(msg)

def fail(msg) : raise exc(msg)
 
class L: pass   # Global object for the DLL
setattr(L, "dll", None)

def loadLib():
  # Load the C DLL ...
  if not L.dll :
    print("Loading DLL: %s" % ('/'.join([libpath, libfile])))
    try:
      L.dll = ctypes.CDLL( '/'.join([libpath, libfile]) )
    except OSError:  
      fail("Failed load lib")
  else:
    print("lib already open")
  #print(L.dll)

usb_relay_lib_funcs = [
  # TYpes: h=handle (pointer sized), p=pointer, i=int, e=error num (int), s=string
  ("usb_relay_device_enumerate",               'h', None),
  ("usb_relay_device_close",                   'e', 'h'),
  ("usb_relay_device_open_with_serial_number", 'h', 'si'),
  ("usb_relay_device_get_num_relays",          'i', 'h'),
  ("usb_relay_device_get_id_string",           's', 'h'),
  ("usb_relay_device_next_dev",                'h', 'h'),
  ("usb_relay_device_get_status_bitmap",       'i', 'h'),
  ("usb_relay_device_open_one_relay_channel",  'e', 'hi'),
  ("usb_relay_device_close_one_relay_channel", 'e', 'hi'),
  ("usb_relay_device_close_all_relay_channel", 'e', None)
  ]
      
      
def getLibFunctions():
  """ Get needed functions and configure types; call lib. init.
  """
  assert L.dll
  
  #Get lib version (my extension, not in the original dll)
  libver = L.dll.usb_relay_device_lib_version()  
  print("%s version: 0x%X" % (libfile,libver))
  
  ret = L.dll.usb_relay_init()
  if ret != 0 : fail("Failed lib init!")
  
  """
  Tweak imported C functions
  This is required in 64-bit mode. Optional for 32-bit (pointer size=int size)
  Functions that return and receive ints or void work without specifying types.
  """
  ctypemap = { 'e': ctypes.c_int, 'h':ctypes.c_void_p, 'p': ctypes.c_void_p,
            'i': ctypes.c_int, 's': ctypes.c_char_p}
  for x in usb_relay_lib_funcs :
      fname, ret, param = x
      try:
        f = getattr(L.dll, fname)
      except Exception:  
        fail("Missing lib export:" + fname)

      ps = []
      if param :
        for p in param :
          ps.append( ctypemap[p] )
      f.restype = ctypemap[ret]
      f.argtypes = ps
      setattr(L, fname, f)
      
def openDevById(idstr):
  #Open by known ID:
  print("Opening " + idstr)
  h = L.usb_relay_device_open_with_serial_number(stringToCharp(idstr), 5)
  if not h: fail("Cannot open device with id="+idstr)
  global numch
  numch = L.usb_relay_device_get_num_relays(h)
  if numch <= 0 or numch > 8 : fail("Bad number of channels, can be 1-8")
  global hdev
  hdev = h  
  print("Number of relays on device with ID=%s: %d" % (idstr, numch))

def closeDev():
  global hdev
  L.usb_relay_device_close(hdev)
  hdev = None

def enumDevs():
  global devids
  devids = []
  enuminfo = L.usb_relay_device_enumerate()
  while enuminfo :
    idstrp = L.usb_relay_device_get_id_string(enuminfo)
    idstr = charpToString(idstrp)
    print(idstr)
    assert len(idstr) == 5
    if not idstr in devids : devids.append(idstr)
    else : print("Warning! found duplicate ID=" + idstr)
    enuminfo = L.usb_relay_device_next_dev(enuminfo)

  print("Found devices: %d" % len(devids))
  
def unloadLib():
  global hdev, L
  if hdev: closeDev()
  L.dll.usb_relay_exit()
  L.dll = None
  print("Lib closed")
  
def switch(state):
  """ Test one device with handle hdev, 1 or 2 channels """
  global numch, hdev
  if numch <=0 or numch > 8:
     fail("Bad number of channels on relay device!")

  ret = L.usb_relay_device_open_one_relay_channel(hdev,1) if state else L.usb_relay_device_close_one_relay_channel(hdev,1)
  if ret != 0: fail("Failed to switch state!")
  
def during_working_hours():
    now = datetime.datetime.today()
    return now.weekday() in range(0,5) and WORKDAY_START_TIME < now.time() and now.time() < WORKDAY_END_TIME

def get_number_of_failed_jenkins_jobs(view_url):
    req = requests.get(view_url + '/api/json?tree=jobs[color]')
    if req.status_code != 200:
        print "Failed to get status of Jenkins jobs, returned status: {}, content:\n{}".format(req.status_code, req.text)
    
    job_results = [job for job in req.json()['jobs'] if job['color'] in FAILED_JOB_COLORS]
    return len(job_results)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        raise Exception("No Jenkins view URL passed. Usage: python jenkins-failed-build-warning-light.py http://jenkins.example.com/view/Main")
    
    view_url = sys.argv[1]
    print "Start monitoring Jenkins view {}".format(view_url)
    loadLib()
    getLibFunctions()
    try:
        print("Searching for compatible devices")
        enumDevs()
        if len(devids) != 0 :
            # Test any 1st found dev .
            print("Using relay with ID=" + devids[0])
            openDevById(devids[0])
            current_state = OFF
            switch(current_state)
            try:
                while True:
                    if during_working_hours():
                        try:
                            number_of_failed_jobs = get_number_of_failed_jenkins_jobs(view_url)
                            if number_of_failed_jobs == 0:
                                print "Everything is OK"
                                current_state = OFF
                            else:
                                print "There are {} failing jobs".format(number_of_failed_jobs)
                                current_state = ON
                            switch(current_state)
                        except Exception as e:
                            print "Failed to get update status of Jenkins jobs: {}".format(str(e))
                    else:
                        print "Nobody is in the office"
                        if current_state == ON:
                            current_state = OFF
                            switch(current_state)
                        
                    time.sleep(POLL_INTERVAL_SECONDS)
            except (SystemExit, KeyboardInterrupt):
                switch(OFF)
                closeDev()
    finally:
        unloadLib()