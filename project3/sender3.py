import socket
import struct
import time
import zlib

# Function to calculate checksum (CRC32 truncated to 16 bits)
def calculate_checksum(data_bytes):
    return zlib.crc32(data_bytes) & 0xFFFF

def make_packet(seq_num, message):
    # Pack sequence number + message bytes + checksum
    payload = struct.pack('!I', seq_num) + message.encode('utf-8')
    checksum = calculate_checksum(payload)
    return payload + struct.pack('!H', checksum)

def reliable_udp_sender(window_size=5, total_packets=20, timeout=2):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('localhost', 12345)

    base = 0                # base of the sending window (lowest unacked packet)
    next_seq_num = 0        # next sequence number to send
    packets = []            # store packets for retransmission
    timer_start = None      # to track timeout

    # Prepare all packets in advance
    for i in range(total_packets):
        msg = f"Message {i}"
        pkt = make_packet(i, msg)
        packets.append(pkt)

    client_socket.settimeout(0.1)  # non-blocking short timeout for ACKs

    print("Starting reliable UDP sender with Go-Back-N...")

    while base < total_packets:
        # Send packets in window
        while next_seq_num < base + window_size and next_seq_num < total_packets:
            client_socket.sendto(packets[next_seq_num], server_address)
            print(f"Sent packet {next_seq_num}")
            if base == next_seq_num:
                timer_start = time.time()
            next_seq_num += 1

        # Wait for ACKs and handle timeout
        try:
            ack_packet, _ = client_socket.recvfrom(4096)
            ack_seq = struct.unpack('!I', ack_packet[:4])[0]
            print(f"Received ACK for packet {ack_seq}")

            if ack_seq >= base:
                base = ack_seq + 1
                timer_start = time.time()

        except socket.timeout:
            # Check timeout to retransmit
            if timer_start and (time.time() - timer_start) > timeout:
                print(f"Timeout! Retransmitting packets from {base} to {next_seq_num - 1}")
                for i in range(base, next_seq_num):
                    client_socket.sendto(packets[i], server_address)
                    print(f"Retransmitted packet {i}")
                timer_start = time.time()

    print("All packets sent and acknowledged.")
    client_socket.close()

if __name__ == '__main__':
    reliable_udp_sender(window_size=5, total_packets=20)
