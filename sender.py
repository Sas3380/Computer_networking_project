import socket                 
import struct                 
import time                    

sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
server_address = ('localhost', 12345)                           

timeout = 1                  # timeout for waiting on ACKs
max_sequence = 256        

WINDOW_SIZE = 4           
USE_GOBACKN = True          # flag to enable Go-Back-N (True) or Stop-and-Wait (False)

# variables for Stop-and-Wait
sequence_number = 0         # sequence number of current packet to send

# variables for Go-Back-N
base = 0                   # base of sending window (lowest unacknowledged sequence number)
next_seq_num = 0           # next sequence number to send (can be ahead of base)
packets = []               # list to store packets (for retransmission)
timer_start = None         # timestamp when timer started (for timeout handling)

# function to create packet bytes from sequence number and data string
def make_packet(seq, data):
    return struct.pack('!I', seq) + data.encode('utf-8')  # pack seq (4 bytes) + message bytes

# Stop-and-Wait sending function
def send_stop_and_wait():
    global sequence_number    # use global sequence number
    while True:              # infinite sending loop
        message = f"Message {sequence_number}"         # create message string
        packet = make_packet(sequence_number, message) # create packet bytes
        sender_socket.sendto(packet, server_address)  # send packet to receiver
        print(f"Sent: {message} with sequence number {sequence_number}")

        sender_socket.settimeout(timeout)              # set timeout waiting for ACK
        try:
            ack, _ = sender_socket.recvfrom(4096)     # receive ACK from receiver
            ack_seq = struct.unpack('!I', ack[:4])[0] # extract sequence number from ACK
            print(f"Received ACK for sequence number {ack_seq}")
            if ack_seq == sequence_number:             # if ACK matches sent packet's sequence
                sequence_number += 1                    # move to next packet number
            else:
                print("Wrong ACK, retransmitting...")  # else retransmit current packet
        except socket.timeout:
            print("Timeout! Retransmitting...")        # if no ACK received in time, retransmit

# Go-Back-N sending function
def send_gobackn():
    global base, next_seq_num, timer_start   # use global variables for window management

    # helper function to check if seq is within current window
    def is_in_window(seq):
        return base <= seq < base + WINDOW_SIZE

    # prepare a fixed number of packets/messages in advance (here 20 messages)
    for i in range(20):
        msg = f"Message {i}"
        pkt = make_packet(i, msg)
        packets.append(pkt)

    # main sending loop runs while base (lowest unACKed) is less than total packets
    while base < len(packets):
        # send packets in the current window (from next_seq_num up to base + window size)
        while next_seq_num < base + WINDOW_SIZE and next_seq_num < len(packets):
            sender_socket.sendto(packets[next_seq_num], server_address)  # send packet
            seq_num = struct.unpack('!I', packets[next_seq_num][:4])[0]  # extract seq num for printing
            print(f"Sent packet with sequence number {seq_num}")

            if base == next_seq_num:
                timer_start = time.time()    # start timer when first packet in window sent
            next_seq_num += 1               # increment next_seq_num to send next packet

        sender_socket.settimeout(timeout)    # set socket timeout for ACK waiting
        try:
            ack, _ = sender_socket.recvfrom(4096)          # receive ACK packet
            ack_seq = struct.unpack('!I', ack[:4])[0]      # extract ack sequence number
            print(f"Received ACK for sequence number {ack_seq}")
            if ack_seq >= base:
                base = ack_seq + 1          # slide window forward past acknowledged packets
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