# Small Nexus Keycode Protocol Credit Keycode Generator
# Convenience script to generate keycodes 'on the fly' for testing/QA purposes.

import argparse
import nexus_keycode.protocols.small as protocol

if __name__ == "__main__":

    def check_message_type(message_type):
        valid_message_types = ['SET', 'UNLOCK', 'ADD']
        if not isinstance(message_type, basestring) or str(message_type) not in valid_message_types:
            raise argparse.ArgumentTypeError("'{}' is not in {}".format(message_type, valid_message_types))
        return str(message_type)

    def check_secret_key(secret_key):
        try:
            int(secret_key, 16)
        except ValueError:
            raise argparse.ArgumentTypeError("'{}' contains characters that are not valid hexadecimal values (a-f, 0-9)".format(secret_key))

        if len(secret_key) != 32:
            raise argparse.ArgumentTypeError("'{}' is not a 16-byte secret key (must be 32 hex characters)".format(secret_key))

        return secret_key.decode("hex")

    argparser = argparse.ArgumentParser(description="Generate credit keycodes for Nexus Keycode 'small' protocol.", epilog="python generate_small_keycode.py -t ADD -i 0 -k abcdef0011223344556677889900ffee -d 30")

    # Note: 'UNLOCK' is implemented as a special case of "ADD", but for the purposes of this tool they are considered separate 'types'.
    argparser.add_argument("-t", "--message_type", required=True, type=check_message_type, help="Credit keycode type. Valid options are: 'SET', 'ADD', 'UNLOCK'")
    argparser.add_argument("-i", "--message_id", required=True, type=int, help="Keycode Message ID (e.g. 0, 1, 2, 3...)")
    argparser.add_argument("-k", "--secret_key", required=True, type=check_secret_key, help="Hex-encoded 16-byte secret key, 32 characters long (e.g. 'abcdef0011223344556677889900ffee'")
    argparser.add_argument("-d", "--days", required=True, type=int, help="Days of credit. Ignored for 'UNLOCK'")

    # message_type, message_id, secret_key, days
    args = argparser.parse_args()

    msg_type = args.message_type
    msg_id = args.message_id
    key = args.secret_key
    days = args.days

    if msg_type == "SET":
        msg = protocol.SetCreditSmallMessage(msg_id, days, key)
    elif msg_type == "ADD":
        msg = protocol.AddCreditSmallMessage(msg_id, days, key)

    else:
        assert msg_type == "UNLOCK"
        msg = protocol.AddCreditSmallMessage(msg_id, protocol.SmallMessage.UNLOCK_FLAG, key)

    print msg
