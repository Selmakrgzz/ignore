import socket
import struct
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

def main(server_ip, server_port, file_name, window_size):
    #Creating a UDP socket
    #AF_INET indicates that the underlying network is using IPv4
    #SOCK_DGRAM indicates that it is a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #Defining the server address and port
    server_address = (server_ip, server_port)
    #A timeout is set of 0.5 (500ms) seconds for the socket operations to handle non-responsiveness
    sock.settimeout(0.5)

    #Establish connection:
    #Establishing the three-way handshake before sending any data
    #to make sure that the server is alive and we can connect
    #We will therefore send a SYN packet to initiate connection
    #which is the first step in the 3-way handshake
    #The sequence number and acknowledgment number is set
    #to be 0 to start with
    #We'll create a variable client_seq_num and set it to 0
    #so we can later use it for handling the incrementing
    #of the sequence numbers
    #The sequence number and acknowledgement number correspondans:
    #SYN: client_seq = 0, client_ack = 0
    #SYN-ACK: server_seq = 0, server_ack = client_seq + 1 = 1
    #ACK: client_seq = server_ack = 1, client_ack = server_seq + 1 = 1
    client_seq_num = 0
    client_ack_num = 0
    sock.sendto(create_packet(client_seq_num, client_ack_num, SYN), server_address)
    print("SYN packet sent")

    #Receiving response from the server, which in this case
    #should be a SYN-ACK packet. This is the second step in the
    #3-way handshake.
    #The server will send over a packet and the server address
    #since we are only interested in the packet we'll not assign
    #the server address from the tuple to anything
    response, _ = sock.recvfrom(1024)

    #To find out what kind of packet is sent from server we'll
    #have to look at the flag. Therefor we will have to parse 
    #the packet sent from the server. The parse_packet function
    #will return a tuple of values extracted from the packet,
    #but in this case we are just interessted in what the 
    #flags and sequence number, acknowledgement field is holding. 
    #The sequence number and acknowledgment number
    #received from the server will be handled
    #to exchange the right numbers in the 3 way handshake
    server_seq_num, server_ack_num, flags, _ = parse_packet(response)

    #We have to check if the received flags is a SYN-ACK. For
    #that we'll compare the variable flags that holds the info
    #extracted from the packet (parse_packet function).
    #If the server has sent a SYN-ACK, we'll go to the last
    #step of the 3-way handshake which is to send the ACK-packet
    if flags & (SYN | ACK):
        print("SYN-ACK packet is received")

        #Sending an ACK packet to confirm that the connection
        #is established
        #The sequence number is incremented by 1 to acknowledge the server's SYN
        #The client sequence number will be equal to the server acknowledgement number
        #to tell the server that it's SYN-ACK packet was received
        #The client acknowledgment number will be equal to the server sequence number + 1
        sock.sendto(create_packet(server_ack_num, server_seq_num + 1, ACK), server_address)
        print("ACK packet sent")
        print("Connection established")

    #We'll handle the data transfer part
    print("\nData Transfer:")

    #Base is used to manage and track which packets have been sent and which are still
    #awaiting acknowledgment. When an ACK is received, base is updated so that it points
    #to the next sequence number that has not been acknowledged. This ensures that the 
    #window moves appropriately and that data transmission continues efficiently and reliably
    base = client_seq_num + 1

    #next_seq_num is initialized at the start of the transmission (set to the same initial value as base, 
    #but will be incremented before sending the first packet). As data is sent over the network, 
    #next_seq_num is incremented after each packet dispatch
    next_seq_num = base

    #window is a important component for managing the flow of data packets between 
    #the sender and the receiver
    window = {}

    #We'll start with an attempt to open and read from a file in the try. File operations can 
    #fail for various reasons such as the file not existing, lack of permissions, or issues 
    #with the file system. By placing these operations within a try block, the program can 
    #handle such errors gracefully instead of crashing.
    try:
        #To handle the jpeg file we'll open the file in
        #binary mode rb, read the data and return them
        #as a bytes string which will be sent over the
        #DRTP/UDP conncetion to the server
        with open(file_name, "rb") as file:
            #Read a block of data from the file which is on 994 bytes as specified in the assignment
            #Worth to know:
            #I have checked and found out that the jpeg file is 1.74 Mb.
            #If we calculate Mb to bytes the file's size will be 1 825 792 bytes.
            #Since we'll only be sending 994 bytes at the time, that will
            #make approximatly 1838 packets to send :o
            data = file.read(994)
            #We'll continue until all data is sent and acknowledged
            while data or window:
                #We have to make sure to send data while the window is not full and there is data to send
                #This is the first key component of the Go-Back-N where we are managing packet sending and
                #window managment
                while next_seq_num < base + window_size and data:
                    #Creating a packet with the current sequence number and data
                    packet = create_packet(next_seq_num, 0, 0, data)
                    #Sending the packet to the server
                    sock.sendto(packet, server_address)
                    #We'll have to log the packet sending action with the time, sequence number and sliding window
                    #to keep on track which packet is sent etc
                    print(f"{datetime.now().strftime('%H:%M:%S.%f')} -- packet with seq = {next_seq_num} is sent, sliding window = {list(window.keys())}")
                    #Update the window list by adding the sent packet
                    window[next_seq_num] = packet
                    #Increment the sequence number
                    next_seq_num += 1
                    #Read the next block of data so we don't send the same
                    #data again
                    data = file.read(994)

                #We have to handle the acknowledgments from the server as well
                #This is the second key component of the Go-Back-N where we are handling the
                #received acknowledgements and updating the servers window
                try:
                    #Receive an acknowledgment packet from the server
                    #which tells us that the server received the sent packet
                    #We'll only have use for the ack_packet not the address server is sending
                    ack_packet, _ = sock.recvfrom(1024)
                    #Parse the acknowledgment packet. We'll only need the ack_num 
                    #containing the acknowledgement number and ack_flags containting
                    #the ACK flag
                    _, ack_num, ack_flags, _ = parse_packet(ack_packet)
                    #Check if the packet is an ACK
                    if ack_flags & ACK:
                        #We'll have to log the packet received action with the time, acknowledgment
                        #number to keep on track with the acknowledgment receipt
                        print(f"{datetime.now().strftime('%H:%M:%S.%f')} -- ACK for packet = {ack_num} is received")

                        #This loop is responsible for updating the sender's window 
                        #after receiving an acknowledgment from the server. It ensures 
                        #that the window is moved forward appropriately, acknowledging all the 
                        #packets that have been successfully received by the server up 
                        #to a certain sequence number.
                        while base <= ack_num:
                            window.pop(base, None)
                            base += 1
                except socket.timeout:
                    #Handle the case where the ACK is not received and we have reached the timeout
                    #This loop handles the retransmission of packets that have not been acknowledged 
                    #by the server. It is triggered when the timeout occurs, indicating that the server
                    #may not have received one or more packets, or the ACKs for those packets were lost.
                    #This is the last component of the Go-Back-N where we resend all packets from the 
                    #last acknowledged packet to ensure reliable delivery if a timeout occurs.
                    for seq in range(base, next_seq_num):
                        #Resend all packets in the window
                        print(f"{datetime.now().strftime('%H:%M:%S.%f')} -- Resending packet with seq = {seq}")
                        sock.sendto(window[seq], server_address)

    finally:
        #When all the packets is sent, we'll have to tear down the connection
        print("\nConnection Teardown:")
        #First off we'll  send a FIN packet to indicate that the connection termination
        sock.sendto(create_packet(next_seq_num, 0, FIN), server_address)
        print("FIN packet sent")
        #We'll have to wait for a FIN-ACK from the server that will ensure us that
        #the server has received our teardown request

        #Receiving the fin-ack packet from server
        fin_ack_packet, _ = sock.recvfrom(1024)
        #Parsing the fin-ack packet so we can extract
        #the fin-ack flags to make sure that they're correct
        _, _, fin_ack_flags, _ = parse_packet(fin_ack_packet)
        #Check if the received packet is a FIN-ACK
        if fin_ack_flags & (ACK | FIN):
            print("FIN ACK packet received")
            print("\nConnection Closes")
        #Closing the socket on a reliable way 
        sock.close()

if __name__ == "__main__":
    main()