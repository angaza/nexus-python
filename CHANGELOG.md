# Change Log

Version 1.0.0 *(2020-02-13)*
----------------------------

Initial release.

Version 1.1.0 *(2020-07-31)*
----------------------------

The Nexus Keycode encoder library now supports both Python 2.7 as well as 3.6
and later.

Version 2.2.0 *(2021-03-23)*
----------------------------

This version number updated to correspond with `NEXUS_GLOBAL_VERSION`
package identifier.

The 'small' protocol supports a passthrough constructor, allowing arbitrary
26-bit messages to be generated. These passthrough messages are not
interpreted by the keycode protocol on the device firmware, but passed
to application specific interpretations/handlers.

Build an 'small extended' keycode protocol fthat encapsulates its messages
in the 'small 'passthrough' message type.

Introduce a "SET CREDIT + WIPE RESTRICTED FLAG" function in this 'small
extended' protocol.
