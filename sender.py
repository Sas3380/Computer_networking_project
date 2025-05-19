import socket
import struct
import time
import zlib

def cal_checksum(data):
    return zlib.crc32(data) & 0xFFFF

def verify_checksum(packet):
    data = packet[:-2]  #checksum
    recieved_checksum = struct.unpack('!H', packet[-2:])[0]
    calculated_checksum = cal_checksum(data)
    return recieved_checksum == calculated_checksum


def making_packet(sequence_num, msg):
    # pack, sequence number + msg bytes + checksum
    seq_and_msg = struct.pack('!I', sequence_num) + msg.encode('utf-8')
    checksum = cal_checksum(seq_and_msg)
    return seq_and_msg + struct.pack('!H', checksum)  # append checksum at the end


def reliable_UDP_sender(window_size=5, packets=20, timeout=2):
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('localhost', 12345)

    w_base = 0  #window base or start
    next_seq_num = 0
    packets = []  # storing packets for fast_retransmission
    start_timer = None

    # duplicate ACK tracking for fast retransmission
    dupli_ACK_count = 0
    last_ACK_received = -1

    # preparing packets in advance
    for i in range(packets):
        msg = f"message {i}"
        pkt = making_packet(i, msg)
        packets.append(pkt)

    client_socket.settimeout(0.1)

    print("starting reliable UDP sender..")

    #itearte on all packets
    while w_base < packets:

        # send packets in window
        while next_seq_num < w_base + window_size and next_seq_num < packets:
            
            client_socket.sendto(packets[next_seq_num], server_address)
            print(f"Sent packet {next_seq_num}")
            
            if w_base == next_seq_num:#if first packet in the current window
                timer_start = time.time()
            next_seq_num += 1

     
        # wait for ack and timeout
        try:
            ACK_packet, _ = client_socket.recvfrom(4096)

            if not verify_checksum(ACK_packet):
                print("corrupted ACK received so Ignore it.")
                continue

            ACK_seq = struct.unpack('!I', ACK_packet[:4])[0]
            print(f"received ACK for packet {ACK_seq}")

            # fast retransmission logic
            if ACK_seq == last_ACK_received:
                dupli_ACK_count += 1
            else:
                dupli_ACK_count = 1  


            last_ACK_received = ACK_seq

            if dupli_ACK_count == 3:
                print(f"fast retransmission for packet {w_base}")
                client_socket.sendto(packets[w_base], server_address)#send the oldest unack packet
                start_timer = time.time()

            # slide window forward
            if ACK_seq >= w_base:
                w_base = ACK_seq + 1
                start_timer = time.time()

        except socket.timeout:
            # check timeout to retransmit all unacknowledged packets
            if start_timer and (time.time() - timer_start) > timeout:
                
                print(f"timeout! Retransmitting packets from {w_base} to {next_seq_num - 1}")
               
                for i in range(w_base, next_seq_num):
                    client_socket.sendto(packets[i], server_address)
                    print(f"retransmitted packet {i}")
               
                timer_start = time.time()#reset

    print("all packets sent and acknowledged")
    client_socket.close()

if __name__ == '__main__':
    reliable_UDP_sender(window_size=5, packets=20)
