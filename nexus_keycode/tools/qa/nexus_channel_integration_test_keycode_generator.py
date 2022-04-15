"""
Generates keycodes for Nexus Channel integration test plan v1.0.0:
https://docs.google.com/spreadsheets/d/16Xqwv0GToPna8NplMlhTdjdKZ40POz6arU9yW4_S_Xo/edit
"""

import csv
import datetime

from nexus_keycode.tools.generate_full_keycode import (
    VALID_NXC_MESSAGE_TYPES,
    VALID_NXK_MESSAGE_TYPES,
    create_full_channel_message,
    create_full_credit_message,
)

# device definitions; before running, update this section!
# WARNING: assumes that Nexus Keycode and Channel secret keys are identical!
NXC_CONTROLLER_A = dict(
    nx_device_id=243456100, nxk_nxc_sym_key="\xaa" * 16, nxk_count=30, nxc_count=30
)
NXC_CONTROLLER_B = dict(
    nx_device_id=243456209, nxk_nxc_sym_key="\xbb" * 16, nxk_count=30, nxc_count=30
)
NXC_ACCESSORY_A = dict(
    nx_device_id=243458007, nxk_nxc_sym_key="\xcc" * 16, nxk_count=30, nxc_count=30
)
NXC_ACCESSORY_B = dict(
    nx_device_id=243457900, nxk_nxc_sym_key="\xdd" * 16, nxk_count=30, nxc_count=30
)

# test definition according to the linked test plan document above
TEST_STEPS = [
    dict(step_number=2, device=NXC_CONTROLLER_A, keycode_type="UNLINK"),
    dict(step_number=2, device=NXC_CONTROLLER_B, keycode_type="UNLINK"),
    dict(step_number=3, device=NXC_CONTROLLER_A, keycode_type="SET", hours=0),
    dict(step_number=3, device=NXC_CONTROLLER_B, keycode_type="SET", hours=0),
    dict(step_number=7, device=NXC_CONTROLLER_A, keycode_type="ADD", hours=24),
    dict(
        step_number=8,
        device=NXC_CONTROLLER_A,
        keycode_type="LINK",
        nxc_accessory=NXC_ACCESSORY_A,
    ),
    dict(
        step_number=9,
        device=NXC_CONTROLLER_A,
        keycode_type="LINK",
        nxc_accessory=NXC_ACCESSORY_B,
    ),
    dict(step_number=12, device=NXC_CONTROLLER_A, keycode_type="UNLOCK"),
    dict(step_number=16, device=NXC_CONTROLLER_A, keycode_type="SET", hours=0),
    dict(
        step_number=17,
        device=NXC_CONTROLLER_A,
        keycode_type="LINK",
        nxc_accessory=NXC_ACCESSORY_A,
    ),
    dict(step_number=18, device=NXC_CONTROLLER_A, keycode_type="ADD", hours=24),
    dict(
        step_number=21,
        device=NXC_CONTROLLER_B,
        keycode_type="LINK",
        nxc_accessory=NXC_ACCESSORY_A,
    ),
    dict(
        step_number=23,
        device=NXC_CONTROLLER_B,
        keycode_type="LINK",
        nxc_accessory=NXC_ACCESSORY_B,
    ),
    dict(step_number=25, device=NXC_CONTROLLER_B, keycode_type="ADD", hours=24),
]


def create_keycodes(steps):
    """Consume a list of dicts, each one describing a test step
    that requires a keycode to be generated. Each dict should
    include `step_number`, `device`, `keycode_type`, and any other
    kwargs required to generate the token described in the step.

    Return a list of dicts including the keycode as well as state
    at the time of generating it, suitable for output or analysis."""
    keycodes = list()
    for step in steps:
        # common message-generation parameters
        keycode_type = step["keycode_type"]
        key = step["device"]["nxk_nxc_sym_key"]

        # begin to populate output dict
        keycode_data = dict(
            step_number=step["step_number"],
            nexus_id=step["device"]["nx_device_id"],
            secret_key=step["device"]["nxk_nxc_sym_key"],
        )

        # generate keycode
        message = None
        if keycode_type in VALID_NXK_MESSAGE_TYPES:
            # activation / Nexus Keycode message
            msg_args = dict(
                msg_id=step["device"]["nxk_count"],
                hours=step.get("hours", None),
                secret_key=key,
            )

            message = create_full_credit_message(msg_type=keycode_type, **msg_args)

            # increment NXK count
            step["device"]["nxk_count"] = step["device"]["nxk_count"] + 1

            # update output dict
            keycode_data.update(msg_args)
        elif keycode_type in VALID_NXC_MESSAGE_TYPES:
            # origin command / Nexus Channel message
            msg_args = dict(controller_command_count=step["device"]["nxc_count"])

            # update msg_args with accessory data for link command
            if keycode_type == "LINK":
                accessory = step["nxc_accessory"]
                msg_args.update(
                    dict(
                        accessory_command_count=accessory["nxc_count"],
                        accessory_sym_key=accessory["nxk_nxc_sym_key"],
                    )
                )

                # update accessory NXC count and add to output dict
                keycode_data.update(
                    dict(
                        accessory_nx_id=accessory["nx_device_id"],
                        accessory_command_count=accessory["nxc_count"],
                        controller_command_count=step["device"]["nxc_count"],
                    )
                )
                accessory["nxc_count"] = accessory["nxc_count"] + 1

            message = create_full_channel_message(
                keycode_type, controller_sym_key=key, **msg_args
            )
            # increment NXC count
            step["device"]["nxc_count"] = step["device"]["nxc_count"] + 1

            # update output dict
            keycode_data.update(msg_args)
        else:
            raise ValueError(u"unexpected keycode_type in TEST_STEPS")

        assert message

        keycode_data.update(
            dict(keycode_type=keycode_type, keycode=message.to_keycode())
        )
        keycodes.append(keycode_data)

    return keycodes


def print_keycodes(keycodes):
    # print ordered headers to CSV outfile
    now_utc_str = datetime.datetime.utcnow().strftime(u"%m%d%Y_%Hh%Mm%Ss")
    out_filename = now_utc_str + u"_UTC_nxc_integration_test_v1-0-0_keycodes.csv"
    with open(u"{}".format(out_filename), "w") as outfile:
        writer = csv.DictWriter(
            outfile,
            fieldnames=[
                "step_number",
                "controller_nx_id",
                "keycode_type",
                "accessory_nx_id",
                "keycode",
                "controller_command_count",
                "accessory_command_count",
            ],
        )
        writer.writeheader()

        for keycode in keycodes:
            writer.writerow(
                {
                    "step_number": keycode["step_number"],
                    "controller_nx_id": keycode["nexus_id"],
                    "keycode_type": keycode["keycode_type"],
                    "accessory_nx_id": keycode.get("accessory_nx_id", None),
                    "keycode": keycode["keycode"],
                    "controller_command_count": keycode.get(
                        "controller_command_count", None
                    ),
                    "accessory_command_count": keycode.get(
                        "accessory_command_count", None
                    ),
                }
            )


if __name__ == "__main__":
    print_keycodes(create_keycodes(TEST_STEPS))
