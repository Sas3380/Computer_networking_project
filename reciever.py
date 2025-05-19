
import socket
import struct
import random
import zlib

def cal_checksum(data):
    return zlib.crc32(data) & 0xFFFF#16 bits


def verify_checksum(packet):
    data = packet[:-2]  
    recieved_checksum = struct.unpack('!H', packet[-2:])[0]
    calculated_checksum = cal_checksum(data)
    return recieved_checksum == calculated_checksum


def simulate_packet_loss(loss_prob=0.1):
    # simulate 10% loss by returning False
    return random.random() > loss_prob


def reliable_UDP_receiver(window_size=5, enable_packet_loss=True):
    
    #UDP socket creation
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('localhost', 12345))
    print("receiver started, waiting for packets..")

    expected_seq_num = 0
    last_ACK_sent = -1  # for tracking last ACK sent


    while True:
        #recieve packet and sender address
        packet, client_address = server_socket.recvfrom(4096)

        if enable_packet_loss and not simulate_packet_loss():
            print("simulated packet loss. Packet dropped.")
            continue

        if not verify_checksum(packet):
            print("Checksum mismatched, so discard the corrupted packet.")
            continue #if corrupted drop silently.


        # extract seq_number and message
        sequence_num = struct.unpack('!I', packet[:4])[0]
        msg_bytes = packet[4:-2]
        msg = msg_bytes.decode('utf-8')

        #if within window range
        if expected_seq_num <= sequence_num < expected_seq_num + window_size:

            if sequence_num == expected_seq_num:
                print(f"received expected packet {sequence_num}: {msg}")
                expected_seq_num = expected_seq_num + 1
                last_ACK_sent = sequence_num
            
            else:
                print(f"received packet {sequence_num} inside window but out of order so ignore it.")


            # Prepare ACK packet with checksum
            ACK_seq_bytes = struct.pack('!I', last_ACK_sent)
            ACK_checksum = cal_checksum(ACK_seq_bytes)

            ACK_packet = ACK_seq_bytes + struct.pack('!H', ACK_checksum)
            server_socket.sendto(ACK_packet, client_address)
            print(f"sent ACK for sequence number {last_ACK_sent}")

        
        else: #if out of window range

            print(f"packet {sequence_num} out of window. so discard it.")
            
            #send ack for last in-order packet
            ACK_seq_bytes = struct.pack('!I', last_ACK_sent)
            ACK_checksum = cal_checksum(ACK_seq_bytes)

            ACK_packet = ACK_seq_bytes + struct.pack('!H', ACK_checksum)
            server_socket.sendto(ACK_packet, client_address)
            print(f"resent ACK for sequence number {last_ACK_sent}")

if __name__ == '__main__':
    reliable_UDP_receiver(window_size=5, enable_packet_loss=True)
