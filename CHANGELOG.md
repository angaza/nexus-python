# Change Log

Version 1.0.0 *(2020-02-13)*
----------------------------

Initial release.

Version 1.1.0 *(2020-07-31)*
----------------------------

The Nexus Keycode encoder library now supports both Python 2.7 as well as 3.6
and later.

Version 1.2.0 *(2020-11-10)*
----------------------------

Introduce a new type of command (as a special subset of `SET CREDIT` type)
which allows setting of firmware-defined 'custom' flags.

Devices using the latest version of the Nexus Keycode embedded library
support a "restricted flag". Embedded code can set this flag, and a special
"Wipe Restricted" keycode (implemented as a `CustomCommand`) can unset this
flag.

An example use case: A productive use PAYG appliance like a water pump may be
installed in an inaccessible location and controlled by a separate pump
controller. In order to ensure that a pump will only work with one pump
controller, the device manufacturer can implement logic that uses the
"restricted flag" to ensure the controller cannot interact with other pumps.
If the controller needs to be replaced, then the "wipe restricted" keycode can
be entered to allow another pump controller to be linked to the pump.

Version 2.2.0 *(2021-03-23)*
----------------------------

This version number updated to correspond with `NEXUS_GLOBAL_VERSION`
package identifier.

The 'small' protocol supports a passthrough constructor, allowing arbitrary
26-bit messages to be generated. These passthrough messages are not
interpreted by the keycode protocol on the device firmware, but passed
to application specific interpretations/handlers.

Build an 'small extended' keycode protocol that encapsulates its messages
in the 'small passthrough' message type.

Introduce a "SET CREDIT + WIPE RESTRICTED FLAG" function in this 'small
extended' protocol.

Version 2.3.0 *(2021-8-26)*
----------------------------
The ability to generate passthrough keycodes has been added.