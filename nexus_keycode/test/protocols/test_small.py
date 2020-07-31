from unittest import TestCase

import nexus_keycode.protocols.small as protocol


class TestTestSmallMessage(TestCase):
    def test_init__invalid_type__raises(self):
        self.assertRaises(ValueError, protocol.TestSmallMessage, type_=20)

    def test_compressed_message_bits__short_test_type__output_correct(self):
        message = protocol.TestSmallMessage(
            type_=protocol.TestSmallMessageType.SHORT_TEST
        )
        self.assertEqual(message.compressed_message_bits[0:16].bin, "0000001100000000")
        self.assertEqual("143 253 222 433 244", message.to_keycode())

    def test_compressed_message_bits__oqc_test_type__output_correct(self):
        message = protocol.TestSmallMessage(
            type_=protocol.TestSmallMessageType.OQC_TEST
        )
        self.assertEqual(message.compressed_message_bits[0:16].bin, "0000001100000001")
        self.assertEqual("124 233 243 522 424", message.to_keycode())


class TestMaintenanceSmallMessage(TestCase):
    def test_init__invalid_type__raises(self):
        self.assertRaises(
            ValueError,
            protocol.MaintenanceSmallMessage,
            type_=3,
            secret_key=b"\xab" * 16,
        )

    def test_compressed_message_bits__wipe_state_0_type__output_correct(self):
        message = protocol.MaintenanceSmallMessage(
            type_=protocol.MaintenanceSmallMessageType.WIPE_STATE_0,
            secret_key=b"\xab" * 16,
        )
        self.assertEqual(message.compressed_message_bits[0:16].bin, "0000001110000000")
        self.assertEqual("122 553 254 245 542", message.to_keycode())

    def test_compressed_message_bits__wipe_state_1_type__output_correct(self):
        message = protocol.MaintenanceSmallMessage(
            type_=protocol.MaintenanceSmallMessageType.WIPE_STATE_1,
            secret_key=b"\xab" * 16,
        )
        self.assertEqual(message.compressed_message_bits[0:16].bin, "0000001110000001")
        self.assertEqual("154 434 534 522 522", message.to_keycode())

    def test_compressed_message_bits__wipe_ids_all_type__output_correct(self):
        message = protocol.MaintenanceSmallMessage(
            type_=protocol.MaintenanceSmallMessageType.WIPE_IDS_ALL,
            secret_key=b"\xab" * 16,
        )
        self.assertEqual(message.compressed_message_bits[0:16].bin, "0000001110000010")
        self.assertEqual("153 224 344 342 322", message.to_keycode())


class TestAddCreditSmallMessage(TestCase):
    def test_init__invalid_too_large_id__raises(self):
        self.assertRaises(
            ValueError,
            protocol.AddCreditSmallMessage,
            id_=68719476721,
            days=1,
            secret_key=b"\xab" * 16,
        )

    def test_init__negative_id__raises(self):
        self.assertRaises(
            ValueError,
            protocol.AddCreditSmallMessage,
            id_=-1,
            days=1,
            secret_key=b"\xab" * 16,
        )

    def test_init__invalid_days__raises(self):
        self.assertRaises(
            ValueError,
            protocol.AddCreditSmallMessage,
            id_=0,
            days=406,
            secret_key=b"\xab" * 16,
        )

    def test_compressed_message_bits__add_1_day_message__output_correct(self):
        message = protocol.AddCreditSmallMessage(id_=0, days=1, secret_key=b"\xab" * 16)
        self.assertEqual(message.compressed_message_bits[0:16].bin, "0000000000000000")
        self.assertEqual("133 232 343 432 255", message.to_keycode())

    def test_compressed_message_bits__add_180_day__output_correct(self):
        message = protocol.AddCreditSmallMessage(
            id_=1, days=180, secret_key=b"\xab" * 16
        )
        self.assertEqual(message.compressed_message_bits[0:16].bin, "0000010010110011")
        self.assertEqual("122 425 324 553 555", message.to_keycode())

    def test_compressed_message_bits__add_181_day__output_correct(self):
        message = protocol.AddCreditSmallMessage(
            id_=10, days=181, secret_key=b"\xab" * 16
        )
        self.assertEqual(message.compressed_message_bits[0:16].bin, "0010100010110100")
        self.assertEqual("132 353 543 455 243", message.to_keycode())

    def test_compressed_message_bits__add_405_day__output_correct(self):
        message = protocol.AddCreditSmallMessage(
            id_=125, days=405, secret_key=b"\xab" * 16
        )
        self.assertEqual(message.compressed_message_bits[0:16].bin, "1111010011111110")
        self.assertEqual("132 335 454 524 233", message.to_keycode())

    def test_compressed_message_bits__large_message_id__output_correct(self):
        message = protocol.AddCreditSmallMessage(
            id_=65234, days=405, secret_key=b"\xab" * 16
        )
        self.assertEqual(message.compressed_message_bits[0:16].bin, "0100100011111110")
        self.assertEqual("143 235 545 435 454", message.to_keycode())

    def test_compressed_message_bits__add_credit_unlock__output_correct(self):
        message = protocol.AddCreditSmallMessage(
            id_=1, days=protocol.SmallMessage.UNLOCK_FLAG, secret_key=b"\xab" * 16
        )
        self.assertEqual(message.compressed_message_bits[0:16].bin, "0000010011111111")
        self.assertEqual("134 435 355 535 552", message.to_keycode())


class TestSetCreditSmallMessage(TestCase):
    def test_init__invalid_days__raises(self):
        self.assertRaises(
            ValueError,
            protocol.SetCreditSmallMessage,
            id_=0,
            days=1185,  # 1184 is set credit max
            secret_key=b"\xab" * 16,
        )

    def test_compressed_message_bits__set_1_day_message__output_correct(self):
        message = protocol.SetCreditSmallMessage(id_=0, days=1, secret_key=b"\xab" * 16)
        self.assertEqual(
            message.compressed_message_bits[0:16].bin, "000000" + "10" + "00000000"
        )
        self.assertEqual("142 525 352 252 234", message.to_keycode())

    def test_compressed_message_bits__set_92_day_message__output_correct(self):
        message = protocol.SetCreditSmallMessage(
            id_=1, days=92, secret_key=b"\xab" * 16
        )
        self.assertEqual(
            message.compressed_message_bits[0:16].bin, "000001" + "10" + "01011010"
        )
        self.assertEqual("124 445 543 325 325", message.to_keycode())

    def test_compressed_message_bits__set_lock_message__output_correct(self):
        message = protocol.SetCreditSmallMessage(
            id_=1542, days=0, secret_key=b"\xab" * 16
        )
        self.assertEqual(
            message.compressed_message_bits[0:16].bin, "000110" + "10" + "11111110"
        )
        self.assertEqual("154 445 453 335 225", message.to_keycode())

    def test_compressed_message_bits__set_unlock_message__output_correct(self):
        message = protocol.SetCreditSmallMessage(
            id_=6573, days=protocol.SmallMessage.UNLOCK_FLAG, secret_key=b"\xab" * 16
        )
        self.assertEqual(
            message.compressed_message_bits[0:16].bin, "101101" + "10" + "11111111"
        )
        self.assertEqual("143 534 323 324 344", message.to_keycode())


class TestUnlockSmallMessage(TestCase):
    def test_compressed_message_bits__unlock__output_correct(self):
        message = protocol.UnlockSmallMessage(id_=1, secret_key=b"\xab" * 16)
        self.assertEqual(message.compressed_message_bits[0:16].bin, "0000010011111111")
        self.assertEqual("134 435 355 535 552", message.to_keycode())


class TestSmallMessage(TestCase):
    def test_to_keycode__without_prefix__raises(self):
        message = protocol.SmallMessage(
            100, protocol.SmallMessageType.ADD_CREDIT, 10, b"\xff" * 16
        )
        self.assertRaises(ValueError, message.to_keycode, prefix="")

    def test_to_keycode__without_required_keys__raises(self):
        message = protocol.SmallMessage(
            100, protocol.SmallMessageType.ADD_CREDIT, 10, b"\xff" * 16
        )
        self.assertRaises(
            KeyError, message.to_keycode, prefix="*", key_dict={0: "a", 1: "b", 2: "c"}
        )

    def test_to_keycode__with_simple_message___expected_value_returned(self):
        message = protocol.SmallMessage(
            100, protocol.SmallMessageType.ADD_CREDIT, 10, b"\xff" * 16
        )
        self.assertEqual(
            "430 202 200 300 100",
            message.to_keycode(
                prefix="4", separator=" ", key_dict={0: "0", 1: "1", 2: "2", 3: "3"}
            ),
        )
        self.assertEqual("152 424 422 522 322", message.to_keycode())

    def test_str__with_simple_message___expected_value_returned(self):
        message = protocol.SmallMessage(
            100, protocol.SmallMessageType.ADD_CREDIT, 10, b"\xff" * 16
        )
        self.assertEqual("152 424 422 522 322", str(message))

    def test_set_credit__possible_collision__message_is_not_created(self):
        self.assertRaises(
            ValueError,
            protocol.SetCreditSmallMessage,
            id_=63,
            days=1,
            secret_key=b"\xff" * 16,
        )

    def test_init__long_key_inputs_accepted__uses_siphash_required_bytes(self):
        xmessage = protocol.SmallMessage(
            343, protocol.SmallMessageType.ADD_CREDIT, 20, b"\xfb\x00\xa5\x98" * 4
        )
        ymessage = protocol.SmallMessage(
            343,
            protocol.SmallMessageType.ADD_CREDIT,
            20,
            b"\xfb\x00\xa5\x98" * 4 + b"\x02\x03\x04\x05" * 4,
        )
        self.assertEqual(str(xmessage), str(ymessage))
        self.assertEqual(repr(xmessage), repr(ymessage))
        self.assertEqual(xmessage.to_keycode(), ymessage.to_keycode())

    def test_repr__simple_message__expected_snippets_present(self):
        repred = repr(
            protocol.SmallMessage(
                100, protocol.SmallMessageType.ADD_CREDIT, 10, b"\xff" * 16
            )
        )
        self.assertIn("SmallMessage", repred)
        repred = repr(
            protocol.SmallMessage(
                100, protocol.SmallMessageType.SET_CREDIT, 10, b"\xff" * 16
            )
        )
        self.assertIn("SmallMessage", repred)
        repred = repr(
            protocol.SmallMessage(
                100, protocol.SmallMessageType.MAINTENANCE_TEST, 10, b"\xff" * 16
            )
        )
        self.assertIn("SmallMessage", repred)
