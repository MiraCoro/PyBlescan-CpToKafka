# BLE iBeaconScanner based on https://gitlab.com/bliznetz/ibeaconscantokafka.git
#05/24/19

# BLE iBeaconScanToKafke based on https://github.com/switchdoclabs/iBeacon-Scanner-.git
# Mira 11/19/18
#
# BLE iBeaconScanner based on https://github.com/adamf/BLE/blob/master/ble-scanner.py
# JCS 06/07/14

DEBUG = False
# BLE scanner based on https://github.com/adamf/BLE/blob/master/ble-scanner.py
# BLE scanner, based on https://code.google.com/p/pybluez/source/browse/trunk/examples/advanced/inquiry-with-rssi.py

# https://github.com/pauloborges/bluez/blob/master/tools/hcitool.c for lescan
# https://kernel.googlesource.com/pub/scm/bluetooth/bluez/+/5.6/lib/hci.h for opcodes
# https://github.com/pauloborges/bluez/blob/master/lib/hci.c#L2782 for functions used by lescan

# performs a simple device inquiry, and returns a list of ble advertizements 
# discovered device

# NOTE: Python's struct.pack() will add padding bytes unless you make the endianness explicit. Little endian
# should be used for BLE. Always start a struct.pack() format string with "<"

import os
import sys
import struct
import bluetooth._bluetooth as bluez
import codecs
#import bitstring
import binascii

LE_META_EVENT = 0x3e
LE_PUBLIC_ADDRESS=0x00
LE_RANDOM_ADDRESS=0x01
LE_SET_SCAN_PARAMETERS_CP_SIZE=7
OGF_LE_CTL=0x08
OCF_LE_SET_SCAN_PARAMETERS=0x000B
OCF_LE_SET_SCAN_ENABLE=0x000C
OCF_LE_CREATE_CONN=0x000D

LE_ROLE_MASTER = 0x00
LE_ROLE_SLAVE = 0x01

# these are actually subevents of LE_META_EVENT
EVT_LE_CONN_COMPLETE=0x01
EVT_LE_ADVERTISING_REPORT=0x02
EVT_LE_CONN_UPDATE_COMPLETE=0x03
EVT_LE_READ_REMOTE_USED_FEATURES_COMPLETE=0x04

# Advertisment event types
ADV_IND=0x00
ADV_DIRECT_IND=0x01
ADV_SCAN_IND=0x02
ADV_NONCONN_IND=0x03
ADV_SCAN_RSP=0x04


def returnnumberpacket(pkt):
    myInteger = 0
    multiple = 256
    for c in pkt:
        #myInteger +=  struct.unpack("B",c)[0] * multiple
        myInteger +=  int(c) * multiple
        multiple = 1
    return myInteger 

def returnstringpacket(pkt):
    myString = "";
    for c in pkt:
        #myString +=  "%02x" %struct.unpack("B",c)[0]
        myString +=  "%02x" %c
    return myString 

def printpacket(pkt):
    for c in pkt:
        #sys.stdout.write("%02x " % struct.unpack("B",c)[0])
        sys.stdout.write("%02x " % c)

def get_packed_bdaddr(bdaddr_string):
    packable_addr = []
    addr = bdaddr_string.split(':')
    addr.reverse()
    for b in addr: 
        packable_addr.append(int(b, 16))
    return struct.pack("<BBBBBB", *packable_addr)

def packed_bdaddr_to_string(bdaddr_packed):
#    return ':'.join('%02x'%i for i in struct.unpack("<BBBBBB", bdaddr_packed[::-1]))
    return ':'.join('%02x'%i for i in bdaddr_packed[::-1])

def hci_enable_le_scan(sock):
    hci_toggle_le_scan(sock, 0x01)

def hci_disable_le_scan(sock):
    hci_toggle_le_scan(sock, 0x00)

def hci_toggle_le_scan(sock, enable):
# hci_le_set_scan_enable(dd, 0x01, filter_dup, 1000);
# memset(&scan_cp, 0, sizeof(scan_cp));
 #uint8_t         enable;
 #       uint8_t         filter_dup;
#        scan_cp.enable = enable;
#        scan_cp.filter_dup = filter_dup;
#
#        memset(&rq, 0, sizeof(rq));
#        rq.ogf = OGF_LE_CTL;
#        rq.ocf = OCF_LE_SET_SCAN_ENABLE;
#        rq.cparam = &scan_cp;
#        rq.clen = LE_SET_SCAN_ENABLE_CP_SIZE;
#        rq.rparam = &status;
#        rq.rlen = 1;

#        if (hci_send_req(dd, &rq, to) < 0)
#                return -1;
    cmd_pkt = struct.pack("<BB", enable, 0x00)
    bluez.hci_send_cmd(sock, OGF_LE_CTL, OCF_LE_SET_SCAN_ENABLE, cmd_pkt)


def hci_le_set_scan_parameters(sock):
    old_filter = sock.getsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, 14)

    SCAN_RANDOM = 0x01
    OWN_TYPE = SCAN_RANDOM
    SCAN_TYPE = 0x01


    
def parse_events(sock, loop_count):
    old_filter = sock.getsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, 14)

    # perform a device inquiry on bluetooth device #0
    # The inquiry should last 8 * 1.28 = 10.24 seconds
    # before the inquiry is performed, bluez should flush its cache of
    # previously discovered devices
    
    iBeaconIdString = (255, 76, 0, 2, 21)
    # Type - xFF (255)
    # MFGID - x4C x00 (76 0)
    # Type - Proximity / iBeacon - x02 (2)
    # Length - x15 (21)
    
    flt = bluez.hci_filter_new()
    bluez.hci_filter_all_events(flt)
    bluez.hci_filter_set_ptype(flt, bluez.HCI_EVENT_PKT)
    sock.setsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, flt )
    done = False
    results = []
    myFullList = []
    for i in range(0, loop_count):
        pkt = sock.recv(255)
        ptype, event, plen = struct.unpack("BBB", pkt[:3])
        if (DEBUG == True):
            print("------ptype, event, plen-------- \n", ptype, event, plen)
        if event == bluez.EVT_INQUIRY_RESULT_WITH_RSSI:
            i =0
        elif event == bluez.EVT_NUM_COMP_PKTS:
            i =0 
        elif event == bluez.EVT_DISCONN_COMPLETE:
            i =0 
        elif event == LE_META_EVENT:
            #subevent, = struct.unpack("B", pkt[3])
            subevent = pkt[3]
            pkt = pkt[4:]
            isiBeacon = False
            if (pkt[14:19]):
                isiBeacon = True if struct.unpack("BBBBB", pkt[14:19]) == iBeaconIdString else False
            if (DEBUG == True):
                print("----- isIbeacon -----", isiBeacon)
            if subevent == EVT_LE_CONN_COMPLETE:
                le_handle_connection_complete(pkt)
            elif ((subevent == EVT_LE_ADVERTISING_REPORT) and isiBeacon):
                #print "advertising report"
                num_reports = pkt[0]
                report_pkt_offset = 0
                for i in range(0, num_reports):
                    #pktbs = bitstring.BitStream(pkt) Previous way to get two last values from pkt
                    #pktbs.pos += len(pktbs) - (2 * 8)
                    #txpower = pktbs.read('int:8')
                    #rssi = pktbs.read('int:8')
                    if (DEBUG == True):
                        print("-------------")
                        print("fullpacket:", end = ' ')
                        print(printpacket(pkt))
                        print("UDID:", end = ' ') 
                        print(printpacket(pkt[report_pkt_offset -22: report_pkt_offset - 6]))
                        print("TTMFGID:", end = ' ')
                        print(printpacket(pkt[report_pkt_offset -27: report_pkt_offset - 22]))
                        print("MAJOR:", end = ' ')
                        print(printpacket(pkt[report_pkt_offset -6: report_pkt_offset - 4]))
                        print("MINOR:", end = ' ')
                        print(printpacket(pkt[report_pkt_offset -4: report_pkt_offset - 2]))
                        print("MAC address:", end = ' ')
                        print(packed_bdaddr_to_string(pkt[report_pkt_offset + 3:report_pkt_offset + 9]))
                        # commented out - don't know what this byte is.  It's NOT TXPower
                        txpower = struct.unpack("b", pkt[report_pkt_offset -2: report_pkt_offset -1])[0]
                        rssi = struct.unpack("b", pkt[report_pkt_offset -1: report_pkt_offset -2:-1])[0]
                        print ('TXPOWER:', txpower)
                        print("RSSI:", rssi)
             # build the return string
                    Adstring = packed_bdaddr_to_string(pkt[report_pkt_offset + 3:report_pkt_offset + 9])
                    Adstring += ","
                    Adstring += returnstringpacket(pkt[report_pkt_offset -22: report_pkt_offset - 6])
                    Adstring += ","
                    Adstring += "%i" % returnnumberpacket(pkt[report_pkt_offset -6: report_pkt_offset - 4])
                    Adstring += ","
                    Adstring += "%i" % returnnumberpacket(pkt[report_pkt_offset -4: report_pkt_offset - 2])
                    Adstring += ","
                    Adstring += "%i" % struct.unpack("b", pkt[report_pkt_offset -2: report_pkt_offset -1])[0]
                    Adstring += ","
                    Adstring += "%i" % struct.unpack("b", pkt[report_pkt_offset -1: report_pkt_offset -2:-1])[0]
		    
                    if (DEBUG == True):
                        print("Adstring =", Adstring)
                    myFullList.append(Adstring)
                done = True
    sock.setsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, old_filter )
    return myFullList
