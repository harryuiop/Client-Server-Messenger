# Harry Ellis - 81186884 - HEL46

from sys import exit, argv
from socket import *

# Constants
MAGIC_NUMBER = 0xAE73
IDENTITY_CREATE = 2
IDENTITY_READ = 1

# Dictionary to store messages based on receivers
memory = {}

def check_incoming_request_validity(message):
    """
    Validates the incoming message for correctness
    """

    # Extract message data
    name, receiver, text, magic_number, identity = extract_message_data(message)

    # Check magic number
    if magic_number != MAGIC_NUMBER:
        print("Magic Number Incorrect")
        return True
    
    # Check identity
    if identity not in [IDENTITY_READ, IDENTITY_CREATE]:
        print("Invalid Identity")
        return True
    
    # Check name length
    if len(name) < 1:
        print("Length of name not acceptable")
        return True
    
    # Check receiver for create requests
    if identity == IDENTITY_CREATE and len(receiver) < 1:
        print("Receiver not specified for create")
        return True
    
    # Check message text for read requests
    if identity == IDENTITY_READ and len(text) != 0:
        print("No messages required for read")
        return True
    
    # Check message text for create requests
    if identity == IDENTITY_CREATE and len(text) < 1:
        print("Message required for create")
        return True
    
    return False


def update_memory(message_data):
    """
    Updates the memory with new messages.
    """ 

    # Check if receiver is already in memory, then we append to their key.
    if message_data[2] in memory:

        # Check to see if their inbox is full (255 messages)
        # To adjust the capacity of all individuals inbox, simply just change the number below
        if len(memory[message_data[2]]) < 255:
            memory[message_data[2]].append((message_data[0], message_data[1]))

        else:
            if memory[message_data[2]][-1][1] != "Inbox Full":
                memory[message_data[2]].append(("From Server", "Inbox Full"))

    # Otherwise we create a new Key for them
    else:
        memory[message_data[2]] = [(message_data[0], message_data[1])]


def extract_message_data(message):
    """
    Extracts information from the received message.
    """

    magic_number = (message[0] << 8) | (message[1])
    identitiy = message[2]
    name_length = message[3]
    receiver_length = message[4]
    
    name = message[7:7 + name_length]
    decoded_name = name.decode('utf-8')
    
    text = message[7 + name_length + receiver_length::]
    decoded_text = text.decode('utf-8')
    
    receiver = message[7 + name_length:7 + name_length + receiver_length]
    decoded_receiver = receiver.decode('utf-8')
    
    return decoded_name, decoded_text, decoded_receiver, magic_number, identitiy


def handle_create_request(message, conn):
    """
    Handles the processing of a "create" request message.
    """

    # Check Validity
    errors_detected = check_incoming_request_validity(message)
    if errors_detected == True:
        response_text = (f'Invalid create packet').encode("UTF-8")
        conn.send(response_text)
        return 

    # Extract message data
    message_data = extract_message_data(message)
    
    update_memory(message_data)

    
    # Prepare response message
    response_text = (f'Thanks {message_data[0]}, the server has saved your message for {message_data[2]} saying "{message_data[1]}"')
    response = response_text.encode("UTF-8")
    
    # Send response back to the client
    conn.send(response)


def handle_read_request(message, conn):
    """
    Handles the processing of a "read" request message.
    """

    # Check Validity
    errors_detected = check_incoming_request_validity(message)
    if errors_detected == True:
        print("Invalid read packet")

    # Build the response packet for read requests
    read_packet = build_read_packet(message)

    # If there are no messages to send, print a message and return
    if read_packet is None:
        print(f'There are no messages for {extract_message_data(message)[1]}')
        return
    
    # Send the read response packet back to the client
    conn.send(read_packet)


def build_read_packet(message):
    """
    Creates a response packet for read requests.
    """

    extract = extract_message_data(message)
    while True:
        if memory.get(extract[1]) is not None:
            message_list = memory.get(extract[1])

            # Checks for MoreMsgs
            more_msgs = 0
            if len(memory.get(extract[1])) > 255:
                pass
            
            # Create the initial response packet
            message_request = bytearray([
                (0xAE73 >> 8), (0xAE73 & 0xff),     # Magic Number (2 Bytes)
                3,                                  # ID (1 Byte)
                len(message_list),                  # NumItems (1 Byte)
                more_msgs                           # MoreMsgs (1 Byte)
            ])
            for msg in message_list:
                sender, message_recv = msg
                message_recv_len = len(message_recv)
                sender_encoded = sender.encode("UTF-8")
                message_recv_encoded = message_recv.encode("UTF-8")
                            
                # Extend the response packet
                message_request.extend(bytearray([
                    len(sender),
                    (message_recv_len >> 8), (message_recv_len & 0xff)
                ]))
                
                message_request.extend(sender_encoded)
                message_request.extend(message_recv_encoded)

            del memory[extract[1]]
            return message_request

        else:
            return


def main():
    """
    The main server function that listens for incoming connections and processes messages.
    """
    # Socket and Connection
    sock = None
    conn = None

    try:
        if len(argv) != 2:
            print(f"Usage:\n\n\tpython(3) {argv[0]} <port>\n")
            exit()

        port = int(argv[1])
        sock = socket(AF_INET, SOCK_STREAM)
        sock.bind(("0.0.0.0", port))
        sock.listen(5)
        
        while True:
            conn, client = sock.accept()
            print(f'{client[0]} has connected on port {client[1]}')
            
            # Receive the message
            message = conn.recv(256)

            if message[2] == 2:  # ID == Read
                handle_create_request(message, conn)

            elif message[2] == 1:  # ID == Create
                handle_read_request(message, conn)

                    
    except ValueError:  # Port int conversion
        print(f"ERROR: Port '{argv[1]}' is not an integer")

    except UnicodeDecodeError:  # Message decode
        print("ERROR: Decoding/encoding failure")

    except OSError as err:  # Raised by all socket methods
        print(f"ERROR: {err}")  # Print the error string

    except KeyboardInterrupt:
        print(f'Keyboard Interupt')


    finally:  # Close the sockets
        if sock is not None:
            sock.close()

        if conn is not None:
            conn.close()

# Call the main function to start the server
main()
