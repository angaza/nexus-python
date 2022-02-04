import enum
import math

import bitstring
import siphash

from typing import Any  # noqa F401

from nexus_keycode.protocols.passthrough_uart import (
    compute_passthrough_uart_keycode_numeric_body_and_mac,
)
from nexus_keycode.protocols.channel_origin_commands import ChannelOriginAction
from nexus_keycode.protocols.utils import full_deobscure, full_obscure

NEXUS_MODULE_VERSION_STRING = "1.1.0"
NEXUS_INTEGRITY_CHECK_FIXED_00_KEY = b"\x00" * 16


@enum.unique
class FullMessageWipeFlags(enum.Enum):
    TARGET_FLAGS_0 = 0  #: Wipe state, except for recvd-msgs bitmask
    TARGET_FLAGS_1 = 1  #: Wipe state, including recvd-msgs bitmask
    WIPE_IDS_ALL = 2  #: Clear device recvd-msgs bitmask (no ACE modification)
    WIPE_RESTRICTED_FLAG = 3  #: Clear device 'restricted' flag (app specific)


@enum.unique
class FullMessageType(enum.Enum):
    ADD_CREDIT = 0
    SET_CREDIT = 1
    WIPE_STATE = 2
    RESERVED_TYPE_ID_3 = 3
    FACTORY_ALLOW_TEST = 4
    FACTORY_OQC_TEST = 5
    FACTORY_DISPLAY_PAYG_ID = 6
    RESERVED_TYPE_ID_7 = 7
    PASSTHROUGH_COMMAND = 8

    @property
    def parsers(self):
        """String-to-value parsers for all parameters of this message type.

        :return: {"param_name": str_to_value_func, ...}
        :rtype: :class:`dict`
        """

        cls = type(self)
        parsers = {
            cls.ADD_CREDIT: {"hours": int},
            cls.SET_CREDIT: {"hours": int},
            cls.WIPE_STATE: {"flags": FullMessageWipeFlags.__getitem__},
            cls.RESERVED: {"minutes": int},
            cls.FACTORY_ALLOW_TEST: {"reserved": int},
            cls.FACTORY_OQC_TEST: {"reserved": int},
            cls.FACTORY_DISPLAY_PAYG_ID: {"reserved": int},
            cls.PASSTHROUGH_COMMAND: {"application_id": int, "opaque_data": int},
        }

        return parsers[self]

    def build(self, **kwargs):
        """Construct an instance of this message type.

        :param kwargs: type-specific message parameters
        :type kwargs: :class:`dict`
        :return: constructed message instance
        :rtype: :class:`FullMessage`
        """

        cls = type(self)
        constructors = {
            cls.ADD_CREDIT: FullMessage.add_credit,
            cls.SET_CREDIT: FullMessage.set_credit,
            cls.WIPE_STATE: FullMessage.wipe_state,
            cls.RESERVED: FullMessage.reserved,
        }

        return constructors[self](**kwargs)


class BaseFullMessage(object):
    """Arbitrary keycode message; immutable.

    Typically, you'll want to use one of the specific derived types instead.

    :see: :class:`FactoryFullMessage`
    :see: :class:`FullMessage`
    """

    def __init__(self, full_id, message_type, body, secret_key, is_factory):
        """
        Secret key provided must be pseudorandom, the first 16 bytes (if
        provided key is longer than 16 bytes) is used for a hashing operation
        which requires a key of exactly 16 bytes/128-bits.

        :param full_id: unsigned integer message ID < UINT32_MAX (0xFFFFFFFF)
        :type full_id: :class:`int`
        :param message_type: integer value for the message type
        :type message_type: :class:`FullMessageType`
        :param body: arbitrary digits of message body
        :type body: str
        :param secret_key: secret hash key (requires 16 bytes, uses first 16)
        :type secret_key: `bytes`
        """

        if message_type not in [e for e in FullMessageType]:
            raise ValueError("unsupported credit message type code")

        # Siphash requires a 16-byte input key.
        self.secret_key = secret_key[:16]
        self.is_factory = is_factory

        self.full_id = full_id
        self.message_type = message_type
        self.body = body  # shorter body for 'factory' messages

        if self.is_factory is True:
            if self.body == "":
                self.body_int = 0
            else:
                self.body_int = int(self.body)
            assert full_id == 0
            self.header = u"{0}".format(self.message_type.value)  # ignore full_id

        else:
            assert len(body) > 0
            # used in check -- uint32_t repr of deobscured body digits.
            self.body_int = int(body)
            # transmitted ID is 6-LSB (0x3F) of full ID
            self.header = u"{0}{1:02d}".format(
                self.message_type.value, (full_id & 0x3F)
            )

        self.mac = None
        # no need to generate MAC for passthrough keycode
        if self.message_type != FullMessageType.PASSTHROUGH_COMMAND:
            self.mac = self._generate_mac()

    def __str__(self):
        return self.to_keycode(obscured=False)

    def __repr__(self):
        return (
            u"{}.{}("
            u"{header!r}, "
            u"{body!r}, "
            u"{secret_key!r}, "
            u"is_factory={is_factory!r}))"
        ).format(self.__class__.__module__, self.__class__.__name__, **self.__dict__)

    @classmethod
    def obscure(cls, digits):
        return full_obscure(digits)

    @classmethod
    def deobscure(cls, digits):
        return full_deobscure(digits)

    def to_keycode(
        self, prefix="*", suffix="#", separator=" ", group_len=3, obscured=None
    ):
        """Render this message in keycode form.

        The rendered message can be transferred to a human. For example:

        >>> message = BaseFullMessage("0" * 4, "1" * 8, b"\x00" * 16)
        >>> message.to_keycode(prefix="*", suffix="#", separator="-")
        '*815-335-269-161-611-719#'

        :param prefix: keycode start character, e.g., "*"
        :type prefix: :class:`str`
        :param suffix: keycode end character, e.g., "#"
        :type suffix: :class:`str`
        :param separator: inter-group separating character, e.g., "-"
        :type separator: :class:`str`
        :param group_len: number of characters in each separated group
        :type group_len: :class:`int`
        :param obscured: obscured or not
        :type obscure: `bool`
        :return: the rendered keycode string
        :rtype: :class:`str`
        """

        keycode = self.header + self.body

        # Passthrough keycodes do not contain a MAC
        if self.mac is not None:
            keycode += self.mac

        if obscured or (obscured is not False and not self.is_factory):
            # Obscured activation keycodes are always 14 digits in length
            assert len(keycode) == 14
            keycode = full_obscure(keycode)

        keycode = separator.join(
            keycode[i * group_len : (i + 1) * group_len]
            for i in range(int(math.ceil(len(keycode) / float(group_len))))
        )

        return prefix + keycode + suffix

    def _generate_mac(self):
        # generate the internal, *truncated* MAC digits for this message
        # MAC is generated over 9 total bytes:
        # 4 = full_message_id (as uint32_t)
        # 1 = message_type (as uint8_t)
        # 4 = contents of body (as uint32_t)
        function = siphash.SipHash_2_4(self.secret_key)

        packed_for_check = bitstring.pack(
            [
                "uintle:32=full_id",
                "uintle:8=message_type",
                "uintle:32=body_int",
            ],  # uint32_t repr of body digits
            full_id=self.full_id,
            message_type=self.message_type.value,
            body_int=self.body_int,
        )

        function.update(packed_for_check.bytes)

        # check/MAC is the lowest 6 decimal digits from the computed check
        return u"{:06d}".format(function.hash() & 0xFFFFFFFF)[-6:]


@enum.unique
class PassthroughApplicationId(enum.Enum):
    TO_PAYG_UART_PASSTHROUGH = 0
    # Used to convey Nexus Channel origin commands in a passthrough message
    CHANNEL_ORIGIN_COMMAND = 1


class FullMessage(BaseFullMessage):
    UNLOCK_FLAG_IN_HOURS = 99999

    def __init__(self, full_id, message_type, body, secret_key, is_factory=False):
        super(FullMessage, self).__init__(
            # 'full' message
            full_id=full_id,
            message_type=message_type,
            body=body,
            secret_key=secret_key,
            is_factory=is_factory,
        )

    @classmethod
    def add_credit(cls, id_, hours, secret_key):
        """Increase device's enabled credit by a specified amount

        :param id_: Message ID
        :type id_: :class:`int`
        :param hours: Number of enabled hours to add to device
        :type hours: :class:`int`
        :param secret_key: Device's secret_key
        :type secret_key: `str`
        :return: Message object of format ADD_CREDIT
        :rtype: :class:`FullMessage`
        """
        return cls(
            full_id=id_,
            message_type=FullMessageType.ADD_CREDIT,
            body=u"{0:05d}".format(hours),
            secret_key=secret_key,
        )

    @classmethod
    def set_credit(cls, id_, hours, secret_key):
        """Set device's enabled credit to specified amount

        :param id_: Message ID
        :type id_: :class:`int`
        :param hours: Number of enabled hours to set for device
        :type hours: :class:`int`
        :param secret_key: Device's secret_key
        :type secret_key: `str`
        :return: Message object of format SET_CREDIT
        :rtype: :class:`FullMessage`
        """
        return cls(
            full_id=id_,
            message_type=FullMessageType.SET_CREDIT,
            body=u"{0:05d}".format(hours),
            secret_key=secret_key,
        )

    @classmethod
    def unlock(cls, id_, secret_key):
        """Unlock a device

        :param id_: Message ID
        :type id_: :class:`int`
        :param secret_key: Device's secret_key
        :type secret_key: `str`
        :return: Message object of format SET_CREDIT
        :rtype: :class:`FullMessage`
        """
        return cls(
            full_id=id_,
            message_type=FullMessageType.SET_CREDIT,
            body=u"{0:05d}".format(cls.UNLOCK_FLAG_IN_HOURS),
            secret_key=secret_key,
        )

    @classmethod
    def reserved(cls, id_, minutes, secret_key):
        raise ValueError("reserved is unsupported")

    @classmethod
    def wipe_state(cls, id_, flags, secret_key):
        """Induce device to wipe state according to target flags rules

        :param id_: Full Message ID
        :type id_: :class:`int`
        :param flags: Type of wipe action this code should perform
        :type flags: :class:`FullMessageWipeFlags`
        :param secret_key: Device's secret_key
        :type secret_key: `str`
        :return: Message object of format WIPE_STATE
        :rtype: :class:`FullMessage`
        """
        if flags not in [e for e in FullMessageWipeFlags]:
            raise ValueError("unsupported wipe flag")

        return cls(
            full_id=id_,
            message_type=FullMessageType.WIPE_STATE,
            body=u"{0:1d}{1:04d}".format(0, flags.value),
            secret_key=secret_key,
        )


class FactoryFullMessage(FullMessage):
    def __init__(self, message_type, body):
        super(FactoryFullMessage, self).__init__(
            full_id=0,  # always 0 ID for factory msg
            message_type=message_type,
            body=body,
            secret_key=b"\x00" * 16,
            is_factory=True,
        )

    @classmethod
    def allow_test(cls):
        """Briefly enable a device even if it is PAYG disabled

        Allows for field testing of potentially faulty product.

        Message contains no body.

        :return: Message object of format FACTORY_ALLOW_TEST
        :rtype: :class:`FactoryFullMessage`
        """
        return cls(message_type=FullMessageType.FACTORY_ALLOW_TEST, body="")

    @classmethod
    def oqc_test(cls, num_min=60):
        # type: (int)->FactoryFullMessage
        """Provide :num_min of credit (additive) up to 10 times per device.

        Allows for factory and warehouse ongoing testing before sale.

        :param num_min: int of minutes of credit to add to device.
        :return: Message object of format FACTORY_OQC_TEST
        :rtype: :class:`FactoryFullMessage`
        """
        if not isinstance(num_min, int):
            raise TypeError("Expected num_min to be an instance of int but actual type was: {}.".format(type(num_min)))
        if num_min < 1 or 99 < num_min:
            raise ValueError("num_min must be between 1 and 99 but was: {}.".format(num_min))
        return cls(message_type=FullMessageType.FACTORY_OQC_TEST, body="000{:02d}".format(num_min))

    @classmethod
    def display_payg_id(cls):
        """Returns feedback instructing product code to display the PAYG
        ID provisioned to the PAYG MCU via an LED or LCD display.

        Allows for factory, warehouse, and field determination of PAYG ID.

        Message contains no body.

        :return: Message object of format FACTORY_DISPLAY_PAYG_ID_TEST
        :rtype: :class:`FactoryFullMessage`
        """
        return cls(message_type=FullMessageType.FACTORY_DISPLAY_PAYG_ID, body="")

    @classmethod
    def passthrough_channel_origin_command(cls, channel_action, **kwargs):
        # type: (ChannelOriginAction, dict[str, Any])->FactoryFullMessage
        """Specific helper to create Nexus Channel origin commands.

        These commands are conveyed in a Nexus Keycode Passthrough message."""
        if not isinstance(channel_action, ChannelOriginAction):
            raise TypeError("Missing Nexus Channel Origin Action.")

        origin_command = channel_action.build(**kwargs)
        # Will prepend passthrough and subtype ID to the generated command
        return cls.passthrough_command(
            PassthroughApplicationId.CHANNEL_ORIGIN_COMMAND,
            origin_command.to_digits()
        )

    @classmethod
    def passthrough_command(cls, application_id, passthrough_digits):
        # type: (PassthroughApplicationId, str)-> FactoryFullMessage
        """Send a keycode which contains application-specific data, and
        will not be parsed by the embedded keycode library. Passthrough
        commands do not trigger any UI feedback (keycode accepted/etc) from the
        Nexus Keycode firmware library, and instead defer any activity at all to
        the final application which receives and parses the passthrough
        command.

        Warning: passthrough commands *do not* have any MAC, and are not
        validated in any way by the Nexus library in devices - the passthrough
        `subtype ID` is examined, and the message is forwarded onward
        accordingly. Applications that use passthrough command should include
        integrity checks on the transmitted data inside the message body.

        :param application_id: ID of device application processing this command
        :type application_id: :class:`PassthroughApplicationId`
        :param passthrough_digits: Digits that will be built into a message
        :type passthrough_digits: :class:`string`
        :return: Message object of format PASSTHROUGH_COMMAND
        :rtype: :class:`FactoryFullMessage`
        """
        if not isinstance(application_id, PassthroughApplicationId):
            raise TypeError("Passthrough command requires an application ID.")

        body = u"{:d}{}".format(application_id.value, passthrough_digits)

        if len(body) == 13:
            # Once we append the message header, we'll be at 14 digits.
            # Firmware uses 14-digits to unambiguously identify 'activation'
            # tokens.
            raise ValueError("Passthrough body cannot be 13 total digits.")

        return cls(message_type=FullMessageType.PASSTHROUGH_COMMAND, body=body)

    @classmethod
    def passthrough_uart_keycode_numeric_body_and_mac(cls, secret_key):
        """Use a given secret key to generate a passthrough keycode
        :param secret_key: secret key used to generate UART security key
        :type secret_key: byte
        """
        numeric_body_and_mac = compute_passthrough_uart_keycode_numeric_body_and_mac(secret_key)
        return cls.passthrough_command(
            PassthroughApplicationId.TO_PAYG_UART_PASSTHROUGH, numeric_body_and_mac
        )
