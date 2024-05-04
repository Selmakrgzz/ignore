import socket
import struct
import sys
import time
from datetime import datetime

#Im using constants for the flags for the simplicity
#when creating packets.
#The binary representation of the flags
#SYN=1000, ACK=0100, FIN=0010
SYN = 0x8
ACK = 0x4
FIN = 0x2

#Checking the struct offical page I found out
#that I will have to use HHH which is equal
#to 6 bytes: 3 unsigned shorts (2 bytes each)
header_format = '!HHH'

#Taking sequence number, acknowledgement number, flags
#and data as parameters to create a new packet.
#data is set to emty(0 bytes) as default for the 
#simplicity when establishing the 3 way handshake etc.
#Returns a packet that is set together with the
#header and data
def create_packet(seq_num, ack_num, flags, data=b''):
    #Creating a package with header information and application data
    #Input arguments are; sequence number, acknowledement number,
    #flags(only 4 bits) and application data
    #The header values will be packed according to the header_format HHH
    header = struct.pack(header_format, seq_num, ack_num, flags)

    #Once the header is created, we add the application data
    #The application data is on 994 bytes and the header 6 bytes = 1000 bytes
    packet = header + data

    return packet

#Function that parses the packet given in as parameter
#so we can extract the header and data. Since we know
#that the header is in the first 6 bytes of the packet
#we can extract the header as shown. The rest of the remaining
#bytes (994) of the packet is data.
#It will return the sequence number, acknowledgment number,
#flags from the header and the data
def parse_packet(packet):
    header = packet[:6]
    data = packet[6:]
    #Unpacking the header based on the specific header format
    #and header extracted from the packet.
    seq_num, ack_num, flags = struct.unpack(header_format, header)
    return seq_num, ack_num, flags, data
    

def main(ip, port):
    #Defining the server socket and address
    server_address = (ip, port)

    #Creating a UDP socket
    #AF_INET indicates that the underlying network is using IPv4
    #SOCK_DGRAM indicates that it is a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        #Bind the server socket
        sock.bind(server_address)
    except: 
        #Throwing an exception if the binding fails
        print("Bind failed. Error : ")
        sys.exit()

    #Initializing variables for tracking sequence numbers, time, and data received from the client
    #Initialize the expected sequence number for incoming packets to hold track on if there is any packets
    #out of order
    expected_seq_num = 1 
    #Initialize the start time for tracking data reception 
    start_time = None  
    #Initialize the total data received counter
    total_data_received = 0  
    #Initicalize the server sequence number
    server_seq_num = 0

    try:
        #An infinite loop where the server continuously waits to receive packets from the client
        while True:
            #Receive a packet and client's address from the client
            packet, client_address = sock.recvfrom(1024)
            #Get the current time
            current_time = datetime.now().strftime("%H:%M:%S.%f")  
            #Parsing the received packet and extract client sequence number, flags and data
            client_seq_num, _, flags, data = parse_packet(packet)  

            #Since the client will be sending many packets to the server, we'll have to
            #handle different types of packets based on their flags

            #If flags equals a SYN flag
            if flags & SYN:
                #This is the first step in the 3 way handshake on server side 
                #The client has sent a SYN packet to initiate connection
                #which we have to handle now
                print("SYN packet is received")
                #The second step in the 3 way handshake is to send a SYN-ACK packet to the
                #client to acknowledge and establish a connection 
                sock.sendto(create_packet(server_seq_num, client_seq_num + 1, SYN | ACK), client_address)
                print("SYN-ACK packet is sent")
                #We'll continue again from where we left
                continue

            #If flags equals a ACK flag and data is emty
            if flags & ACK and not data:
                #Handle ACK packet for connection establishment
                print("ACK packet is received")
                print("Connection established\n")
                #We'll continue again from where we left
                continue

            #If flags equals a FIN flag 
            if flags & FIN:
                #When we receive a FIN flag, it means that the client wants to terminate the connection
                #and want to make it on a reliable way where the client gives the server message about
                print("\nFIN packet is received")
                #Send FIN-ACK packet to acknowledge termination to the client
                sock.sendto(create_packet(server_seq_num, client_seq_num + 1, ACK | FIN), client_address)
                print("FIN ACK packet is sent")
                #Exit the loop to close the connection
                break  
            
            #Checking if the received client sequence number is the same as the expected sequence number
            #This is important to make sure that we don't send ack packets to wrong received packets
            if client_seq_num == expected_seq_num:
                #Handle in-order data packet
                print("{} -- packet {} is received".format(current_time, client_seq_num))
                #Sending ACK for the received packet back to the client
                sock.sendto(create_packet(0, client_seq_num, ACK), client_address)
                print("{} -- sending ack for the received {}".format(current_time, client_seq_num))
                #Update expected sequence number for the next packet
                expected_seq_num += 1  
                #Tracking the total data received so we can calculate the throughput later
                total_data_received += len(data)  
                #This ensures that the start time of the data transfer is recorded 
                #only once when the first data is received in the correct order. 
                #This is crucial for accurately calculating the throughput 
                #based on the time taken to receive the data.
                if not start_time:
                    start_time = time.time()  
            else:
                #Handling the out-of-order data packet
                print("{} -- packet {} received out of order, expected {}".format(current_time, client_seq_num, expected_seq_num))

    finally:
        #Calculate and display throughput if data was received
        if start_time:
            #Calculate the elapsed time
            elapsed_time = time.time() - start_time  
            if elapsed_time > 0:
                #Calculate throughput in Mbps
                throughput = (total_data_received * 8) / (elapsed_time * 1000000)  
                print("\nThe throughput is {:.2f} Mbps".format(throughput))
        
        #Close the socket and print connection closure message
        sock.close()
        print("\nConnection Closes")

if __name__ == "__main__":
    main()

