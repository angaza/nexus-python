# Nexus Keycode: Python (Preview Release)

This package allows you to encode Nexus Keycodes.

This is a preview release. We are working on polishing some of the rough edges in
advance of a production-ready release at the end of Q1 2020. Most notably, this release
currently only supports Python 2.

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

This package uses a form of [semantic versioning](semver.org). The version
number is comprised of three components: MAJOR.MINOR.PATCH

Major version numbers represent breaking changes in the keycode protocol
itself. This is the only version number that is relevant to keycodes
themselves. For example, any keycode generated any version 1.X.Y of this
encoder will be valid on any version 1.X.Y of the [embedded decoder](https://github.com/angaza/nexus-keycode-embedded).

Minor version numbers represent breaking internal API changes. You may need
to modify your code to accomodate these changes.

Patch version numbers represent changes that are fully backward compatible.

## Usage

Generate keycodes for the full and small keypad protocols.

### Full Protocol

Add Credit

```python
secret_key = "\xde\xad\xbe\xef" * 4
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

### Small Protocol

Add Credit

```python
SECRET_KEY = "\xde\xad\xbe\xef" * 4
AddCreditSmallMessage(id_=42, days=7, secret_key=secret_key).to_keycode()
# outputs 135 242 422 455 244
```

Update Credit

```python
UpdateCreditSmallMessage(id_=43, days=14, secret_key=secret_key).to_keycode()
# outputs 145 222 453 233 453
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

Wipe
```python
MaintenanceSmallMessage(type_=MaintenanceSmallMessageType.WIPE_IDS_ALL, secret_key=secret_key).to_keycode()
# outputs 122 324 235 545 545
```
