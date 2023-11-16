import datetime as dt
import socket
import sys
import select

# Language month dictionaries
english = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}

maori = {
    1: "Kohitātea",
    2: "Hui-tanguru",
    3: "Poutū-te-rangi",
    4: "Paenga-whāwhā",
    5: "Haratua",
    6: "Pipiri",
    7: "Hōngongoi",
    8: "Here-turi-kōkā",
    9: "Mahuru",
    10: "Whiringa-ā-nuku",
    11: "Whiringa-ā-rangi",
    12: "Hakihea",
}

german = {
    1: "Januar",
    2: "Februar",
    3: "Marz",
    4: "April",
    5: "Mai",
    6: "Juni",
    7: "Juli",
    8: "August",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Dezember",
}


def input_check(port1, port2, port3):
    input_ports = [port1, port2, port3]

    # Checks if port numbers are in the correct range
    for port in input_ports:
        if not 1024 <= port <= 64000:
            print("error - all ports must be within 1024-64000!")
            sys.exit()

    # Checks that all 3 port numbers are unique
    if len(set(input_ports)) != 3:
        print("error - all ports must be unique")
        sys.exit()


def dt_request_check(array):
    # Packet Length
    if len(array) != 6:
        print("error - Packet does not contain exactly 6 bytes!")
        return False

    # MagicNo
    if array[0] << 8 | array[1] != 0x497E:
        print("error - MagicNo field doesn't contain 0x497E!")
        return False

    # PacketType
    if array[2] << 8 | array[3] != 0x0001:
        print("error - PacketType field doesn't contain 0x0001!")
        return False

    # RequestType
    if array[4] << 8 | array[5] != 0x0001 and array[4] << 8 | array[5] != 0x0002:
        print("error - RequestType field doesn't contain 0x0001 or 0x0002!")
        return False

    return True


def prepare_response_packet(socket, request, socket1, socket2, socket3):
    # Current date/time
    now = dt.datetime.now()
    year = now.year
    month = now.month
    day = now.day
    hour = now.hour
    minute = now.minute
    date = now.strftime("%d, %Y")
    time = now.strftime("%H:%M")

    # Sets the text
    if socket == socket1:
        if request == "date":
            text = f"Today's date is {english[month]} {date}"
        elif request == "time":
            text = f"The current time is {time}"
    elif socket == socket2:
        if request == "date":
            text = f"Ko te ra o tenei ra ko {maori[month]} {date}"
        else:
            text = f"Ko te wa o tenei wa {time}"
    elif socket == socket3:
        if request == "date":
            text = f"Heunte ist der {day}. {german[month]} {year}"
        else:
            text = f"Die Uhrzeit ist {time}"

    # Encodes the text
    message = text.encode("utf-8")

    # Checks message length
    message_length = len(message)

    if message_length > 255:
        print("error - length of message greater than 255!")
        return False

    # Forms DT Response Packet
    byte_array_length = 13 + message_length

    array = bytearray(byte_array_length)

    # MagicNo
    array[0] = 0x49
    array[1] = 0x7E
    # PacketType
    array[2] = 0x00
    array[3] = 0x02
    # LanguageCode
    array[4] = 0x00
    if socket == socket1:
        array[5] = 0x01
    if socket == socket2:
        array[5] = 0x02
    if socket == socket3:
        array[5] = 0x03
    # Year
    array[6] = year >> 8
    array[7] = year & 0x00FF
    # Month
    array[8] = month
    # Day
    array[9] = day
    # Hour
    array[10] = hour
    # Minute
    array[11] = minute
    # Length
    array[12] = message_length

    # Adds the encoded text to the text fields of the bytearray
    i = 13
    for byte in message:
        array[i] = byte
        i += 1

    return array


def main():
    # Checks to see if 3 numbers were entered as parameters
    if (len(sys.argv) - 1) != 3:
        print("error - three port numbers must be passed through!")
        sys.exit()

    # Set parameters to ports
    try:
        port1 = int(sys.argv[1])
        port2 = int(sys.argv[2])
        port3 = int(sys.argv[3])
    except:
        print("error - port numbers couldn't be set from parameters!")
        sys.exit()

    # Check input was valid
    input_check(port1, port2, port3)

    # INADDR_ANY
    server = ""

    # Sets the address of the three sockets
    addr1 = (server, port1)
    addr2 = (server, port2)
    addr3 = (server, port3)

    # Attempts to open three UDP sockets
    try:
        sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock1.bind(addr1)
        sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock2.bind(addr2)
        sock3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock3.bind(addr3)
    except Exception:
        print("error - failure while opening sockets!")
        sys.exit()

    while True:
        readable, writeable, exceptional = select.select(
            [sock1, sock2, sock3], [], [sock1, sock2, sock3]
        )

        for s in readable:
            # Receive array from socket, storing bytearray, IP, and port number
            try:
                message, address = s.recvfrom(1024)
                incoming_array = bytearray(message)
                ip = address[0]
                port = address[1]
            except:
                print("error - server encountered an error receiving the message!")
                break

            # Check whether the packet received is valid
            if not dt_request_check(incoming_array):
                break

            # Determine whether date or time is being requested
            if incoming_array[4] << 8 | incoming_array[5] == 0x0001:
                request = "date"
            else:
                request = "time"

            # DT Response Packet returns array or False if the text is too long
            packet = prepare_response_packet(s, request, sock1, sock2, sock3)
            if not packet:
                break

            # Send Response to Client
            addr = (ip, port)
            try:
                s.sendto(packet, addr)
            except:
                print("error - couldn't send response packet back to the client!")
                break


main()
