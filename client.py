# Harry Ellis - 81186884 - HEL46

from sys import exit, argv
from socket import *

sock = None

def errorchecking():
    """
    Performs error checking on command line arguments.
    """
    # Check if the number of command line arguments is not equal to 5
    if len(argv) != 5:
        print(f"Usage:\n\n\tpython(3) {argv[0]} <hostname> <port> <user> <read/create>\n")
        return True

    port = int(argv[2])
    # Check if the port number is outside the range of 1024 to 64000
    if port < 1024 or port > 64000:
        print(f'Your chosen port number was {port}; it must be inside the bounds of 1024 and 64000!')
        return True

    # Calculate the length of the username
    username_length = len(argv[3])
    if not 1 <= username_length <= 255:
        print(f'The length of the username must be between 1 and 255 characters.\nYours was {username_length}!')
        return True

    # Get the operation type (read or create) from the command line
    operation = argv[4]
    if operation != "create" and operation != "read":
        print(f'Please select "read" or "create", not "{operation}"')
        return True

    # If all checks pass, return False to indicate no errors
    return False


def build_create_packet():
    """
    Creates a message packet for the "create" action
    Returns the full message packet
    """
    while True:
        uc_receiver = input("Please enter the name of the receiver: ")
        if 1 <= len(uc_receiver) <= 255:
            receiver = uc_receiver.encode("UTF-8")
            break
        else:
            print("Receiver name must be between 1 and 255 characters")

    while True:
        uc_message = input("Please enter a message to send: ")
        if 1 <= len(uc_message) <= 255:
            message = uc_message.encode("UTF-8")
            break
        else:
            print("Message must be between 1 and 255 characters")

    message_request = bytearray([
        (0xAE73 >> 8), (0xAE73 & 0xff),             # Magic Number (2 Bytes)
        2,                                          # ID (1 Byte)
        len(argv[3]),                               # NameLen (1 Byte)
        len(receiver),                              # ReceiverLen (1 Byte)
        (len(message) >> 8), (len(message) & 0xff)  # MessageLen (2 Bytes)
    ])
    full_packet = message_request + argv[3].encode("UTF-8") + receiver + message
    return full_packet


def build_read_packet():
    """
    Creates a message packet for the "read" action.
    Returns the full message packet
    """
    while True:
        uc_receiver = argv[3]
        if 1 <= len(uc_receiver) <= 255:
            receiver = uc_receiver.encode("UTF-8")
            break
        else:
            print("Receiver name must be between 1 and 255 characters")

    message_request = bytearray([
        (0xAE73 >> 8), (0xAE73 & 0xff),     # Magic Number (2 Bytes)
        1,                                  # ID (1 Byte)
        len(argv[3]),                       # NameLen (1 Byte)
        0,                                  # ReceiverLen (1 Byte)
        (0 >> 8), (0 & 0xff)                # MessageLen (2 Bytes)
        ])
    full_packet = message_request + argv[3].encode("UTF-8") + receiver + "".encode()
    return full_packet


def interpret_return_packet(sock):
    """
    Interprets and processes the returned message for "read" action
    """

    try:
        header = sock.recv(5)

        for _ in range(header[3]):
            message_head = sock.recv(3)
            processed = message_head
            message_len = message_head[2]
            rec_name = (sock.recv(message_head[0])).decode("UTF-8")
            rec_message = (sock.recv(message_len)).decode("UTF-8")

            print(f'{rec_name}: {rec_message}')

    except Exception as e:
        print(f'No messages in storage for {argv[3]}')

    finally:
        sock.close()
        exit()


def main():
    """
    The main client function that takes inputs and sends them to a connected server.
    """
    errors_detected = errorchecking()
    if errors_detected == True:
        exit()

    try:
        # Perform error checking on command line arguments

        sock = None
        port = int(argv[2])  # Convert the port to an integer
        services = getaddrinfo(argv[1], port, AF_INET, SOCK_STREAM)
        family, socktype, proto, canonname, address = services[0]
        sock = socket(AF_INET, SOCK_STREAM)
        sock.connect(address)
        sock.settimeout(1)

        # Determine whether to perform "read" or "create" action
        if argv[4] == "read":
            read_packet = build_read_packet()
            sock.send(read_packet)
            interpret_return_packet(sock)

        elif argv[4] == "create":
            create_packet = build_create_packet()
            sock.send(create_packet)

            # Read and display the response data
            response = sock.recv(256)
            print(response.decode())


    except ValueError:  # Raised by the int() conversion
        print(f"ERROR: Port '{argv[2]}' is not an integer")
    except UnicodeDecodeError:  # Raised by .decode()
        print("ERROR: Response decoding failure")
    except gaierror:  # Raised by address errors such as in getaddrinfo()
        print(f"ERROR: Host '{argv[1]}' does not exist")
    except OSError as err:  # Raised by all socket methods
        print(f"ERROR: {err}")  # Print the error string
    except KeyboardInterrupt:
        print(f'Keyboard Interupt')


    finally:  # Regardless of an exception or not, close the socket
        if sock is not None:
            sock.close()

# Call the main function to start the program
main()
