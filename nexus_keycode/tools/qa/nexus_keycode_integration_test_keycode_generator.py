"""
Generates keycodes for Nexus Keycode integration test plan v1.4.0:
https://docs.google.com/spreadsheets/d/1gx3SrzXoCtfBLMxT6rKwwDRiCZt9yCa7SIYjoyuHug8/edit#gid=674470677

To use,

1. update data for devices under test in DEVICE DATA DEFINITION section below
2. from this directory, `python nexus_keycode_integration_test_keycode_generator.py`
3. open the CSV that was generated
"""

import csv
import datetime

from nexus_keycode.tools.generate_full_keycode import create_full_credit_message

# DEVICE DATA DEFINITION; before running, update this section!
NX_KEYCODE_TEST_DEVICE = dict(
    nx_device_id=123456789, sym_key="\xaa" * 16, message_id=30
)

# test definition according to the linked test plan document above
TEST_STEPS = [
    dict(step_number=1.1, keycode_type="ADD", hours=1),
    dict(step_number=1.2, keycode_type="ADD", hours=168),
    dict(step_number=1.3, keycode_type="UNLOCK"),
    dict(step_number=1.4, keycode_type="SET", hours=0),
    dict(step_number=2.1, keycode_type="ADD", hours=240),
    dict(step_number=3.1, keycode_type="ADD", hours=48),
]


def create_keycodes(steps):
    """Consume a list of dicts, each one describing a test step
    that requires a keycode to be generated. Each dict should
    include `step_number`, `keycode_type`, and any other
    kwargs required to generate the keycode described in the step.

    Return a list of dicts including the keycode as well as state
    at the time of generating it, suitable for output or analysis."""
    keycodes = list()
    for step in steps:
        # begin to populate output dict
        keycode_data = dict(
            step_number=step["step_number"],
            nexus_id=NX_KEYCODE_TEST_DEVICE["nx_device_id"],
        )

        # generate keycode
        message = None
        msg_args = dict(
            msg_id=NX_KEYCODE_TEST_DEVICE["message_id"],
            msg_type=step["keycode_type"],
            secret_key=NX_KEYCODE_TEST_DEVICE["sym_key"],
            hours=step.get("hours", None),
        )

        message = create_full_credit_message(**msg_args)
        assert message

        # increment message ID
        NX_KEYCODE_TEST_DEVICE["message_id"] = NX_KEYCODE_TEST_DEVICE["message_id"] + 1

        # update output dict
        keycode_data.update(msg_args)
        keycode_data.update(dict(keycode=message.to_keycode()))

        keycodes.append(keycode_data)

    return keycodes


def print_keycodes(keycodes):
    # print ordered headers to CSV outfile
    now_utc_str = datetime.datetime.utcnow().strftime(u"%m%d%Y_%Hh%Mm%Ss")
    out_filename = now_utc_str + u"_UTC_nxk_integration_test_v1-4-0_keycodes.csv"
    with open(u"{}".format(out_filename), "w") as outfile:
        writer = csv.DictWriter(
            outfile,
            fieldnames=[
                "step_number",
                "nexus_id",
                "keycode_type",
                "message_id",
                "hours",
                "keycode",
            ],
        )
        writer.writeheader()

        for keycode in keycodes:
            writer.writerow(
                {
                    "step_number": keycode["step_number"],
                    "nexus_id": keycode["nexus_id"],
                    "keycode_type": keycode["msg_type"],
                    "message_id": keycode["msg_id"],
                    "hours": keycode["hours"],
                    "keycode": keycode["keycode"],
                }
            )


if __name__ == "__main__":
    print_keycodes(create_keycodes(TEST_STEPS))
