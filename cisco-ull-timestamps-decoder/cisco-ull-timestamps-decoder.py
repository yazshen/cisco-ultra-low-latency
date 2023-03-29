#!/usr/bin/python3

'''
Welcome to Cisco ULL Timestamps Decoder

Version 1.0

https://github.com/yazshen

Prerequisites:
1) Python 3.10.x or higher, verified on 3.11.2
2) pip3 install scapy
3) pip3 install texttable

Have fun!

-- Robbie Shen (yazshen@cisco.com)
'''

import os
import sys
import argparse
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.error import Scapy_Exception
from scapy.utils import RawPcapReader, hexdump
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP
from scapy.compat import raw
from texttable import Texttable

def func_decode_pcap(argFileName, argType):
    print('Opening ' + argFileName + ' ...')
    if argType == '3550t' :
        print('Warining: 3550t is an experimental feature, please reach out to me if you encounter unexpected issue.')

    varPacketTotalCount = 0
    varPacketICMPCount = 0
    varPacketTCPCount = 0
    varPacketUDPCount = 0

    varOutputTable = Texttable()
    varOutputTable.set_cols_width([20, 20, 20, 20, 20, 20, 20, 20, 20, 20])
    varOutputTable.set_cols_dtype(["t", "t", "t", "t", "t", "t", "t", "t", "t", "t"])
    varOutputTable.header(['Frame No.', 'Frame Length', 'Src MAC', 'Dst MAC', 'IP Protocol', 'IP Identification', 'Device ID', 'Port ID', 'Seconds Since Epoch', 'Fractional Seconds'])

    try:
        for (varPacketData, varPacketMetaData,) in RawPcapReader(argFileName):
            varTimestampSecond = -1
            varTimestampFractionalSecond = -1
            varDeviceID = -1
            varSourcePortID = -1
            varPacketTotalCount += 1
            varEtherPacket = Ether(varPacketData)
            if 'type' not in varEtherPacket.fields:
                continue
            if varEtherPacket.type != 0x0800:
                continue

            match argType:
                case "3550fhpt" :
                    varDeviceID = int(raw(varPacketData)[-16:-15].hex(), 16)
                    varSourcePortID = int(raw(varPacketData)[-15:-14].hex(), 16)
                    varTimestampSecond = int(raw(varPacketData)[-14:-10].hex(), 16)
                    varTimestampFractionalSecond = round(int(raw(varPacketData)[-10:-5].hex(), 16) * 2**-40, 12)
                case "3550t" :
                    varDeviceID = int(raw(varPacketData)[-20:-19].hex(), 16)
                    varSourcePortID = int(raw(varPacketData)[-19:-18].hex(), 16)
                    varTimestampSecond = int(raw(varPacketData)[-18:-14].hex(), 16)
                    varTimestampFractionalSecond = round(int(raw(varPacketData)[-14:-9].hex(), 16) * 2**-40, 12)
                case "exact" :
                    varByteArray = bytearray.fromhex(raw(varPacketData)[-16:-13].hex())
                    varByteArray.reverse()
                    varTimestampSecond = int(varByteArray.hex(), 16)
                    varByteArray = bytearray.fromhex(raw(varPacketData)[-12:-7].hex())
                    varByteArray.reverse()
                    varTimestampFractionalSecond = int(varByteArray.hex(), 16)
                    varDeviceID = int(raw(varPacketData)[-6:-5].hex(), 16)
                    varSourcePortID = int(raw(varPacketData)[-5:-4].hex(), 16)
                case "exanic" :
                    varTimestampSecond = varPacketMetaData.sec
                    varTimestampFractionalSecond = varPacketMetaData.usec
            
            varIPPacket = varEtherPacket[IP]
            match varIPPacket.proto:
                case 1:
                    varPacketICMPCount += 1
                    varOutputTable.add_row([varPacketTotalCount, len(varPacketData), varEtherPacket.src, varEtherPacket.dst, 'ICMP', hex(varIPPacket.id), varDeviceID, varSourcePortID, varTimestampSecond, varTimestampFractionalSecond])
                case 6:
                    varPacketTCPCount += 1
                    varOutputTable.add_row([varPacketTotalCount, len(varPacketData), varEtherPacket.src, varEtherPacket.dst, 'TCP', hex(varIPPacket.id), varDeviceID, varSourcePortID, varTimestampSecond, varTimestampFractionalSecond])
                case 17:
                    varPacketUDPCount += 1
                    varOutputTable.add_row([varPacketTotalCount, len(varPacketData), varEtherPacket.src, varEtherPacket.dst, 'UDP', hex(varIPPacket.id), varDeviceID, varSourcePortID, varTimestampSecond, varTimestampFractionalSecond])

        print('PCAP analysis done. \nTotal Packets: ' + str(varPacketTotalCount) + '\nTotal ICMP Packets: ' + str(varPacketICMPCount) + '\nTotal TCP Packets: ' + str(varPacketTCPCount) + '\nTotal UDP Packets: ' + str(varPacketUDPCount))
        
    except Scapy_Exception as varErr:
        sys.exit('The script terminated unexceptedly, please check error message: ' + str(varErr))
    
    print(varOutputTable.draw())

def main():
    varParser = argparse.ArgumentParser(prog='cisco-ull-timestamps-decode.py',
                    description='This script will help user to decode timestamp information from packet which is captured by Nexus 3550-F HPT Switch, Nexus 3550-T Switch, exanic-capture Software and exact-capture Software.',
                    epilog='Author: Robbie Shen (yazshen@cisco.com)')
    varParser.add_argument('--file', metavar='<pcap file name>', help='pcap file to decode', required=True)
    varParser.add_argument('--type', choices=['3550fhpt', '3550t', 'exanic', 'exact'], help='packet captured by (Nexus 3550-F HPT, Nexus 3550-T, Exanic-Capture, Exact-Capture)', required=True)
    varArgs = varParser.parse_args()

    varFileName = varArgs.file
    if not os.path.isfile(varFileName):
        sys.exit('The script terminated unexceptedly, please check error message: ' + varFileName + ' does not exist')

    func_decode_pcap(varFileName, varArgs.type)
    
    sys.exit('The script was done successfully!')

if __name__ == '__main__':
    main() 