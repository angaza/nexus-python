import logging

import enum
import math

import bitstring
import siphash
from typing import Optional

from nexus_keycode.protocols.utils import ints_to_bytes, pseudorandom_bits

NEXUS_MODULE_VERSION_STRING = "1.2.0"

logger = logging.getLogger(__name__)


@enum.unique
class SmallMessageType(enum.Enum):
    ADD_CREDIT = 0
    PASSTHROUGH = 1
    SET_CREDIT = 2
    MAINTENANCE_TEST = 3


class SmallMessage(object):
    """Keycode messages for small keypads; immutable.

    All small protocol (except Passthrough) messages follow the following structure:
        * 32-bit message ID
        * 2-bit message type code
        * 8-bit message body
        * 12-bit message authentication code (MAC)

    After compression, the message ID is trimmed to its 6-LSB bits, so the
    compressed/transmitted message size is 28 bits (6+2+8+12).  Receivers of
    a small protocol message must infer/expand the message ID to the 'full' 32
    bit message ID; please see specification document for more details.

    There are four types of small protocol messages, determined by the message
    type code field:
        * Credit messages - message type codes 0, 2
        * Passthrough messages - message type code 1
        * Maintenance/Test messages - message type code 3

    Messages with type codes 0 and 2 (i.e., credit messages) may be applied
    exactly once to a given product over the lifetime of that product.  There
    is no restriction on the number of times Maintenance and Test messages may
    be applied.

    Passthrough messages follow the structure below:
        * 6-bit application data
        * 2-bit message type code (always '0b01')
        * 20-bit application data

    Passthrough messages are obscured in the same way as other 'small' messages
    (to make their structure less obvious when represented as digits), but
    the content of the message is not interpreted or understood by the small
    protocol. Instead, the firmware passes 'passthrough' messages to a handler
    which passes the remaining 26-bits (concatenated) to other application
    specific code for further processing.
    """

    UNLOCK_FLAG = object()

    def __init__(self, id_, message_type, body, secret_key):
        """
        Create a message per the small protocol.  Such messages are
        15 digits long (when represented as decimal). Secret key provided
        must be pseudorandom, the first 16 bytes (if provided key is longer
        than 16 bytes) is used for a hashing operation which requires a key
        of exactly 16 bytes/128-bits.

        :param id_: *Expanded* message ID number for this message (0-4 billion)
        :type id_: `int`
        :param message_type: type code of this message (0-3)
        :type message_type: :class:`SmallMessageType`
        :param body: integer representation of 8-bit body
        :type body: `int`
        :param secret_key: secret hash key (requires 16 bytes, uses first 16)
        :type secret_key: `str`
        """

        if id_ > 4294967295 or id_ < 0:
            raise ValueError("out-of-range credit message ID")
        if message_type not in [e for e in SmallMessageType]:
            raise ValueError("unsupported credit message type code")

        # basic parameters
        self.id_ = id_
        self.message_type = message_type
        self.body = body

        if self.message_type != SmallMessageType.PASSTHROUGH:
            # Siphash requires a 16-byte input key.
            mac_bits = self._generate_mac_bits(secret_key[:16])

            # LSB 6 bits = 0x3F
            compressed_id = self.id_ & 0x3F

            bits = bitstring.pack(
                ["uint:6=message_id", "uint:2=message_type", "uint:8=body"],
                message_id=compressed_id,
                message_type=message_type.value,
                body=body,
            )
            bits.append(mac_bits)
        else:
            # 6-bits opaque data, then 2-bit type ID (passthrough), then
            # 20-bits opaque data. No auth is performed for passthrough messages
            assert secret_key is None
            bits = bitstring.pack(
                ["bits=first_six", "uint:2=message_type", "bits=last_twenty"],
                first_six=self.body[0:6],
                message_type=message_type.value,
                last_twenty=self.body[6:26]
            )

        assert len(bits) == 28
        self.compressed_message_bits = bits

    def __str__(self):
        return self.to_keycode(prefix="1", separator=" ", group_len=3, obscured=True)

    def __repr__(self):
        return "{}({id_!r}, {body!r})".format(self.__class__.__name__, **self.__dict__)

    @classmethod
    def obscure(cls, msg_bits):
        """Obscure a small-protocol message (28 bits).

        Given a unobscured valid small-protocol message, obscure it,
        and return the resulting obscured bits. The purpose of this process
        is to obscure the structure of a given message, which may improve
        perceived security, and to somewhat reduce the occurrence of repeated
        keys, which may reduce entry errors.

        :param msg_bits: 28-bit small protocol message.
        :type msg_bits: :class:`bitstring.BitArray`
        :return: the obscured 28-bit small protocol message
        :rtype: :class:`bitstring.BitArray`
        """

        mac_len = 12  # constant from protocol spec
        body_len = msg_bits.len - mac_len
        mac_bits = msg_bits[-mac_len:]
        prng_bits = pseudorandom_bits(mac_bits, body_len)

        return (msg_bits[:body_len] ^ prng_bits) + mac_bits

    @classmethod
    def deobscure(cls, msg_bits):
        """Deobscure a small-protocol message (28 bits).

        Given an obscured valid small-protocol message, deobscure it.
        The small-protocol obscure is a bitwise operation designed to be
        easily reversible; simply call the same function (obscure) on the
        obscured 28-bit message to get back the original (deobscured)
        message.

        :param msg_bits: 28-bit obscured small protocol message.
        :type msg_bits: :class:`bitstring.BitArray`
        :return: the deobscured 28-bit small protocol message
        :rtype: :class:`bitstring.BitArray`
        """

        return cls.obscure(msg_bits)

    def to_keycode(
        self, prefix="1", separator=" ", group_len=3, key_dict=None, obscured=True
    ):
        """Render this message in keycode form.

        The rendered message can be transferred to a human. For example:

        >>> message = SmallMessage(33, SmallMessageType.ADD_CREDIT, 10, b"\x00" * 16)
        >>> message.to_keycode(prefix="4", separator="-")
        '422-112-100-002-232'

        :param prefix: keycode start character, e.g., "1"
        :type prefix: :class:`str`
        :param separator: inter-group separating character, e.g., "-"
        :type separator: :class:`str`
        :param group_len: number of characters in each separated group
        :type group_len: :class:`int`
        :param key_dict: Four element dict mapping [0,1,2,3] to character keys
        :type key_dict: :class:`dict`
        :param obscured: Obscured true or false
        :type obscured: `bool`
        :return: the rendered keycode string
        :rtype: :class:`str`
        """

        key_dict_confirmed = (
            key_dict if key_dict is not None else {0: "2", 1: "3", 2: "4", 3: "5"}
        )

        # ensure provided values are suitable for small protocol messages
        if len(prefix) < 1:
            raise ValueError("Prefix key is required.")
        for key in range(0, 4):
            if key not in key_dict_confirmed:
                raise KeyError("Require dict keys for [0, 1, 2, 3]")

        output_message_bits = self.compressed_message_bits
        # Obscure (at bit level) if required
        if obscured:
            output_message_bits = self.obscure(output_message_bits)

        keycode = self._bits_to_digits(output_message_bits)

        # Map each character in keycode to desired output
        keycode = prefix + "".join(map(lambda x: key_dict_confirmed[int(x)], keycode))

        keycode = separator.join(
            keycode[i * group_len : (i + 1) * group_len]
            for i in range(int(math.ceil(len(keycode) / float(group_len))))
        )

        return keycode

    def _generate_mac_bits(self, secret_key):
        """Compute the internal truncated MAC bits for this message.

        Generate a MAC for this message using the specified secret key.  The
        MAC is a 'truncated_MAC', generated from the 12 MSB from the result of
        a SipHash function applied to the message contents and secret key.  The
        returned result will be a 12-bit bitstream.

        MAC is generated using message ID, type code, and body byte.

        :param secret_key: 16-byte secret key, e.g. b"\xff" * 16
        :type secret_key: `bytes`
        :return: bitstream-packed form of the MAC generated using secret_key.
        :rtype: :class:`bitstring`
        """

        # the hash is computed over a struct representation of the message,
        # struct { uint32_t message_id (LE); uint8_t message_type, uint8_t body }
        structed = ints_to_bytes(
            [
                (self.id_ & 0xFF),
                ((self.id_ & 0x0000FF00) >> 8),
                ((self.id_ & 0x00FF0000) >> 16),
                (self.id_ >> 24),
                (self.message_type.value),
                (self.body),
            ]
        )

        function = siphash.SipHash_2_4(secret_key, structed)
        check_value = function.hash() >> 52  # use 12 most-significant bits

        bits = bitstring.pack("uint:12", check_value)

        return bits

    @classmethod
    def _bits_to_digits(cls, bits):
        """Convert the packed message bits to digits for a code.

        :param bits: bits to convert to digit, usually from `bitstring.pack()`
        :type bits: :class:`BitStream`
        """

        stream = bitstring.BitStream(bits)
        digits = ""
        while stream.bitpos < stream.length:
            digits += str(stream.read("uint:2"))

        return digits


class AddCreditSmallMessage(SmallMessage):
    MAX_ADD_CREDIT_DAYS = 405
    COARSE_DAYS_PER_INCREMENT_ID = 3

    def __init__(self, id_, days, secret_key):
        super(AddCreditSmallMessage, self).__init__(
            id_=id_,
            message_type=SmallMessageType.ADD_CREDIT,
            body=AddCreditSmallMessage.generate_body(days),
            secret_key=secret_key,
        )

    @classmethod
    def generate_body(cls, days):
        if isinstance(days, int):
            if 1 <= days <= 180:
                increment_id = days - 1
            elif 181 <= days <= cls.MAX_ADD_CREDIT_DAYS:
                increment_id = ((days - 181) // cls.COARSE_DAYS_PER_INCREMENT_ID) + 180
            else:
                raise ValueError("unsupported number of days")
            return increment_id
        elif days == cls.UNLOCK_FLAG:
            return 255
        else:
            raise ValueError("invalid days value")


class PossibleMessageCollisionError(ValueError):
    pass


class SetCreditSmallMessage(SmallMessage):
    def __init__(self, id_, days, secret_key):
        if id_ & 0x3F == 63 and days == 1:
            # Prevent older small protocol test codes; which are interpreted
            # as a SET_CREDIT message with increment ID 0 and message ID 63.
            # This check prevents possible collisions from occurring.
            # If this error is hit; simply increase the id_ of the message
            # to generate by 1 (e.g. 63->64; 703->704; etc).
            raise PossibleMessageCollisionError(
                "Cannot generate SET_CREDIT small protocol message "
                "with ID where LSB 6 bits are equal to 63!"
            )
        super(SetCreditSmallMessage, self).__init__(
            id_=id_,
            message_type=SmallMessageType.SET_CREDIT,
            body=self.generate_body(days),
            secret_key=secret_key,
        )

    @classmethod
    def generate_body(cls, days):
        if isinstance(days, int):
            if 1 <= days <= 90:
                increment_id = days - 1
            elif 91 <= days <= 180:
                increment_id = (days - 91) // 2 + 90
            elif 181 <= days <= 360:
                increment_id = (days - 181) // 4 + 135
            elif 361 <= days <= 720:
                increment_id = (days - 361) // 8 + 180
            elif 721 <= days <= 960:
                increment_id = (days - 721) // 16 + 225
            elif days == 0:  # lock device
                increment_id = 254
            else:
                raise ValueError("unsupported number of days")
            return increment_id
        elif days == cls.UNLOCK_FLAG:
            return 255
        else:
            raise ValueError("invalid days value")


@enum.unique
class CustomCommandSmallMessageType(enum.Enum):
    """ Values are the increment_id used by this custom command type. """
    # Flags 240-253 are reserved for custom commands.
    WIPE_RESTRICTED_FLAG = 253


class CustomCommandSmallMessage(SmallMessage):
    """Implemented as a SET_CREDIT message with specific increment_id values"""
    def __init__(self, id_, type_, secret_key):
        if (
            not isinstance(type_, CustomCommandSmallMessageType)
            or type_ not in CustomCommandSmallMessageType
        ):
            raise ValueError("unsupported value for 'type_'")

        super(CustomCommandSmallMessage, self).__init__(
            id_=id_,
            message_type=SmallMessageType.SET_CREDIT,
            body=self._generate_body(type_),
            secret_key=secret_key
        )

    @staticmethod
    def _generate_body(type_):
        if type_ == CustomCommandSmallMessageType.WIPE_RESTRICTED_FLAG:
            increment_id = type_.value
        else:
            raise ValueError("Custom command type unknown")

        # We should never reach here, as type is checked above
        if increment_id < 240 or increment_id > 253:
            raise ValueError("increment_id invalid/used by SET_CREDIT")

        return increment_id


class UnlockSmallMessage(AddCreditSmallMessage):
    def __init__(self, id_, secret_key):
        super(AddCreditSmallMessage, self).__init__(
            id_=id_,
            message_type=SmallMessageType.ADD_CREDIT,
            body=AddCreditSmallMessage.generate_body(self.UNLOCK_FLAG),
            secret_key=secret_key,
        )


@enum.unique
class MaintenanceSmallMessageType(enum.Enum):
    WIPE_STATE_0 = 0
    WIPE_STATE_1 = 1
    WIPE_IDS_ALL = 2


class MaintenanceSmallMessage(SmallMessage):
    def __init__(self, type_, secret_key):
        if type_ not in [e for e in MaintenanceSmallMessageType]:
            raise ValueError("unsupported value for 'type_'")

        # body MSB diagnostic value of '1' represents "Maintenance" message
        assert type_.value < 128
        body_bits = type_.value | (1 << 7)
        assert 128 <= body_bits < 256

        super(MaintenanceSmallMessage, self).__init__(
            id_=0,
            message_type=SmallMessageType.MAINTENANCE_TEST,
            body=body_bits,
            secret_key=secret_key,
        )


class PassthroughSmallMessage(SmallMessage):
    PASSTHROUGH_BITS_FIXED_LENGTH = 26

    def __init__(self, bits):
        assert isinstance(bits, bitstring.Bits)
        if len(bits) != self.PASSTHROUGH_BITS_FIXED_LENGTH:
            raise ValueError(
                "Can only pass through {} bits, {} bits provided".format(
                    self.PASSTHROUGH_BITS_FIXED_LENGTH, len(bits)
                )
            )

        super(PassthroughSmallMessage, self).__init__(
            id_=0,
            message_type=SmallMessageType.PASSTHROUGH,
            body=bits,
            secret_key=None,
        )


@enum.unique
class ExtendedSmallMessageType(enum.Enum):
    """ 8 possible extended small message types (0-7)

    (type ID integer, number of body bits dedicated to truncated message ID)
    """
    # Set credit and also clear custom 'restricted flag'
    SET_CREDIT_WIPE_RESTRICTED_FLAG = (0, 2)


class ExtendedSmallMessageIdInvalidError(Exception):
    """The ExtendedSmallMessage cannot be created with the ID requested.

    This is typically raised if a potential MAC/auth collision exists within the
    'receipt window' for the keycode; that is, creating this same
    `ExtendedSmallMessage` with a different ID close to the requested ID will
    result in the same auth/MAC field.

    If this error is raised, attempt to create the keycode again after
    incrementing the ID by 1.
    """


class ExtendedSmallMessage(PassthroughSmallMessage):
    """'Extended' small keycodes carried inside a Passthrough message.

    These are 26-bit messages structured as:

    `atttbbbbbbbbbbmmmmmmmmmmmm`

    * `a` = Passthrough "App ID" (1 bit, 1 = "Extended Small" message)
    * `t` = ExtendedSmallMessageType (3 bits)
    * `b` = Message Body (10 bits, contents dependent on type)
    * `m` = Message Authentication Code (12 bits)

    Message ID *may* be higher than what is requested, to avoid collisions
    within the receiving window on the device. The message ID generated is
    obtained via `message.id_`.
    """
    PASSTHROUGH_APPLICATION_ID_EXTENDED_SMALL_BIT_VALUE = 1
    EXTENDED_SMALL_FIRMWARE_RECEIPT_WINDOW_IDS_ABOVE = 40
    EXTENDED_SMALL_FIRMWARE_RECEIPT_WINDOW_IDS_BELOW = 23

    def __repr__(self):
        return "{}({final_message_id!r}, {body!r})".format(self.__class__.__name__, **self.__dict__)

    def __init__(self, type_, **kwargs):
        bits = bitstring.pack(
            ["uint:1=app_id"],
            app_id=self.PASSTHROUGH_APPLICATION_ID_EXTENDED_SMALL_BIT_VALUE
        )

        if type_ not in [e for e in ExtendedSmallMessageType]:
            raise ValueError("unsupported value for 'type_'")

        bits.append(bitstring.pack(["uint:3=type_code"], type_code=type_.value[0]))
        assert len(bits) == 4

        if type_ == ExtendedSmallMessageType.SET_CREDIT_WIPE_RESTRICTED_FLAG:
            required_args = ['id_', 'days', 'secret_key']
            if not all(arg in kwargs for arg in required_args):
                raise ValueError("Missing required kwargs {}".format(required_args))

            id_ = kwargs['id_']
            days = kwargs['days']
            secret_key = kwargs['secret_key']

            # We might not be able to use the requested `id_` due to
            # MAC collisions, and may need to increment.
            # However, we don't want to increment beyond the message ID window
            auth = None
            final_id = id_
            while (
                auth is None and final_id < (
                    id_ + self.EXTENDED_SMALL_FIRMWARE_RECEIPT_WINDOW_IDS_ABOVE
                )
            ):
                body_bits = self.generate_set_credit_wipe_restricted_flag_body(
                    final_id,
                    days
                )
                assert len(body_bits) == 10
                auth = self.compute_auth_with_no_collisions(
                    final_id,
                    type_,
                    body_bits,
                    secret_key
                )
                if auth is None:
                    logger.info("Unable to use id %s due to collision.", final_id)
                    final_id += 1

            if final_id != id_:
                raise ExtendedSmallMessageIdInvalidError(
                    "ID {} yields MAC collision, next valid ID is {}.".format(
                        id_, final_id)
                )

            assert (
                final_id <
                id_ + self.EXTENDED_SMALL_FIRMWARE_RECEIPT_WINDOW_IDS_ABOVE
            )

            body_and_mac = bitstring.pack(
                ["bits:10=body", "uint:12=auth"],
                body=body_bits,
                auth=auth
            )

            self.final_message_id = final_id

        else:
            raise ValueError("unsupported value for 'type_'")

        # 22 bits for body and MAC fields
        assert len(body_and_mac) == 22

        bits.append(body_and_mac)
        return super(ExtendedSmallMessage, self).__init__(bits=bits)

    @staticmethod
    def _compute_auth(full_id, type_, body, secret_key):
        # type: (int, ExtendedSmallMessageType, bitstring.Bits, bytes) -> int

        packed_mac_inputs = bitstring.pack(
            [
                "uintle:32=full_id",
                "uintle:8=extended_type_code",
                "uintle:16=body_for_auth",  # 10 bits, left is 0-padded
            ],
            full_id=full_id,
            extended_type_code=type_.value[0],
            body_for_auth=body.uint
        )
        mac_input_bytes = packed_mac_inputs.tobytes()
        assert len(mac_input_bytes) == 7
        # 12 MSB bits are MAC/auth
        return siphash.SipHash_2_4(secret_key, mac_input_bytes).hash() >> 52

    @classmethod
    def compute_auth_with_no_collisions(cls, requested_id, type_, body, secret_key):
        # type: (int, ExtendedSmallMessageType, bitstring.Bits, bytes) -> Optional[int]
        # Will return None if there is a possible collision for the requested
        # ID, otherwise will return the auth value for the requested ID.

        # The message contains a truncated ID (2 bits) dividing the window by 4
        SUBWINDOW_STEP_INTERVAL = 2 ** type_.value[1]

        candidate_mac = cls._compute_auth(requested_id, type_, body, secret_key)

        # {auth: msg_id}
        min_window_id = max(
            requested_id - cls.EXTENDED_SMALL_FIRMWARE_RECEIPT_WINDOW_IDS_BELOW,
            0
        )
        max_window_id = min(
            requested_id + cls.EXTENDED_SMALL_FIRMWARE_RECEIPT_WINDOW_IDS_ABOVE,
            # Sanity check that generation is not attempted above UINT16_MAX
            65535,
        )

        for i in range(min_window_id, max_window_id + 1):
            # Only check for collisions on IDs that have the same
            # 2-LSB transmitted message ID bits
            if (requested_id - i) % SUBWINDOW_STEP_INTERVAL != 0:
                continue

            # Don't recompute the candidate MAC
            elif requested_id == i:
                continue

            auth = cls._compute_auth(i, type_, body, secret_key)

            if auth == candidate_mac:
                logger.info("Encountered collision at ID %s (Auth=%s)", i, auth)
                return None

        return candidate_mac

    @classmethod
    def generate_set_credit_wipe_restricted_flag_body(cls, id_, days):
        # type: (int, int) -> bitstring.Bits
        set_credit_increment_id = SetCreditSmallMessage.generate_body(days)

        body_bits = bitstring.pack(
            ["uint:2=truncated_msg_id", "uintle:8=increment_id"],
            # truncate to least-significant 2 bits of the full ID
            truncated_msg_id=id_ & 0b11,
            increment_id=set_credit_increment_id
        )

        return body_bits


@enum.unique
class TestSmallMessageType(enum.Enum):
    SHORT_TEST = 0
    OQC_TEST = 1


class TestSmallMessage(SmallMessage):
    def __init__(self, type_):
        if type_ not in [e for e in TestSmallMessageType]:
            raise ValueError("unsupported value for 'type_'")

        # body MSB diagnostic value of '0' represents "Test" message
        assert type_.value < 128

        super(TestSmallMessage, self).__init__(
            id_=0,
            message_type=SmallMessageType.MAINTENANCE_TEST,
            body=type_.value,
            secret_key=b"\xff" * 16,
        )
