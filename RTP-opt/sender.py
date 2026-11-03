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

    # Tao socket UDP de truyen goi tin
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:

        start_header = PacketHeader(type=0, seq_num=0, length=0)
        start_header.checksum = compute_checksum(start_header)
        s.sendto(bytes(start_header), (receiver_ip, receiver_port))

        s.settimeout(3.0)

        # Cho ACK hop le cho goi START
        while True:
            ack_data, address = s.recvfrom(2048)

            if len(ack_data) != 16:
                continue

            ack_header = PacketHeader(ack_data)
            received_checksum = ack_header.checksum

            ack_header.checksum = 0
            if compute_checksum(ack_header) != received_checksum:
                continue

            if (
                ack_header.type == 3
                and ack_header.seq_num == 1
                and ack_header.length == 0
            ):
                break

        import time

        if window_size < 1:
            raise ValueError("window_size must be positive")

        # Sender sliding window
        base = 1
        next_seq = 1
        total_packets = len(data_packets)
        timer_start = None
        acked_packets = set()

        while base <= total_packets:
            sent_new = False
            # Gui cac goi tin khi cua so con cho
            while (
                next_seq <= total_packets
                and next_seq < base + window_size
            ):
                packet = data_packets[next_seq - 1]
                s.sendto(packet, (receiver_ip, receiver_port))
                next_seq += 1
                sent_new = True

            if sent_new and timer_start is None:
                timer_start = time.monotonic()

            remaining = 0.5 - (time.monotonic() - timer_start)

            # Truyen lai cac DATA chua duoc ACK khi het 500 ms
            if remaining <= 0:
                for seq in range(base, next_seq):
                    s.sendto(
                        data_packets[seq - 1],
                        (receiver_ip, receiver_port)
                    )

                timer_start = time.monotonic()
                continue

            s.settimeout(remaining)

            # Cho ACK tu receiver
            try:
                ack_data, address = s.recvfrom(2048)
            except socket.timeout:
                continue

            # Bo qua packet khong dung kich thuoc ACK
            if len(ack_data) != 16:
                continue

            # Doc va kiem tra checksum cua ACK
            ack_header = PacketHeader(ack_data)
            received_checksum = ack_header.checksum
            ack_header.checksum = 0

            if compute_checksum(ack_header) != received_checksum:
                continue

            if ack_header.type != 3 or ack_header.length != 0:
                continue

            # Xu ly ACK rieng cho tung DATA
            ack_num = ack_header.seq_num

            if base <= ack_num < next_seq and ack_num <= total_packets:
                acked_packets.add(ack_num)
                old_base = base

                while base in acked_packets:
                    acked_packets.remove(base)
                    base += 1

                if base > old_base:
                    if base < next_seq:
                        timer_start = time.monotonic()
                    else:
                        timer_start = None


        # Tao goi END
        end_seq = total_packets + 1
        end_header = PacketHeader(type=1, seq_num=end_seq, length=0)

        # Tinh checksum va gui goi END
        end_header.checksum = compute_checksum(end_header)
        s.sendto(bytes(end_header), (receiver_ip, receiver_port))

        end_deadline = time.monotonic() + 0.5

        while True:
            remaining = end_deadline - time.monotonic()

            if remaining <= 0:
                break

            s.settimeout(remaining)

            try:
                ack_data, address = s.recvfrom(2048)
            except socket.timeout:
                break

            if len(ack_data) != 16:
                continue

            # Doc va kiem tra checksum cua ACK
            ack_header = PacketHeader(ack_data)
            saved_checksum = ack_header.checksum
            ack_header.checksum = 0

            if compute_checksum(ack_header) != saved_checksum:
                continue

            if (
                ack_header.type == 3
                and ack_header.length == 0
                and ack_header.seq_num == end_seq + 1
            ):
                break

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
