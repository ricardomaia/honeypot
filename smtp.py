#!/usr/bin/python3
# encoding: utf-8

__author__ = "Ricardo Maia"
__copyright__ = "Copyright 2015"
__credits__ = ["Ricardo Maia"]
__license__ = "GPL"
__version__ = "0.3"
__maintainer__ = "Ricardo Maia"
__email__ = "rsmaia@gmail.com"
__status__ = "Development"

import socket
import time
import threading
import logging
import re

def handleConnection(conn, addr, socketAddress, socketPort):
    
    temp = ""
    terminalInput = ""
    log = getLogger()
    lastCommand = ""
    
    remoteAddr = getRemoteAddr(addr)
    remotePort = getRemotePort(addr)
    
    sendMessage(conn, "Connection received\r\n")
    sendMessage(conn, "220 mail.gdfnet.df.gov.br ESMTP\r\n") 
    
    log.info("dst_port=" + str(socketPort) + " dst_ip=" + str(socketAddress) + " src_port=" + remotePort + " src_ip=" + remoteAddr + " action=\"open\"")
    
    while True:

        try:
            data = conn.recv(1024)        
            temp = temp + data.decode('utf-8')          
            time.sleep(.01)                  
                        
            if temp.count("\n") or temp.count("\r\n"):
                terminalInput = temp.strip()
                temp = ""                
                
                if terminalInput.count(":"):
                    commandTuple = terminalInput.split(":",1)
                    command = commandTuple[0]
                    params =  commandTuple[1]     
                elif terminalInput.count(" "):
                    commandTuple = terminalInput.split(" ",1)
                    command = commandTuple[0]
                    params =  commandTuple[1]
                else:
                    command = terminalInput
                    params =  ""                  
                                
                cmdResult = execCommand(conn, command, params, lastCommand)
                lastCommand = command                
                
                log.info("dst_port=" + str(socketPort) + " dst_ip=" + str(socketAddress) + " src_port=" + remotePort + " src_ip=" + remoteAddr + " cmd=" + command + " params=" + params)              
                
                if cmdResult != 0:         
                    break # Exit from loop and close connection.
                                    
        except UnicodeDecodeError:
            log.error("Error. Only unicode characters are accepted")
            
    conn.close()
    log.info("dst_port=" + str(socketPort) + " dst_ip=" + str(socketAddress) + " src_port=" + remotePort + " src_ip=" + remoteAddr + " action=\"close\"")
    return True

def getRemoteAddr(addr):
    return str(addr[0])

def getRemotePort(addr):
    return str(addr[1])

def getLogger(filePath = 'smtp.log'):
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(filePath)
    
    handler = logging.FileHandler(filePath)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %I:%M:%S %p')
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger

def sendMessage(conn, msg = ''):
    msg = str.encode( msg )
    conn.sendall( msg )    

def startServer(socketAddress = '127.0.0.1', socketPort = 25):
    
    serverSocket = socket.socket()
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)    
    
    try:
        serverSocket.bind((socketAddress, socketPort))
        serverSocket.listen(100) 
        log = getLogger() 
        log.info("msg=\"Start listening on  " + str(socketAddress) + ":" + str(socketPort) +  "\" action=start")
        
    
        while True:
            conn, addr = serverSocket.accept()
            
            try:
                threading.Thread(target=handleConnection,args=(conn, addr, socketAddress, socketPort)).start()            
            except e:
                log.info("msg=\"Threading Error. " + e.strerror + ".(" + str(e.errno) + ").\" action=error")
        
        serverSocket.close()    
        
    except KeyboardInterrupt as ki:
        log.info("msg=\"Keyboard Interruption.\" action=error") 
        
    except ConnectionResetError as cre:
        log.info("msg=\"Connection reset error.\" action=error")   
                
    except OSError as ose:
        log.info("msg=\"OsError. " + ose.strerror + ".(" + str(ose.errno) + ").\" action=error")
        
    finally:
        pass

def execCommand(conn, command, params="", lastCommand = "", exitCommand = 'quit'):
                        
    if command == exitCommand:
        sendMessage(conn, "\r221 2.0.0 Bye\r\n")
        return -1  
    
    if command == "helo":
        if params == "":
            sendMessage(conn, "\r501 Syntax: HELO hostname\r\n")
        else:
            sendMessage(conn, "\r250 mail.gdfnet.df.gov.br\r\n")
        return 0
    
    if command == "mail from":
        mailPattern = re.compile("^<.*>+$")
        mailString = u""+params
        searchResult = re.search(mailPattern, mailString)
        
        if searchResult:
            sendMessage(conn, "\r250 2.1.0 Ok\r\n")
        else:
            sendMessage(conn, "\r501 5.1.7 Bad sender address syntax\r\n")
        return 0
            
    if command == "rcpt to":
        mailPattern = re.compile("^<.*>+$")
        mailString = u""+params
        searchResult = re.search(mailPattern, mailString)
        
        if searchResult:
            sendMessage(conn, "\r250 2.1.5 Ok\r\n")
        else:
            sendMessage(conn, "\r501 5.1.3 Bad recipient address syntax\r\n")
        return 0            
    
    if command == "data":
        sendMessage(conn, "\r354 End data with <CR><LF>.<CR><LF>\r\n")
        return 0
        
    if command == ".":
        sendMessage(conn, "\r250 2.0.0 Ok: queued as 3EA8750037\r\n")
        return 0

    if command not in ['helo', 'mail from', 'rcpt to', 'data', '.', exitCommand]:
        if lastCommand != "data":
            sendMessage(conn, "\r502 5.5.2 Error: command not recognized\r\n")
        return 0

startServer()
