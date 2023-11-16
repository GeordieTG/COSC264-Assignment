import socket
import sys
import select


def valid_ip(address, port):
    # Gets IP address from input, returns error if input is invalid
    try:
        result = socket.getaddrinfo(address, port)
        ip = result[0][4][0]
    except:
        print("error - invalid ip address/hostname")
        sys.exit()

    return ip


def input_check(request, input_ip, port):
    # Checks to see if the type was valid
    if request != "date" and request != "time":
        print("error - type must be either 'date' or 'time'!")
        sys.exit()

    # Checks to see if IP was given correctly
    ip = valid_ip(input_ip, port)

    # Checks if port number is in correct range
    if port < 1024 or port > 64000:
        print("error - port number must be between 1024 and 64000!")
        sys.exit()

    return ip


def prepare_request_packet(request):
    array = bytearray(6)

    # Magic No
    array[0] = 0x49
    array[1] = 0x7E
    # Packet Type
    array[2] = 0x00
    array[3] = 0x01
    # Request Type
    array[4] = 0x00

    if request == "date":
        array[5] = 0x01
    else:
        array[5] = 0x02

    return array


def dt_response_check(array):
    if len(array) < 13:
        print("error - response packet not correct length!")
        sys.exit()

    if array[0] << 8 | array[1] != 0x497E:
        print("error - MagicNo field not correct!")
        sys.exit()

    if array[2] << 8 | array[3] != 0x0002:
        print("error - PacketType field not correct!")
        sys.exit()

    if (array[4] << 8 | array[5]) not in [0x0001, 0x0002, 0x0003]:
        print("error - LanguageCode field not correct!")
        sys.exit()

    if array[6] << 8 | array[7] >= 2100:
        print("error - Year field not below 2100!")
        sys.exit()

    if array[8] not in range(1, 13):
        print("error - Month field not in range 1-12!")
        sys.exit()

    if array[9] not in range(1, 32):
        print("error - Day field not in range 1-31!")
        sys.exit()

    if array[10] not in range(0, 24):
        print("error - Hour field not in range 0-23!")
        sys.exit()

    if array[11] not in range(0, 60):
        print("error - Minute field not in range 0-59!")
        sys.exit()

    if len(array) != (13 + array[12]):
        print("error - Length of packet doesn't equal 13 + Length Field!")
        sys.exit()


def print_dt_response_packet(array):
    print(f"[MAGIC NO] {array[0] << 8 | array[1]}")
    print(f"[PACKET TYPE] {array[2] << 8 | array[3]}")
    print(f"[LANGUAGE CODE] {(array[4] << 8 | array[5])}")
    print(f"[YEAR] {array[6] << 8 | array[7]}")
    print(f"[MONTH] {array[8]}")
    print(f"[DAY] {array[9]}")
    print(f"[HOUR] {array[10]}")
    print(f"[MINUTE] {array[11]}")
    print(f"[LENGTH] {array[12]}")
    print(array[13:].decode("utf-8"))


def main():
    # Checks to see if 3 parameters were entered
    if (len(sys.argv) - 1) != 3:
        print("error - three port numbers must be passed through!")
        sys.exit()

    # Initial Input
    try:
        request = sys.argv[1]
        input_ip = sys.argv[2]
        port = int(sys.argv[3])
    except:
        print("error - were your parameters entered correctly?")
        sys.exit()

    # Checks to see if input is valid and returns IP address
    ip = input_check(request, input_ip, port)

    # Open UDP socket
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except:
        print("error - failure while opening socket!")
        sys.exit()

    # DT Request Packet
    request_packet = prepare_request_packet(request)

    # Send Request Packet to Server
    addr = (ip, port)

    try:
        client.sendto(request_packet, addr)
    except:
        print("error - couldn't send to server!")
        sys.exit()

    # Select method to exit if the client doesn't receive a response in one second
    readable, writeable, exceptional = select.select([client], [], [client], 1)

    if readable:
        # Receive Response Packet from Server
        try:
            message, address = client.recvfrom(1024)
        except:
            print("error - couldn't receive from server!")
            sys.exit()

        incoming_array = bytearray(message)

        # DT Response Check
        dt_response_check(incoming_array)

        # Print DT Response Packet
        print_dt_response_packet(incoming_array)
        sys.exit()
    else:
        print("error - client didn't receive a response and timed out!")
        sys.exit()


main()
