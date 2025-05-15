import socket
import struct
import random
import zlib

def calculate_checksum(data):
    # compute 16-bit checksum using CRC32 and truncate to lower 16 bits
    return zlib.crc32(data) & 0xFFFF

def verify_checksum(packet):
    # separate data and checksum (last 2 bytes)
    data = packet[:-2]
    recv_checksum = struct.unpack('!H', packet[-2:])[0] # it means last 2 bytes
    calc_checksum = calculate_checksum(data)
    return recv_checksum == calc_checksum

def simulate_packet_loss(loss_probability=0.1):
    # simulate 10% loss by returning False
    return random.random() > loss_probability

def reliable_UDP_receiver(window_size=5, enable_packet_loss=True):#by default 5 window size.
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('localhost', 12345))
    print("Receiver started, waiting for packets...")

    expected_seq_num = 0
    last_ack_sent = -1  # To track last ACK sent

    while True:
        packet, client_addr = server_socket.recvfrom(4096)

        if enable_packet_loss and not simulate_packet_loss():
            print("Simulated packet loss. Packet dropped.")
            continue

        # Verify checksum before processing
        if not verify_checksum(packet):
            print("Checksum mismatch. Discarding corrupted packet.")
            # Discard corrupted packet silently (no NAK)
            continue

        # Extract sequence number (4 bytes) and message (rest except checksum)
        seq_num = struct.unpack('!I', packet[:4])[0]
        message_bytes = packet[4:-2]
        message = message_bytes.decode('utf-8')

        # Check if packet is inside the current window
        if expected_seq_num <= seq_num < expected_seq_num + window_size:
            if seq_num == expected_seq_num:
                print(f"Received expected packet {seq_num}: {message}")
                expected_seq_num += 1
                last_ack_sent = seq_num
            else:
                print(f"Received packet {seq_num} inside window but out of order. Ignored.")

            # Send ACK for the last in-order received packet
            ack_packet = struct.pack('!I', last_ack_sent)
            server_socket.sendto(ack_packet, client_addr)
            print(f"Sent ACK for sequence number {last_ack_sent}")

        else:
            # Packet is out of window: discard and resend ACK for last in-order packet
            print(f"Packet {seq_num} out of window. Discarding.")
            ack_packet = struct.pack('!I', last_ack_sent)
            server_socket.sendto(ack_packet, client_addr)
            print(f"Resent ACK for sequence number {last_ack_sent}")

if __name__ == '__main__':
    reliable_udp_receiver(window_size=5, enable_packet_loss=True)
