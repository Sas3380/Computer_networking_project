import socket                 
import struct                 
import time     
import zlib                

sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
server_address = ('localhost', 12345)                           

timeout = 1                  # timeout for waiting on ACKs
max_sequence = 256        

WINDOW_SIZE = 4           
USE_GOBACKN = True          #make it false if not using the goback in

sequence_number = 0        

base = 0                  
next_seq_num = 0           
packets = []               
timer_start = None         # timestamp when timer started 


#create packet bytes from sequence number and data string
def make_packet(seq, data):
      payload = struct.pack('!I', seq) + data.encode('utf-8')

      checksum = zlib.crc32(payload) & 0xFFFF
      return payload + struct.pack('!H', checksum) #append to the end of the packet

# Stop-and-Wait sending function
def send_stop_and_wait():
    global sequence_number    
    while True:              
        message = f"Message {sequence_number}"         
        packet = make_packet(sequence_number, message) # create packet bytes 
        sender_socket.sendto(packet, server_address)  # send packet bytes to receiver

        print(f"Sent: {message} with sequence number {sequence_number}")

        sender_socket.settimeout(timeout)              
        try:
            ack, _ = sender_socket.recvfrom(4096)     # receive ACK from receiver, just ignore the address
            ack_seq = struct.unpack('!I', ack[:4])[0] # extract sequence number from ACK
            
            print(f"Received ACK for sequence number {ack_seq}")
            if ack_seq == sequence_number:             
                sequence_number += 1                    
            else:
                print("Wrong ACK, retransmitting...")  

        except socket.timeout:
            print("Timeout! Retransmitting...")        # if no ACK received in time, retransmit



def send_gobackn():
    global base, next_seq_num, timer_start   # use global variables for window management

    #check if seq is within current window
    def is_in_window(seq):
        if seq >= base:
            return seq < base + WINDOW_SIZE
        else:
            return False

    # prepare a fixed number of packets/messages in advance with checksum
    for i in range(20):
        msg = f"Message {i}"
        pkt = make_packet(i, msg)
        packets.append(pkt)


    while base < len(packets):
        # send packets from next_seq_num up to base + window size
        while next_seq_num < base + WINDOW_SIZE and next_seq_num < len(packets):
            
            sender_socket.sendto(packets[next_seq_num], server_address) 
            seq_num = struct.unpack('!I', packets[next_seq_num][:4])[0]  # extract seq num 
            print(f"Sent packet with sequence number {seq_num}")

            if base == next_seq_num:
                timer_start = time.time()    # start timer when first packet in window sent
            next_seq_num += 1               


        sender_socket.settimeout(timeout)    
        try:
            ack, _ = sender_socket.recvfrom(4096)          # receive ACK packet
            ack_seq = struct.unpack('!I', ack[:4])[0]      # extract ack sequence number
            print(f"Received ACK for sequence number {ack_seq}")

            if ack_seq >= base:
                base = ack_seq + 1          # slide window forward 
                timer_start = time.time()   # reset timer when window slides

        except socket.timeout:
            # on timeout, retransmit all unacknowledged packets in the window
            print("Timeout! Retransmitting window...")
            for i in range(base, next_seq_num):
                sender_socket.sendto(packets[i], server_address)
                seq_num = struct.unpack('!I', packets[i][:4])[0]
                print(f"Retransmitted packet with sequence number {seq_num}")
            timer_start = time.time()       # reset timer after retransmission

def main():
    if USE_GOBACKN:
        print("Starting Go-Back-N transmission...")
        send_gobackn()          # run Go-Back-N sending method
    else:
        print("Starting Stop-and-Wait transmission...")
        send_stop_and_wait()    # run Stop-and-Wait sending method

if __name__ == '__main__':
    main()    # start the program



#stop and wait method

# Send one packet.
# Wait for confirmation (ACK).
# If confirmation received and correct, send the next packet.
# If no confirmation or wrong one, send the same packet again.
# Keep doing this forever.