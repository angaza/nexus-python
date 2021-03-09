import enum
import bitstring
import siphash

# for 'generate_body' in `SET_CREDIT_WIPE_RESTRICTED_FLAG`
from nexus_keycode.protocols.small import SetCreditSmallMessage, PassthroughSmallMessage

NEXUS_MODULE_VERSION_STRING = "1.0.0"


@enum.unique
class ChannelOriginAction(enum.Enum):
    """Business logic list of possible origin command actions."""
    UNLINK_ALL_ACCESSORIES = object()
    UNLOCK_ALL_ACCESSORIES = object()
    UNLOCK_ACCESSORY = object()
    UNLINK_ACCESSORY = object()
    LINK_ACCESSORY_MODE_3 = object()
    # Borne in Channel Origin actions, but does not interact with or modify
    # Nexus Channel state.
    KEYCODE_SET_CREDIT_WIPE_RESTRICTED_FLAG = object()

    def build(self, **kwargs):
        # type: () -> ChannelOriginCommandToken
        """Construct an instance of this message type."""

        cls = type(self)
        constructors = {
            cls.UNLINK_ALL_ACCESSORIES: (
                GenericControllerActionToken.unlink_all_accessories
            ),
            cls.UNLOCK_ALL_ACCESSORIES: (
                GenericControllerActionToken.unlock_all_accessories
            ),
            cls.UNLOCK_ACCESSORY: (
                SpecificLinkedAccessoryToken.unlock_specific_accessory
            ),
            cls.UNLINK_ACCESSORY: (
                SpecificLinkedAccessoryToken.unlink_specific_accessory
            ),
            cls.LINK_ACCESSORY_MODE_3: (
                LinkCommandToken.challenge_mode_3
            ),
            # Special passthrough command not conveying Channel information.
            # Smallpad bearer only.
            cls.KEYCODE_SET_CREDIT_WIPE_RESTRICTED_FLAG: (
                GenericControllerActionToken.keycode_set_credit_wipe_restricted_flag
            )
        }

        return constructors[self](**kwargs)


@enum.unique
class OriginCommandType(enum.Enum):
    """ Types of Nexus Origin commands that exist.
    Types 0-9 are possible to transmit via keycode. Additional types
    may exist in the future which are not easily transmitted via token.

    This is not called directly; as some business-facing 'types' are actually
    subtypes of the types defined here. The types in this list map
    directly to the "Origin Command Types" defined in the spec.

    This enum should not be used/exposed outside of this module.
    """
    GENERIC_CONTROLLER_ACTION = 0
    UNLOCK_ACCESSORY = 1
    UNLINK_ACCESSORY = 2
    # 3-8 reserved
    LINK_ACCESSORY_MODE_3 = 9


@enum.unique
class OriginCommandBearerProtocol(enum.Enum):
    """ Bearer protocols for Origin Commands.

    ASCII digits (0-9) supports all Nexus Channel functionality. Other
    bearer protocols are experimental and limited in functionality.
    """

    ASCII_DIGITS = object()
    SMALLPAD_BITS = object()


class ChannelOriginCommandToken(object):
    """Data sent from the Nexus Channel origin (backend) to a controller.

    This data is typically encoded as a string of decimal digits 0-9.

    For some limited use cases, a small protocol compatible stream of bits
    may be used, see `KEYCODE_SET_CREDIT_WIPE_RESTRICTED_FLAG`.

    This data may be packed into a keycode (see `PASSTHROUGH_COMMAND` in
    `keycodev1.py`), or may be transmitted inside any other format.
    It is likely, however, that for more 'advanced' transmission formats,
    we may decide to use a more expressive data format.

    `ChannelOriginCommandTokens` all include appropriate integrity
    checks, and do not make any assumptions about integrity checks provided by
    lower-level transport protocols.

    A `ChannelOriginCommandToken` typically takes the following form
    (when borne in `ASCII_DIGITS` 0-9):

    [1-digit command code][N-digit message body][M-digit 'auth' fields]

    These 1+N+M digits are expected to be placed inside the body of a
    lower-level keycode transport protocol - which is responsible for getting
    the `ChannelOriginCommandToken` into a controller through an existing
    keycode protocol.

    :see: :class:`LinkCommandToken`
    """

    def __init__(self, type_, body, auth, bearer=OriginCommandBearerProtocol.ASCII_DIGITS):
        """
        :param type_: Type of origin command this token represents
        :type type_: :class:`OriginCommandType`
        :param body: arbitrary contents of message body
        :type body: :class:`str`
        :param auth: Siphash_2_4 object which exposes a hash via `.hash()`
        :type auth: :class:`str`
        :param bearer: Bearing protocol/encoding for the command
        :type bearer: :class:`OriginCommandBearerProtocol`
        """
        if not isinstance(type_, OriginCommandType):
            raise TypeError("Must supply valid OriginCommandType.")

        self.type_code = type_.value
        self.body = body
        self.auth = auth
        self.bearer = bearer

    def __str__(self):
        return self.to_digits()

    def __repr__(self):
        return (
            "{}.{}("
            "{type_code!r}, "
            "{bearer!r}, "
            "{body!r}, "
            "{auth!r},))").format(
            self.__class__.__module__,
            self.__class__.__name__,
            **self.__dict__)

    def to_digits(self):
        # type: () -> str
        # String of digits making up this Nexus Channel "Token".

        if self.bearer == OriginCommandBearerProtocol.SMALLPAD_BITS:
            # Create 26-bit 'passthrough' message
            # 1-bit = 0b1 (Passthrough app ID = Nexus Channel Origin Command)
            # 3-bits = Origin Command Type ID
            # 10-bits = Body (interpretation dependent on contents)
            # 12-bits = MAC

            bits = bitstring.pack(
                [
                    "uint:1=app_id",
                    "bits:13=body",
                    "uint:12=mac",
                ],
                app_id=1,
                nx_channel_origin_command_type_code=self.type_code,
                body=self.body,
                # 12 MSB bits of hash
                mac=self.auth.hash() >> 52
            )

            small_message = PassthroughSmallMessage(bits)
            return small_message.to_keycode()

        else:
            # ASCII_DIGITS
            result = "{}{}{}".format(
                self.type_code,
                self.body,
                self.auth_digits(),
            )
        return result

    def auth_digits(self):
        return self.digits_from_siphash(self.auth)

    @staticmethod
    def digits_from_siphash(siphash_function, digits=6):
        """ Return the least-significant digits from a Siphash function.

        Defaults to 6, may be increased.
        """
        format_str = "{{:0{}d}}".format(digits)
        return format_str.format(
            siphash_function.hash() & 0xffffffff
        )[-digits:]


class GenericControllerActionToken(ChannelOriginCommandToken):
    """ Not intended to be instantiated directly.

    see: `unlink_all_accessories`.
    """

    _origin_command_type = OriginCommandType.GENERIC_CONTROLLER_ACTION

    def __init__(
            self,
            type_,
            # ASCII digits or bitstream, depending on the bearer
            controller_command_and_action_data,
            auth,
            bearer,
    ):
        super(GenericControllerActionToken, self).__init__(
            type_=self._origin_command_type,
            body=controller_command_and_action_data,
            auth=auth,
            bearer=bearer,
        )

    @enum.unique
    class GenericControllerActionType(enum.Enum):
        """ Types of 'generic controller actions' that are possible.
        Types 0-20 are reserved for Angaza use. Other types may be 'custom'
        as needed.

        These type values are used in authentication on the device side
        and are not arbitrary, renumbering will result in a breaking change.
        """

        # Delete all accessories from the receiving controller
        UNLINK_ALL_ACCESSORIES = 0
        # Unlock all accessories linked to the receiving controller
        UNLOCK_ALL_ACCESSORIES = 1
        KEYCODE_SET_CREDIT_WIPE_RESTRICTED_FLAG = 6
        # Types 2-5, 7-99 undefined

    @classmethod
    def _generic_controller_action_builder(
        cls,
        type_,
        type_action_data,
        controller_command_count,
        controller_sym_key,
        bearer=OriginCommandBearerProtocol.ASCII_DIGITS,
    ):
        # type: (cls.GenericControllerActionType, int, int, str) -> ChannelOriginCommandToken
        """ Resulting token:

        1-digit Origin Keycode Type ID (0)
        2-digit "Origin Controller Commmand" (0-99)
        0-65535 (uint16_t) arbitrary "Action Data" (for SET_CREDIT_WIPE_RESTRICTED_FLAG only)
        6-digit target authentication (auth for controller)
        """
        # Requires 16-bit symmetric Nexus keys
        assert len(controller_sym_key) == 16
        controller_command_value = type_.value

        if type_action_data is None:
            type_action_data_int = 0
        else:
            type_action_data_int = type_action_data

        packed_target_inputs = bitstring.pack(
            [
                "uintle:32=controller_command_count",
                "uintle:8=origin_command_type_code",  # '0 = Generic Controller Action'
                "uintle:16=controller_command_value",  # generic action 'type'
                "uintle:16=type_action_data",  # if unused, '0'
            ],
            controller_command_count=controller_command_count,
            origin_command_type_code=cls._origin_command_type.value,
            controller_command_value=controller_command_value,
            type_action_data=type_action_data_int,
        ).bytes
        assert len(packed_target_inputs) == 9

        auth = siphash.SipHash_2_4(
            controller_sym_key,
            packed_target_inputs)

        if bearer == OriginCommandBearerProtocol.SMALLPAD_BITS:
            if type_ != cls.GenericControllerActionType.KEYCODE_SET_CREDIT_WIPE_RESTRICTED_FLAG:
                raise NotImplementedError("Type {} not implemented".format(type_))

            body_bits = bitstring.pack(
                [
                    "uint:3=controller_command_data",
                    "bits:2=generic_action_type_id",
                    "uintle:8=set_credit_increment_id",
                ],
                # '0', generic controller action
                controller_command_data=cls._origin_command_type.value,
                # '11' indicates set credit + wipe restricted
                generic_action_type_id=bitstring.Bits('0b11'),
                set_credit_increment_id=type_action_data
            )

            return cls(
                type_=type_,
                controller_command_and_action_data=body_bits,
                auth=auth,
                bearer=bearer
            )

        else:
            # 'type_action_data' is currently unused for ASCII bearer
            assert type_action_data is None
            return cls(
                type_=type_,
                controller_command_and_action_data="{:02d}".format(controller_command_value),
                auth=auth,
                bearer=bearer
            )

    @classmethod
    def unlink_all_accessories(
        cls,
        controller_command_count,
        controller_sym_key
    ):
        return cls._generic_controller_action_builder(
            cls.GenericControllerActionType.UNLINK_ALL_ACCESSORIES,
            None,
            controller_command_count,
            controller_sym_key,
        )

    @classmethod
    def unlock_all_accessories(
        cls,
        controller_command_count,
        controller_sym_key
    ):
        return cls._generic_controller_action_builder(
            cls.GenericControllerActionType.UNLOCK_ALL_ACCESSORIES,
            None,
            controller_command_count,
            controller_sym_key,
        )

    @classmethod
    def keycode_set_credit_wipe_restricted_flag(
        cls,
        days,
        controller_command_count,
        controller_sym_key,
    ):
        if days == u"UNLOCK":
            days = SetCreditSmallMessage.UNLOCK_FLAG
        set_credit_increment_id = SetCreditSmallMessage.generate_body(days)
        return cls._generic_controller_action_builder(
            cls.GenericControllerActionType.KEYCODE_SET_CREDIT_WIPE_RESTRICTED_FLAG,
            set_credit_increment_id,
            controller_command_count,
            controller_sym_key,
            bearer=OriginCommandBearerProtocol.SMALLPAD_BITS,
        )


class SpecificLinkedAccessoryToken(ChannelOriginCommandToken):
    def __init__(
            self,
            type_,
            accessory_asp_id,
            auth
    ):
        # Truncated Nexus ID = least significant one decimal digits
        truncated_accessory_asp_id = "{:01d}".format(
            (accessory_asp_id & 0xFFFFFFFF) % 10)
        super(SpecificLinkedAccessoryToken, self).__init__(
            type_=type_,
            body=truncated_accessory_asp_id,
            auth=auth,
        )

    @classmethod
    def _specific_accessory_builder(
        cls,
        type_,
        accessory_asp_id,
        controller_command_count,
        controller_sym_key
    ):
        # type: (int, int, int, str, str) -> ChannelOriginCommandToken
        """ Resulting token:

        1-digit Origin Keycode Type ID (2)
        1-digit body field (Accessory Nexus ID, truncated)
        6-digit target authentication (MAC)

        Note that the controller cannot validate this command if it does not
        actually have a link to the specified accessory. This is because
        the MAC is generated using the accessory Nexus ID, and thus it must
        'look up' the accessory Nexus ID to validate the message.

        Practically, we can do this by allowing the origin manager to 'ask'
        for the ID of all linked accessories (optionally those matching the
        truncated ID), and attempt to compute the MAC using each of those. If
        there is no match, the message is invalid.

        The expanded 'body' consists of two parts - the Nexus 'authority'
        ID (first 2 bytes of Nexus ID), and the Nexus 'device' ID (last 4 bytes
        of Nexus ID).
        """

        # Requires 16-bit symmetric Nexus keys
        assert len(controller_sym_key) == 16

        # note that these are not 'transmitted' body digits, but it is
        # assumed that the receiver will 'expand' the message (from the
        # transmitted, truncated accessory ID) to then find any linked
        # accessory with a matching device ID, and pull in the full values
        # to use to generate this MAC.

        # vendor / authority ID is upper 2 bytes of the full 'Nexus ID'
        nexus_authority_id = (accessory_asp_id & 0xFFFF00000000) >> 32
        nexus_device_id = accessory_asp_id & 0xFFFFFFFF

        packed_target_inputs = bitstring.pack(
            [
                "uintle:32=controller_command_count",
                "uintle:8=origin_command_type_code",  # '2' or '3'
                "uintle:16=nexus_authority_id",
                "uintle:32=nexus_device_id",
            ],
            controller_command_count=controller_command_count,
            origin_command_type_code=type_.value,
            nexus_authority_id=nexus_authority_id,
            nexus_device_id=nexus_device_id
        ).bytes

        assert len(packed_target_inputs) == 11
        auth = siphash.SipHash_2_4(
            controller_sym_key,
            packed_target_inputs
        )

        return cls(
            type_=type_,
            accessory_asp_id=accessory_asp_id,
            auth=auth
        )

    @classmethod
    def unlink_specific_accessory(
            cls,
            accessory_asp_id,
            controller_command_count,
            controller_sym_key
    ):
        return cls._specific_accessory_builder(
            OriginCommandType.UNLINK_ACCESSORY,
            accessory_asp_id,
            controller_command_count,
            controller_sym_key
        )

    @classmethod
    def unlock_specific_accessory(
            cls,
            accessory_asp_id,
            controller_command_count,
            controller_sym_key
    ):
        return cls._specific_accessory_builder(
            OriginCommandType.UNLOCK_ACCESSORY,
            accessory_asp_id,
            controller_command_count,
            controller_sym_key
        )


class LinkCommandToken(ChannelOriginCommandToken):

    _origin_command_type = OriginCommandType.LINK_ACCESSORY_MODE_3

    def __init__(
            self,
            type_,
            body,
            auth
    ):
        super(LinkCommandToken, self).__init__(
            type_=type_,
            body=body,
            auth=auth)

    @classmethod
    def challenge_mode_3(
            cls,
            accessory_asp_id,
            controller_command_count,
            accessory_command_count,
            accessory_sym_key,
            controller_sym_key):
        # type: (int, int, int, str, str) -> ChannelOriginCommandToken
        """ Resulting token:

        1-digit Origin Keycode Type ID (9)
        7-digit body (1 digit Truncated Nexus ID, 6 "Challenge Result" digits)
        6-digit auth (controller authentication)
        """

        command_type = OriginCommandType.LINK_ACCESSORY_MODE_3

        # Requires 16-bit symmetric Nexus keys
        assert len(accessory_sym_key) == 16
        assert len(controller_sym_key) == 16

        # this auth is the 'challenge result' which accessory will validate
        packed_target_inputs = bitstring.pack(
            ["uintle:32=accessory_command_count"],
            accessory_command_count=int(accessory_command_count)
        ).bytes
        assert len(packed_target_inputs) == 4
        accessory_auth = siphash.SipHash_2_4(
            accessory_sym_key,
            packed_target_inputs
        )

        # 6-digits
        accessory_auth_digits = cls.digits_from_siphash(accessory_auth)

        trunc_accessory_device_id = "{:01d}".format(
            (accessory_asp_id & 0xFFFFFFFF) % 10)

        # This auth is used by the receiver of the origin command
        # the receiver will unpack the truncated accessory Nexus ID and the
        # challenge digits, and recompute a MAC using these. Only if the MAC
        # is valid will the challenge digits be passed onwards to the accessory
        packed_auth_inputs = bitstring.pack(
            [
                "uintle:32=controller_command_count",
                "uintle:8=command_type_code",  # '9'
                "uintle:8=trunc_accessory_asp_id",
                "uintle:32=challenge_digits_int",  # challenge digits as int
            ],
            controller_command_count=controller_command_count,
            command_type_code=command_type.value,
            trunc_accessory_asp_id=trunc_accessory_device_id,
            challenge_digits_int=int(accessory_auth_digits)
        )
        assert len(packed_auth_inputs.tobytes()) == 10

        body_digits = trunc_accessory_device_id + accessory_auth_digits

        auth = siphash.SipHash_2_4(
            controller_sym_key,
            packed_auth_inputs.bytes)

        return cls(
            type_=command_type,
            body=body_digits,
            auth=auth,
        )
