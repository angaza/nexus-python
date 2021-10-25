from unittest import TestCase

import bitstring
from nexus_keycode.tools.generate_small_keycode import create_small_credit_message
import nexus_keycode.protocols.small as protocol


class TestCreateSmallCreditMessage(TestCase):
    def test_invalid_msg_type__raises(self):
        self.assertRaises(
            ValueError, create_small_credit_message, 15, "INVALID_TYPE", b"\x12\xab" * 8, days=4
        )

    def test_valid_add_credit__returns_expected(self):
        msg = create_small_credit_message(15, "ADD", b"\x12\xab" * 8, days=4)
        self.assertEqual(15, msg.id_)
        self.assertEqual(protocol.SmallMessageType.ADD_CREDIT, msg.message_type)
        self.assertEqual(u"135 223 524 333 444", msg.to_keycode())

    def test_valid_set_credit__returns_expected(self):
        msg = create_small_credit_message(15, "SET", b"\x12\xab" * 8, days=4)
        self.assertEqual(15, msg.id_)
        self.assertEqual(protocol.SmallMessageType.SET_CREDIT, msg.message_type)
        self.assertEqual(u"134 522 553 223 545", msg.to_keycode())

    def test_valid_unlock__returns_expected(self):
        msg = create_small_credit_message(15, "UNLOCK", b"\x12\xab" * 8)
        self.assertEqual(15, msg.id_)
        # 'unlock' is a special case of add or set credit for small protocol
        self.assertEqual(protocol.SmallMessageType.ADD_CREDIT, msg.message_type)
        self.assertEqual(u"125 422 435 423 252", msg.to_keycode())
