from unittest import TestCase

from nexus_keycode.protocols.full import (
    FactoryFullMessage,
    FullMessage,
    FullMessageWipeFlags,
)
from nexus_keycode.protocols.small import (
    AddCreditSmallMessage,
    MaintenanceSmallMessage,
    MaintenanceSmallMessageType,
    SetCreditSmallMessage,
    UnlockSmallMessage,
)


class TestREADME(TestCase):
    SECRET_KEY = b"\xde\xad\xbe\xef" * 4

    def test_add_credit__full__ok(self):
        message = FullMessage.add_credit(
            id_=42, hours=24 * 7, secret_key=self.SECRET_KEY
        )
        self.assertEqual("*599 791 493 194 43#", message.to_keycode())

    def test_set_credit__full__ok(self):
        message = FullMessage.set_credit(
            id_=43, hours=24 * 10, secret_key=self.SECRET_KEY
        )
        self.assertEqual("*682 070 357 093 12#", message.to_keycode())

    def test_unlock__full__ok(self):
        message = FullMessage.unlock(id_=44, secret_key=self.SECRET_KEY)
        self.assertEqual("*578 396 697 305 45#", message.to_keycode())

    def test_wipe__full__ok(self):
        message = FullMessage.wipe_state(
            id_=45, flags=FullMessageWipeFlags.WIPE_IDS_ALL, secret_key=self.SECRET_KEY
        )
        self.assertEqual("*356 107 776 307 38#", message.to_keycode())

    def test_oqc_test__full__ok(self):
        message = FactoryFullMessage.oqc_test()
        self.assertEqual("*577 043 3#", message.to_keycode())

    def test_factory_test__full__ok(self):
        message = FactoryFullMessage.allow_test()
        self.assertEqual("*406 498 3#", message.to_keycode())

    def test_display_payg_id__full__ok(self):
        message = FactoryFullMessage.display_payg_id()
        self.assertEqual("*634 776 5#", message.to_keycode())

    def test_add_credit__small__ok(self):
        message = AddCreditSmallMessage(id_=42, days=7, secret_key=self.SECRET_KEY)
        self.assertEqual("135 242 422 455 244", message.to_keycode())

    def test_set_credit__small__ok(self):
        message = SetCreditSmallMessage(id_=44, days=10, secret_key=self.SECRET_KEY)
        self.assertEqual("142 522 332 234 533", message.to_keycode())

    def test_unlock__small__ok(self):
        message = UnlockSmallMessage(id_=45, secret_key=self.SECRET_KEY)
        self.assertEqual("152 323 254 454 322", message.to_keycode())

    def test_wipe__small__ok(self):
        message = MaintenanceSmallMessage(
            type_=MaintenanceSmallMessageType.WIPE_IDS_ALL, secret_key=self.SECRET_KEY
        )
        self.assertEqual("122 324 235 545 545", message.to_keycode())
