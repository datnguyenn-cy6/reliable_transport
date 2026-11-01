import argparse
import socket

from utils import PacketHeader, compute_checksum


def receiver(receiver_ip, receiver_port, window_size):
    """TODO: Listen on socket and print received message to sys.stdout."""

    # Tao socket UDP va lang nghe tren dia chi duoc chi dinh
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((receiver_ip, receiver_port))

        # Trang thai ket noi
        started = False
        sender_address = None

        while True:
            packet, address = s.recvfrom(2048)

            if not 16 <= len(packet) <= 1472:
                continue

            # Tach header va payload
            header = PacketHeader(packet[:16])
            payload = packet[16:]

            if header.length != len(payload):
                continue

            # Kiem tra checksum
            saved_checksum = header.checksum
            header.checksum = 0

            if compute_checksum(header / payload) != saved_checksum:
                continue

            # Xu ly START khi chua co ket noi
            if not started:
                if (
                    header.type != 0
                    or header.seq_num != 0
                    or header.length != 0
                ):
                    continue

                started = True
                sender_address = address

                ack = PacketHeader(type=3, seq_num=1, length=0)
                ack.checksum = compute_checksum(ack)

                s.sendto(bytes(ack), sender_address)
                continue

            if address != sender_address:
                continue

            if header.type == 0:
                continue

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

    receiver(args.receiver_ip, args.receiver_port, args.window_size)


if __name__ == "__main__":
    main()
