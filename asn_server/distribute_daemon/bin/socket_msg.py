import struct

from bin.log_and_data import log

#---------------------------------------------------------
#function: socket_send_msg
#arguments:
#  - socket: socket on which the message should be send
#  - message: string with messag to send
#---------------------------------------------------------
def socket_send_msg(socket, message):
    try:
        #prefix message with its length (4 as byte unsigned integer in big-endian byte-order)
        message = struct.pack('>I', len(message)) + message
        #send complete message with sendall to avoid multiple calls to send()
        socket.sendall(message)
    except Exception as e:
        log("socket_send_msg method failed")
        log(type(e))
        log(e)

#---------------------------------------------------------
#function: socket_receive_msg
#arguments:
#  - socket: socket on which the message should be received
#return values:s
#  - data: received data from the socket as string
#---------------------------------------------------------
def socket_receive_msg(socket):
    try:
        #read length of next message from socket
        length_packed = socket_receive_bytes(socket, 4)
        if not length_packed:
            return None
        #unpack length to integer
        length = struct.unpack('>I', length_packed)[0]
        #read message of expected length
        return socket_receive_bytes(socket,length)
    except Exception as e:
        log("socket_receive_msg method failed")
        log(type(e))
        log(e)

#---------------------------------------------------------
#function: socket_receive_bytes
#arguments:
#  - socket: socket on which the message should be received
#  - n: length of message to receive
#---------------------------------------------------------
def socket_receive_bytes(socket, n):
    data = ''
    #receive data of expected length through multiple recv() calls
    while len(data) < n:
        segment = socket.recv(n-len(data))
        if not segment:
            return None
        data += segment
    return data
