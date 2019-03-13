import plux, datetime
import numpy as np


class MyDevice(plux.MemoryDev):
    # callbacks override
    def __init__(self, bt):
        super(MyDevice, self).__init__(bt)
        # self.data2 = []
        self.inter = ""

    def onRawFrame(self, nSeq, data):
        allData = [np.asarray(data), np.datetime64(datetime.datetime.now())]
        # print nSeq, allData
        # self.data2.append(allData)
        self.inter = allData
        return True  # Stop after receiving 10000 frames

        '''if nSeq % 100 == 0: #% 1000 == 0:
            print nSeq, data
            self.data2.append(data)
        if nSeq >= 10000: return True  # Stop after receiving 10000 frames'''
        return False

    def onEvent(self, event):
        if type(event) == plux.Event.DigInUpdate:
            print 'Digital input event - Clock source:', event.timestamp.source, \
                ' Clock value:', event.timestamp.value, ' New input state:', event.state
        elif type(event) == plux.Event.SchedChange:
            print 'Schedule change event - Action:', event.action, \
                ' Schedule start time:', event.schedStartTime
        elif type(event) == plux.Event.Sync:
            print 'Sync event:'
            for tstamp in event.timestamps:
                print ' Clock source:', tstamp.source, ' Clock value:', tstamp.value
        elif type(event) == plux.Event.Disconnect:
            print 'Disconnect event - Reason:', event.reason
            return True
        return False

    def onInterrupt(self, param):
        print 'Interrupt:', param
        return False

    def onTimeout(self):
        print 'Timeout'
        return False

    def onSessionRawFrame(self, nSeq, data):
        if nSeq % 1000 == 0:
            print 'Session:', nSeq, data
        return False

    def onSessionEvent(self, event):
        if type(event) == plux.Event.DigInUpdate:
            print 'Session digital input event - Clock source:', event.timestamp.source, \
                ' Clock value:', event.timestamp.value, ' New input state:', event.state
        elif type(event) == plux.Event.Sync:
            print 'Session sync event:'
            for tstamp in event.timestamps:
                print ' Clock source:', tstamp.source, ' Clock value:', tstamp.value
        return False


# example routines

def exampleFindDevices():
    devices = plux.BaseDev.findDevices()
    print "Found devices: ", devices


def exampleStart():  # with exception handling
    dev = None
    try:
        dev = MyDevice("BTH00:07:80:46:E0:64")  # MAC address of device
        props = dev.getProperties()
        print 'Properties:', props
        dev.start(1000, 0xFF, 16)  # 1000 Hz, ports 1-8, 16 bits
        dev.loop()  # returns after receiving 10000 frames (onRawFrame() returns True)
        dev.stop()
        dev.close()
    except Exception as e:
        print e
        if (dev):
            dev.close()


def exampleStartSources():
    srcx = plux.Source()
    srcx.port = 1
    # nBits defaults to 16
    # freqDivisor defaults to 1
    # chMask defaults to 1

    srcy = plux.Source()
    srcy.port = 2
    srcy.nBits = 8
    srcy.freqDivisor = 3  # divide base frequency by 3 for this source

    srcz = plux.Source()
    srcz.port = 3
    srcz.freqDivisor = 2  # divide base frequency by 2 for this source

    dev = MyDevice("00:07:80:79:6F:DB")  # MAC address of device
    dev.start(1000, (srcx, srcy, srcz))  # base freq: 1000 Hz, ports 1-3 as defined by sources
    dev.loop()  # returns after receiving 10000 frames (onRawFrame() returns True)
    dev.stop()
    dev.close()


def exampleAddSchedule():
    srcx = plux.Source()
    srcx.port = 1

    srcy = plux.Source()
    srcy.port = 2

    srcz = plux.Source()
    srcz.port = 3

    dev = MyDevice("00:07:80:79:6F:DB")  # MAC address of device
    dev.setTime()  # adjust device RTC

    sch = plux.Schedule()
    sch.baseFreq = 1000  # in Hz
    sch.startTime = datetime.datetime.now() + datetime.timedelta(0,
                                                                 10)  # start an internal acquisition 10 seconds from now
    # sch.startTime = 1  # decomment this line to start an internal acquisition with external trigger
    sch.duration = 30  # maximum duration of 30 seconds
    sch.sources = (srcx, srcy, srcz)

    dev.addSchedule(sch)
    dev.close()


def exampleReplaySessions():
    dev = MyDevice("00:07:80:79:6F:DB")  # MAC address of device
    sessions = dev.getSessions()
    for s in sessions:
        dev.replaySession(s.startTime)  # replay all sessions on device
    dev.close()
