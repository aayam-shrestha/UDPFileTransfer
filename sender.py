import socket
import argparse
import os

parser = argparse.ArgumentParser(description="A UDP file sender")
parser.add_argument("-s", "--server", dest="server", default="127.0.0.1",
                    help="server hostname or IP address (default: 127.0.0.1)")
parser.add_argument("-p", "--port", dest="port", type=int, default=12345,
                    help="TCP port the server is listening on (default 12345)")
parser.add_argument("-f", "--filename", dest="file_name",
                    help="name of file to transfer")
args = parser.parse_args()

UDP_IP = args.server        # IP address and Port number of the receiver
UDP_PORT = args.port
file_name = args.file_name  # File name as command line argument
packet_size = 1450          # Size of payload in each packet that is sent
ack_size = 8                # Size of received acks
header_size = 13            # Size of packet header
packet_number = 0           # Packet ID
gap = 0                     # Gap between acked packets - incremented after each ack
gap_counter = 0             # Tracks number of packets sent after the last ack
is_acked = 1                # Indicates if packet needs to be acked by the receiver
ack_packet_num = 0          # ID of the received acked packet
last_ack_counter = 0        # Number of timeouts while waiting for last packet to be acked
file_size = os.path.getsize(file_name)      # Size of file being transferred
num_bytes = file_size.to_bytes(4, 'big')    # Size of file in bytes

# Create socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Connection times out if no response is received in 1 second
sock.settimeout(1)

# Generating a random ID for the connection
conn_id = os.urandom(4)

# Opening the file to read bytes
file = open(file_name, 'rb')
data = file.read(packet_size)

print(f"UDP target IP: {UDP_IP}")
print(f"UDP target port: {UDP_PORT}")
print(f"Sending {file_name}...")

while True:
    while data:
        # If no data is read from the file, exit the loop
        if len(data) == 0:
            break
        # If the gap after the last ack is reached or the last packet is reached, ack the packet
        if (gap_counter == gap) or (len(data) != packet_size):
            is_acked = 1
        else:
            is_acked = 0

        # Create header by concatenating the connection ID, the total number of bytes, the packet number, and the ack flag
        header = conn_id + num_bytes + \
            packet_number.to_bytes(4, 'big') + is_acked.to_bytes(1, 'big')

        # Send the header and payload to the destination
        sock.sendto(header + data, (UDP_IP, UDP_PORT))
        # print(f"Sending packet {packet_number}")

        # Read new bytes from the file
        data = file.read(packet_size)

        # if the packet was marked to be acked
        if is_acked:
            try:
                ack, addr = sock.recvfrom(ack_size)
                ack_packet_num = int.from_bytes(ack[4:8], 'big')
                print("ACK received")
                print("Connection ID: ", ack[0:4].hex())
                print("Packet number: ", ack_packet_num, "\n")
                # if the packet was successfully acked, increase gap and reset the gap counter
                gap += 1
                gap_counter = 1
                packet_number += 1
                break
            # if ack isn't received
            except socket.timeout:
                if len(data) == 0:
                    break
                elif len(data) != packet_size:
                    last_ack_counter += 1
                print("Connection timed out")
                print(f"Resending packet number {ack_packet_num + 1}...\n")
                # move file pointer to the position of the last acked packet
                file.seek(packet_size * ack_packet_num, 0)
                # change packet number to the one after the last acked packet
                packet_number = ack_packet_num + 1
                # set flag for dropped packet to true
                packet_dropped = True
                # reset the gap
                gap = 0
                gap_counter = 0
                break
        # if the packet was not marked to be acked
        else:
            gap_counter += 1
            packet_number += 1
    if len(data) == 0:
        break
    if last_ack_counter == 6:
        print("File transfer success unknown")
        break
sock.close()
file.close()
