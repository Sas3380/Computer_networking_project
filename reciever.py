import socket                 
import struct #for packing/unpacking binary data
import random               

receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiver_address = ('localhost', 12345)                            
receiver_socket.bind(receiver_address)                           

expected_seq_num = 0  # initialize expected sequence number to 0 for in-order delivery

def simulate_packet_loss():
    return random.random() > 0.1  # 90% chance to process the packet


def main():
    global expected_seq_num   
    
    while True:           
        packet, addr = receiver_socket.recvfrom(4096) 

        if simulate_packet_loss(): #only process packet if "not lost", randomly here

            seq_num = struct.unpack('!I', packet[:4])[0] 
            data = packet[4:].decode('utf-8') 

            if seq_num == expected_seq_num:                # if packet is the expected one
                print(f"Received expected packet: {data} with seq {seq_num}")
                expected_seq_num += 1                       # increment for next packet
            else:
                print(f"Received out-of-order packet: seq {seq_num} (expected {expected_seq_num})")
                # do nothing else — packet is discarded by ignoring it

            # send ACK for the last correctly received in-order packet (expected_seq_num - 1)
            ack_packet = struct.pack('!I', expected_seq_num - 1)  
            receiver_socket.sendto(ack_packet, addr)       # send ACK back to sender's address
            print(f"Sent ACK for sequence number {expected_seq_num - 1}")

        else:
            print("Packet lost. No ACK sent.")# simulate loss by not sending ACK

if __name__ == '__main__':
    main()  # run the main function when script is executed
