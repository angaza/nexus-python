# Nexus Python

This repository contains server-side code for managing devices using Nexus
protocols, including Nexus Keycode.

Learn more about about Angaza Nexus [here](https://angaza.github.io/nexus)!

## Installation

Nexus Keycode will be available on PyPI. Installation will be as simple as:

```shell
pip install nexus-keycode
```

This package comes with a full suite of unit tests, which you can run like so:

```shell
nose2
```

## Versioning

### Package Version

This package uses a form of [semantic versioning](semver.org). The version
number is comprised of three components: MAJOR.MINOR.PATCH

Major version numbers represent breaking internal API changes. You may need
to modify your code to accomodate these changes. Minor version numbers
represent feature additions or changes that do not break the library's API,
and are fully backward compatible. Patch version numbers represent bug fixes
or minor changes that do not add additional functionality.

The package version is independent of the Nexus System Version that the
package supports.

## Usage

Generate keycodes for the full and small keypad protocols.

### Full Protocol

Add Credit

```python
secret_key = b"\xde\xad\xbe\xef" * 4
message = FullMessage.add_credit(
    id_=42, hours=24 * 7, secret_key=secret_key
).to_keycode()
# outputs *599 791 493 194 43#
```

Set Credit

```python
message = FullMessage.set_credit(
    id_=43, hours=24 * 10, secret_key=secret_key
).to_keycode()
# outputs *682 070 357 093 12#
```

Unlock

```python
message = FullMessage.unlock(id_=44, secret_key=secret_key).to_keycode()
# outputs *578 396 697 305 45#
```

Wipe
```python
message = FullMessage.wipe_state(
    id_=45, flags=FullMessageWipeFlags.WIPE_IDS_ALL, secret_key=secret_key
).to_keycode()
# outputs *356 107 776 307 38#
```

Enabled/Disabled Test
```python
message = FactoryFullMessage.oqc_test().to_keycode()
# outputs *577 043 3#
```

Factory Test
```python
message = FactoryFullMessage.allow_test().to_keycode()
# outputs *406 498 3#
```

Display PAYG ID
```python
message = FactoryFullMessage.display_payg_id().to_keycode()
# outputs *634 776 5#
```


#### Nexus Channel Origin Commands

These commands generate commands that are accepted by [Nexus Channel](https://nexus.angaza.com/channel.html)
"Controller" devices using the "Full Protocol". Typically, these are used
to manage the secured link state of "Controller" and "Accessory" devices.

See `protocols/channel_origin_commands.py` for a full list of command types
to generate.

Create Nexus Channel Secured Link
```python
from nexus_keycode.protocols.full import FactoryFullMessage
from nexus_keycode.protocols.channel_origin_commands import ChannelOriginAction

message = FactoryFullMessage.passthrough_channel_origin_command(
	ChannelOriginAction.LINK_ACCESSORY_MODE_3,
    accessory_nexus_id=0x000200003322,
    controller_command_count=5,
    accessory_command_count=2,
    accessory_sym_key=b"\xAB" * 16,
    controller_sym_key=b"\xCD" * 16,
)
message.to_keycode()
# outputs *819 079 821 151 997 4#

```

Delete Nexus Channel Secured Link (Single Accessory Link)
```python
from nexus_keycode.protocols.full import FactoryFullMessage
from nexus_keycode.protocols.channel_origin_commands import ChannelOriginAction

message = FactoryFullMessage.passthrough_channel_origin_command(
	ChannelOriginAction.UNLINK_ACCESSORY,
    accessory_nexus_id=0x000200003322,
    controller_command_count=6,
    controller_sym_key=b"\xCD" * 16,
)
message.to_keycode()
# outputs *812 094 159 7#
```

Delete Nexus Channel Secured Link (All Accessory Links)
```python
from nexus_keycode.protocols.full import FactoryFullMessage
from nexus_keycode.protocols.channel_origin_commands import ChannelOriginAction

message = FactoryFullMessage.passthrough_channel_origin_command(
	ChannelOriginAction.UNLINK_ALL_ACCESSORIES,
    controller_command_count=7,
    controller_sym_key=b"\xCD" * 16,
)

message.to_keycode()
# outputs *810 003 592 81#
```

### Small Protocol

Add Credit

```python
SECRET_KEY = b"\xde\xad\xbe\xef" * 4
AddCreditSmallMessage(id_=42, days=7, secret_key=secret_key).to_keycode()
# outputs 135 242 422 455 244
```

Set Credit

```python
SetCreditSmallMessage(id_=44, days=10, secret_key=secret_key).to_keycode()
# outputs 142 522 332 234 533
```

Unlock

```python
UnlockSmallMessage(id_=45, secret_key=secret_key).to_keycode()
# outputs 152 323 254 454 322
```

Wipe Message IDs

```python
MaintenanceSmallMessage(type_=MaintenanceSmallMessageType.WIPE_IDS_ALL, secret_key=secret_key).to_keycode()
# outputs 122 324 235 545 545
```

Wipe Custom "Restricted Flag"

```python
CustomCommandSmallMessage(id_=46, type_=CustomCommandSmallMessageType.WIPE_RESTRICTED_FLAG, secret_key=secret_key).to_keycode()
# outputs 154 545 254 542 523
```

Set Credit + Wipe Custom "Restricted Flag"

```python
# Creating a message of this type *may* lead to a 'message ID collision',
# meaning the message cannot be unambiguously interpreted by the unit
# (it might be mistaken for a different message if entered into the unit).
# If this occurs, an `ExtendedSmallMessageIdInvalidError` error will be raised.
# Typically incrementing the ID by 1 and creating the message again will
# succeed.

In [25]: ExtendedSmallMessage(id_=50, days=84, type_=ExtendedSmallMessageType.SET_CREDIT_WIPE_RESTRICTED_FLAG, secret_key=secret_key).to_keycode()
# raises `ExtendedSmallMessageIdInvalidError: ID 50 yields MAC collision, next valid ID is 51.`

In [26]: ExtendedSmallMessage(id_=51, days=84, type_=ExtendedSmallMessageType.SET_CREDIT_WIPE_RESTRICTED_FLAG, secret_key=secret_key).to_keycode()
# outputs 145 545 244 442 435
```
