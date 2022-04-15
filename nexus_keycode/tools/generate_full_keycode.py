# Full Nexus Keycode Protocol Keycode Generator
# Convenience script to generate keycodes 'on the fly' for testing/QA purposes.

import argparse
import codecs

import nexus_keycode.protocols.full as protocol
from nexus_keycode.protocols.channel_origin_commands import ChannelOriginAction

VALID_NXK_MESSAGE_TYPES = ["SET", "UNLOCK", "ADD"]
VALID_NXC_MESSAGE_TYPES = ["LINK", "UNLINK"]


def create_full_credit_message(msg_id, msg_type, secret_key, hours=None):

    if msg_type not in VALID_NXK_MESSAGE_TYPES:
        raise ValueError(
            u"Invalid message type, supported values are {}".format(
                VALID_NXK_MESSAGE_TYPES
            )
        )

    if msg_type == "UNLOCK":
        return protocol.FullMessage.unlock(msg_id, secret_key)

    if hours is None:
        raise ValueError(
            u"Expected non-null `hours` argument for message type {}".format(msg_type)
        )

    if msg_type == "ADD":
        return protocol.FullMessage.add_credit(msg_id, hours, secret_key)
    else:
        assert msg_type == "SET"
        return protocol.FullMessage.set_credit(msg_id, hours, secret_key)


def create_full_channel_message(
    msg_type,
    controller_sym_key,
    controller_command_count,
    accessory_sym_key=None,
    accessory_command_count=None,
):

    if msg_type not in VALID_NXC_MESSAGE_TYPES:
        raise ValueError(
            u"Invalid message type, supported values are {}".format(
                VALID_NXC_MESSAGE_TYPES
            )
        )

    if msg_type == "UNLINK":
        return protocol.FactoryFullMessage.passthrough_channel_origin_command(
            ChannelOriginAction.UNLINK_ALL_ACCESSORIES,
            controller_sym_key=controller_sym_key,
            controller_command_count=controller_command_count,
        )
    else:
        assert msg_type == "LINK"
        if accessory_sym_key is None or accessory_command_count is None:
            raise ValueError(
                u"Expected non-null accessory symmetric key and command count!"
            )

        return protocol.FactoryFullMessage.passthrough_channel_origin_command(
            ChannelOriginAction.LINK_ACCESSORY_MODE_3,
            controller_sym_key=controller_sym_key,
            controller_command_count=controller_command_count,
            accessory_sym_key=accessory_sym_key,
            accessory_command_count=accessory_command_count,
        )


if __name__ == "__main__":

    def check_message_type(message_type):
        VALID_MESSAGE_TYPES_ALL = VALID_NXK_MESSAGE_TYPES + VALID_NXC_MESSAGE_TYPES
        if (
            not isinstance(message_type, str)
            or str(message_type) not in VALID_MESSAGE_TYPES_ALL
        ):
            raise argparse.ArgumentTypeError(
                u"'{}' is not in {}".format(message_type, VALID_MESSAGE_TYPES_ALL)
            )
        return str(message_type)

    def check_secret_key(secret_key):
        try:
            int(secret_key, 16)
        except ValueError:
            raise argparse.ArgumentTypeError(
                u"'{}' contains characters that are not valid hexadecimal values "
                "(a-f, 0-9)".format(secret_key)
            )

        if len(secret_key) != 32:
            raise argparse.ArgumentTypeError(
                u"'{}' is not a 16-byte secret key (must be 32 hex characters)".format(
                    secret_key
                )
            )

        decode_hex = codecs.getdecoder("hex_codec")
        return decode_hex(secret_key)[0]

    argparser = argparse.ArgumentParser(
        description="Generate credit or Channel keycodes for Nexus Keycode 'full' protocol.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="python generate_full_keycode.py -t ADD -i 0 -k abcdef0011223344556677889900ffee -hr 30\n"
        "python generate_full_keycode.py -t LINK -ck abcdef0011223344556677889900ffee -cc 15 -ak aabbccddeeff11223344556677889900 -ac 3",
    )

    # Note: 'UNLOCK' is implemented as a special case of "SET", but for the purposes of this tool they are considered separate 'types'.
    argparser.add_argument(
        "-t",
        "--message_type",
        required=True,
        type=check_message_type,
        help="Keycode type. Valid options are: 'SET', 'ADD', 'UNLOCK', 'LINK', and 'UNLINK'",
    )
    argparser.add_argument(
        "-i",
        "--message_id",
        required=False,
        type=int,
        help="Keycode Message ID (e.g. 0, 1, 2, 3...)",
    )
    argparser.add_argument(
        "-k",
        "--secret_key",
        required=False,
        type=check_secret_key,
        help="Hex-encoded 16-byte symmetric key for Nexus Keycode, 32 characters long (e.g. 'abcdef0011223344556677889900ffee')",
    )
    argparser.add_argument(
        "-hr", "--hours", required=False, type=int, help="Hours of credit."
    )
    argparser.add_argument(
        "-ck",
        "--controller_key",
        required=False,
        type=check_secret_key,
        help="Hex-encoded 16-byte Nexus Channel Controller symmetric key, 32 characters long (e.g. 'abcdef0011223344556677889900ffee')",
    )
    argparser.add_argument(
        "-cc",
        "--controller_count",
        required=False,
        type=int,
        help="Nexus Channel Controller Command Count",
    )
    argparser.add_argument(
        "-ak",
        "--accessory_key",
        required=False,
        type=check_secret_key,
        help="Hex-encoded 16-byte Nexus Channel Accessory symmetric key, 32 characters long (e.g. 'abcdef0011223344556677889900ffee')",
    )
    argparser.add_argument(
        "-ac",
        "--accessory_count",
        required=False,
        type=int,
        help="Nexus Channel Accessory Command Count",
    )

    args = argparser.parse_args()

    msg_type = args.message_type
    if msg_type in VALID_NXK_MESSAGE_TYPES:
        msg_id = args.message_id
        key = args.secret_key
        hours = args.hours
        msg = create_full_credit_message(msg_id, msg_type, key, hours)

        print(
            (u"{}\n" "Message Type={}\n" "Message ID={}\n" "Message Hours={}\n").format(
                msg.to_keycode(), msg_type, msg_id, hours
            )
        )
    else:
        controller_key = args.controller_key
        controller_count = args.controller_count
        accessory_key = args.accessory_key
        accessory_count = args.accessory_count

        msg = create_full_channel_message(
            msg_type, controller_key, controller_count, accessory_key, accessory_count
        )

        print(
            (
                u"{}\n"
                "Message Type={}\n"
                "Controller Count={}\n"
                "Accessory Count={}\n"
            ).format(msg.to_keycode(), msg_type, controller_count, accessory_count)
        )
