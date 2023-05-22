import socket
import argparse

parser = argparse.ArgumentParser(description="A UDP file sender")
parser.add_argument("-p", "--port", dest="port", type=int, default=12345,
                    help="TCP port the server is listening on (default 12345)")
parser.add_argument("-f", "--filename", dest="file_name",
                    help="name of file to write to")
args = parser.parse_args()

UDP_IP = ''                 # IP address and port to listen on
UDP_PORT = args.port
file_name = args.file_name  # Name of file to write to
packet_size = 1450          # Size of payload in each packet
header_size = 13            # Size of packet header
prev_packet = 0             # Stores ID of the previous packet
first_packet = True         # Flag indicating the first packet received

# Create socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# Open the file to write bytes
file = open(file_name, 'wb')

while True:
    # Receive data from the socket
    data, addr = sock.recvfrom(packet_size + header_size)

    if data:
        # Extract header information from packet
        conn_id = data[0:4]
        num_bytes = data[4:8]
        packet_number = int.from_bytes(data[8:12], 'big')
        is_acked = data[12]

        print("packet received")
        print("Connection id: ", conn_id.hex())
        print("Packet number: ", packet_number, "\n")

        # If it is the first packet received
        if first_packet:
            prev_packet = packet_number
            first_packet = False
            ack = conn_id + packet_number.to_bytes(4, 'big')
            sock.sendto(ack, addr)
            file.write(data[13:])
        # If it is a duplicate of an old packet
        elif packet_number <= prev_packet:
            # and the sender has requested an ack
            if is_acked:
                ack = conn_id + packet_number.to_bytes(4, 'big')
                sock.sendto(ack, addr)
            # if the sender has not requested an ack, drop the packet
            else:
                continue
        # If it is a future packet, drop the packet
        elif packet_number > prev_packet + 1:
            continue
        # If it is an expected packet, write data to the file
        else:
            file.write(data[13:])
            prev_packet = packet_number
            # If it is marked to be acked, ack it
            if is_acked:
                ack = conn_id + packet_number.to_bytes(4, 'big')
                sock.sendto(ack, addr)

        # If it is the last packet
        if len(data) != (packet_size + header_size):
            break
sock.close()
file.close()