import enum
import math

import bitstring
import siphash

from nexus_keycode.protocols.utils import pseudorandom_bits


@enum.unique
class FullMessageWipeFlags(enum.Enum):
    TARGET_FLAGS_0 = 0  #: Wipe state, except for recvd-msgs bitmask
    TARGET_FLAGS_1 = 1  #: Wipe state, including recvd-msgs bitmask
    WIPE_IDS_ALL = 2  #: Clear device recvd-msgs bitmask (no ACE modification)
    RESERVED = 3


@enum.unique
class FullMessageType(enum.Enum):
    ADD_CREDIT = 0
    SET_CREDIT = 1
    WIPE_STATE = 2
    RESERVED = 3
    FACTORY_ALLOW_TEST = 4
    FACTORY_OQC_TEST = 5
    FACTORY_DISPLAY_PAYG_ID = 6

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

    :see: :class:`FactoryMessage`
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
        :type body: :class:`bytes`
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
            assert len(body) == 0
            self.body_int = 0
            assert full_id == 0
            self.header = "{0}".format(self.message_type.value)  # ignore full_id

        else:
            assert len(body) > 0
            # used in check -- uint32_t repr of deobscured body digits.
            self.body_int = int(body)
            # transmitted ID is 6-LSB (0x3F) of full ID
            self.header = "{0}{1:02d}".format(self.message_type.value, (full_id & 0x3F))

        self.mac = self._generate_mac()

    def __str__(self):
        return self.to_keycode(obscured=False)

    def __repr__(self):
        return (
            "{}.{}("
            "{header!r}, "
            "{body!r}, "
            "{secret_key!r}, "
            "is_factory={is_factory!r}))"
        ).format(self.__class__.__module__, self.__class__.__name__, **self.__dict__)

    @classmethod
    def obscure(cls, digits, sign=1):

        perturbed = list(map(int, list(digits)))

        assert len(digits) == 14

        # MAC digits are last 6 of perturbed, use uint32_t value as seed
        packed_check = bitstring.pack("uintle:32", int(digits[-6:]))

        # [0, 255] values; one for each body digit
        # 8 body digits, 8 bytes (8 bits each), so 64 bits of output required
        pr_bits = pseudorandom_bits(packed_check, 64)

        for (i, d) in enumerate(perturbed[:8]):
            # value [0, 255]
            pr_value = pr_bits[i * 8 : (i * 8 + 8)].uint * sign
            perturbed[i] += pr_value
            perturbed[i] %= 10

        return "".join(map(str, perturbed))

    @classmethod
    def deobscure(cls, digits):
        return cls.obscure(digits, sign=-1)

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

        keycode = self.header + self.body + self.mac

        if obscured or (obscured is not False and not self.is_factory):
            keycode = self.obscure(keycode)

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
        return "{:06d}".format(function.hash() & 0xFFFFFFFF)[-6:]


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
            body="{0:05d}".format(hours),
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
            body="{0:05d}".format(hours),
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
            body="{0:05d}".format(cls.UNLOCK_FLAG_IN_HOURS),
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
        if flags == FullMessageWipeFlags.RESERVED:
            raise ValueError("reserved is unsupported for wipe flags")

        return cls(
            full_id=id_,
            message_type=FullMessageType.WIPE_STATE,
            body="{0:1d}{1:04d}".format(0, flags.value),
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
        :rtype: :class:`FactoryMessage`
        """
        return cls(message_type=FullMessageType.FACTORY_ALLOW_TEST, body="")

    @classmethod
    def oqc_test(cls):
        """Provide 1 hour of credit (additive) up to 10 times per device.

        Allows for factory and warehouse ongoing testing before sale.

        Message contains no body.

        :return: Message object of format FACTORY_OQC_TEST
        :rtype: :class:`FactoryMessage`
        """
        return cls(message_type=FullMessageType.FACTORY_OQC_TEST, body="")

    @classmethod
    def display_payg_id(cls):
        """Returns feedback instructing product code to display the PAYG
        ID provisioned to the PAYG MCU via an LED or LCD display.

        Allows for factory, warehouse, and field determination of PAYG ID.

        Message contians no body.

        :return: Message object of format FACTORY_DISPLAY_PAYG_ID_TEST
        :rtype: :class:`FactoryMessage`
        """
        return cls(message_type=FullMessageType.FACTORY_DISPLAY_PAYG_ID, body="")
