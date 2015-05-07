#!/usr/bin/env python

# Signed Certificate Timestamp TLS extension verifier  
# Copyright (c) 2015 Pier Carlo Chiodi - http://www.pierky.com
#
# https://github.com/pierky/sct-verify

import sys
import subprocess
import base64
import struct

OPENSSL_PATH="openssl"

LOGS = [
    { "Name": "Aviator",
    "Key": "-----BEGIN PUBLIC KEY-----\n"
    "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE1/TMabLkDpCjiupacAlP7xNi0I1J\n"
    "YP8bQFAHDG1xhtolSY1l4QgNRzRrvSe8liE+NPWHdjGxfx3JhTsN9x8/6Q==\n"
    "-----END PUBLIC KEY-----",
    "LogID": "aPaY+B9kgr46jO65KB1M/HFRXWeT1ETRCmesu09P+8Q=" },

    { "Name": "Digicert Log",
    "Key": "-----BEGIN PUBLIC KEY-----\n"
    "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEAkbFvhu7gkAW6MHSrBlpE1n4+HCF\n"
    "RkC5OLAjgqhkTH+/uzSfSl8ois8ZxAD2NgaTZe1M9akhYlrYkes4JECs6A==\n"
    "-----END PUBLIC KEY-----",
    "LogID": "VhQGmi/XwuzT9eG9RLI+x0Z2ubyZEVzA75SYVdaJ0N0=" },

    { "Name": "Pilot",
    "Key": "-----BEGIN PUBLIC KEY-----\n"
    "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEfahLEimAoz2t01p3uMziiLOl/fHT\n"
    "DM0YDOhBRuiBARsV4UvxG2LdNgoIGLrtCzWE0J5APC2em4JlvR8EEEFMoA==\n"
    "-----END PUBLIC KEY-----",
    "LogID": "pLkJkLQYWBSHuxOizGdwCjw1mAT5G9+443fNDsgN3BA=" },

    { "Name": "Rocketeer",
    "Key": "-----BEGIN PUBLIC KEY-----\n"
    "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEIFsYyDzBi7MxCAC/oJBXK7dHjG+1\n"
    "aLCOkHjpoHPqTyghLpzA9BYbqvnV16mAw04vUjyYASVGJCUoI3ctBcJAeg==\n"
    "-----END PUBLIC KEY-----",
    "LogID": "7ku9t3XOYLrhQmkfq+GeZqMPfl+wctiDAMR7iXqo/cs=" },

    { "Name": "Izenpe",
    "Key": "-----BEGIN PUBLIC KEY-----\n"
    "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEJ2Q5DC3cUBj4IQCiDu0s6j51up+T\n"
    "ZAkAEcQRF6tczw90rLWXkJMAW7jr9yc92bIKgV8vDXU4lDeZHvYHduDuvg==\n"
    "-----END PUBLIC KEY-----",
    "LogID": "dGG0oJz7PUHXUVlXWy52SaRFqNJ3CbDMVkpkgrfrQaM=" },

    { "Name": "Certly",
    "Key": "-----BEGIN PUBLIC KEY-----\n"
    "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAECyPLhWKYYUgEc+tUXfPQB4wtGS2M\n"
    "NvXrjwFCCnyYJifBtd2Sk7Cu+Js9DNhMTh35FftHaHu6ZrclnNBKwmbbSA==\n"
    "-----END PUBLIC KEY-----",
    "LogID": "zbUXm3/BwEb+6jETaj+PAC5hgvr4iW/syLL1tatgSQA=" }

    ]

if len( sys.argv ) <= 1:
    print( "Missing hostname argument." )
    print( "Usage: ./sct-verify hostname" )
    print( "" )
    print( "Example:" )
    print( "  ./sct-verify sni.velox.ch" )
    print( "" )
    print( "Known hosts implementing SCT TLS Extensions:" )
    print( " - sni.velox.ch" )
    print( " - ritter.vg" )
    quit()

HostName = sys.argv[1]

Args = [ OPENSSL_PATH ]
Args.extend( [ "s_client", "-serverinfo", "18", "-connect", "%s:443" % HostName, "-servername", HostName ])

OpenSSL= subprocess.Popen( Args, stdin=open('/dev/null', 'r'), stdout=subprocess.PIPE, stderr=subprocess.PIPE )
OpenSSL_stdout, OpenSSL_stderr = OpenSSL.communicate()
OpenSSL_exitcode = OpenSSL.wait()

if OpenSSL_exitcode != 0:
    print("OpenSSL can't connect to %s" % HostName)
    print(OpenSSL_stderr)
    quit()

ServerInfo18 = ""
ServerInfo18_Add = False
EECert = ""
EECert_Add = False
for L in OpenSSL_stdout.split('\n'):
    if L == "-----BEGIN SERVERINFO FOR EXTENSION 18-----":
        ServerInfo18_Add = True
    elif L == "-----END SERVERINFO FOR EXTENSION 18-----":
        ServerInfo18_Add = False
    elif L == "-----BEGIN CERTIFICATE-----":
        EECert_Add = True
    elif L == "-----END CERTIFICATE-----":
        EECert_Add = False
    elif ServerInfo18_Add:
        if ServerInfo18:
            ServerInfo18 = ServerInfo18 + '\n'
        ServerInfo18 = ServerInfo18 + L
    elif EECert_Add:
        if EECert:
            EECert = EECert + '\n'
        EECert = EECert + L

EECertDER = base64.b64decode( EECert )

Data = base64.b64decode( ServerInfo18 )
DataLen = len(Data)

def ToHex( v ):
    if type(v) is int or type(v) is long:
        return hex(v)
    else:
        return ":".join("{:02x}".format(ord(c)) for c in v)

def Read( buf, offset, format ):
    Values = struct.unpack_from( format, buf, offset )
    NewOffset = offset + struct.calcsize( format )

    Ret = ()
    Ret = Ret + ( NewOffset, )
    Ret = Ret + Values
    return Ret

def ReadSCT( SCT ):
    print("===========================================================")
    Offset = 0

    Offset, SCTVersion = Read( SCT, Offset, "!B" )

    Offset, SCTLogID = Read( SCT, Offset, "!32s" )
    Base64LogID = base64.b64encode( SCTLogID )

    Offset, SCTTimestamp = Read( SCT, Offset, "!Q" )

    Offset, SCTExtensionsLen = Read( SCT, Offset, "!H" )

    #FIXME
    if SCTExtensionsLen > 0:
        print("Extensions length > 0; not implemented")
        return

    Offset, SCTSignatureAlgHash = Read( SCT, Offset, "!B" )
    Offset, SCTSignatureAlgSign = Read( SCT, Offset, "!B" )

    Offset, SCTSignatureLen = Read( SCT, Offset, "!H" )
    Offset, SCTSignature = Read( SCT, Offset, "!%ss" % SCTSignatureLen )

    # print SCT information

    print( "Version   : %s" % ToHex( SCTVersion ) )
    SCTLogID1, SCTLogID2 = struct.unpack( "!16s16s", SCTLogID )
    print( "LogID     : %s" % ToHex( SCTLogID1 ) )
    print( "            %s" % ToHex( SCTLogID2 ) )
    print( "LogID b64 : %s" % Base64LogID )
    print( "Timestamp : %s (%s)" % ( SCTTimestamp, ToHex( SCTTimestamp ) ) )
    print( "Extensions: %s (%s)" % ( SCTExtensionsLen, ToHex( SCTExtensionsLen )) )
    print( "Algorithms: %s/%s (hash/sign)" % ( ToHex( SCTSignatureAlgHash ), ToHex ( SCTSignatureAlgSign ) )) 

    SigOffset = 0
    while SigOffset < len( SCTSignature ):
        if len( SCTSignature ) - SigOffset > 16:
            SigBytesToRead = 16
        else:
            SigBytesToRead = len( SCTSignature ) - SigOffset
        SigBytes = struct.unpack_from( "!%ss" % SigBytesToRead, SCTSignature, SigOffset )[0]

        if SigOffset == 0:
            print( "Signature : %s" % ToHex( SigBytes ) )
        else:
            print( "            %s" % ToHex( SigBytes ) )
    
        SigOffset = SigOffset + SigBytesToRead

    # look for signing log and its key

    PubKey = None
    for Log in LOGS:
        if Log["LogID"] == Base64LogID:
            print( "Log found : %s" % Log["Name"])
            PubKey = Log["Key"]

    if not PubKey:
        print("Log not found")
        return

    # signed data

    # 1 version
    # 1 signature_type
    # 8 timestamp
    # 2 entry_type
    # 3 DER lenght
    # x DER
    # 2 extensions length

    EECertDERLen = len( EECertDER )
    _, EECertDERLen1, EECertDERLen2, EECertDERLen3 = struct.unpack( "!4B", struct.pack( "!I", EECertDERLen ) )
    
    Data = struct.pack("!BBQhBBB%ssh" % len( EECertDER ), SCTVersion, 0, SCTTimestamp, 0, EECertDERLen1, EECertDERLen2, EECertDERLen3, EECertDER, SCTExtensionsLen )

    File = open("tmp-signeddata.bin", "wb")
    File.write( Data )
    File.close()

    File = open("tmp-pubkey.pem", "w")
    File.write( PubKey )
    File.close()

    File = open("tmp-signature.bin", "wb")
    File.write( SCTSignature )
    File.close()

    Args = [ OPENSSL_PATH ] 
    Args.extend( [ "dgst", "-sha256", "-verify", "tmp-pubkey.pem", "-signature", "tmp-signature.bin", "tmp-signeddata.bin" ] )

    OpenSSL= subprocess.Popen( Args, stdin=open('/dev/null', 'r'), stdout=subprocess.PIPE, stderr=subprocess.PIPE )
    OpenSSL_stdout, OpenSSL_stderr = OpenSSL.communicate()
    OpenSSL_exitcode = OpenSSL.wait()

    if OpenSSL_exitcode == 0:
        print( "Result    : %s" % OpenSSL_stdout )
    else:
        print( "OpenSSL error - Exit code %d" % OpenSSL_exitcode )
        print( OpenSSL_stderr )
 
Offset = 0
Offset, TLS_ExtensionType, TLS_ExtensionLen = Read( Data, Offset, "!HH" )
Offset, SignedCertificateTimestampListLen = Read( Data, Offset, "!H" )

while Offset < DataLen:
    Offset, SCTLen = Read( Data, Offset, "!H" )
    Offset, SCT = Read( Data, Offset, "!%ss" % SCTLen )
    ReadSCT( SCT )
