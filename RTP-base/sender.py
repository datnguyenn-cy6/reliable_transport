import argparse
import socket

from utils import PacketHeader, compute_checksum


def sender(receiver_ip, receiver_port, window_size):
    """TODO: Open socket and send message from sys.stdin."""
    import sys

    # Kich thuoc toi da cua goi RTP
    MAX_PACKET_SIZE = 1472
    HEADER_SIZE = 16
    MAX_PAYLOAD_SIZE = MAX_PACKET_SIZE - HEADER_SIZE

    message = sys.stdin.buffer.read()
    data_packets = []

    # Chia du lieu thanh cac chunks
    for offset in range(0, len(message), MAX_PAYLOAD_SIZE):
        chunk = message[offset:offset + MAX_PAYLOAD_SIZE]

        seq_num = len(data_packets) + 1

        # RTP header
        header = PacketHeader(
            type=2,
            seq_num=seq_num,
            length=len(chunk)
        )

        # Tinh checksum
        header.checksum = compute_checksum(header / chunk)

        packet = bytes(header / chunk)
        data_packets.append(packet)

    return data_packets

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "receiver_ip", help="The IP address of the host that receiver is running on"
    )
    parser.add_argument(
        "receiver_port", type=int, help="The port number on which receiver is listening"
    )
    parser.add_argument(
        "window_size", type=int, help="Maximum number of outstanding packets"
    )
    args = parser.parse_args()

    sender(args.receiver_ip, args.receiver_port, args.window_size)


if __name__ == "__main__":
    main()
