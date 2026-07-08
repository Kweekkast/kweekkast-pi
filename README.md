# kweekkast-pi
This repository houses the services for the two Raspberry Pis in the Kweekkast project. It contains four modules:
- **kweekkast-core**: service for the core Raspberry Pi.
- **kweekkast-net**: service for the network Raspberry Pi.
- **kweekkast-common**: shared code between the two Pis.
- **kweekkast-tests**: tests for the services (root module).

Python packages and modules are managed using [**uv**](https://github.com/astral-sh/uv). Consult the tool’s [documentation](https://docs.astral.sh/uv/) on how to install dependencies and run the modules.

## Communication
The complete system is split into three main layers:
- [**kweekkast-web (web)**](https://github.com/Kweekkast/kweekkast-web) (Django web app)
- **kweekkast-net (net)** (network Raspberry Pi)
- **kweekkast-core (core)** (core Raspberry Pi)

The web application is responsible for user interaction, schedules, manual control, and data storage. The net-Pi acts as the network bridge: it talks to Django over HTTPS and forwards data to/from the core-Pi over UART.

> web ⇄ HTTPS/JSON ⇄ net ⇄ UART/binary protocol ⇄ core

The core-Pi is responsible for local hardware interaction: actuator control, sensor aggregation, and camera capture.

> core ← ESP32 modules (sensors)  
> core → actuators (pumps and lights)  
> core ⇄ cameras

Two main communication flows exist:
1. Telemetry and images to Django
    - The core-Pi collects sensor readings from the ESP32 modules and images from the cameras.
    - The core-Pi sends telemetry snapshots and images to the net-Pi over the UART binary protocol.
    - The net-Pi uploads telemetry to `/api/input` and images to `/api/images`.
2. Actuator configuration to the physical system
    - Django determines the desired state for each module's `pump`, `day`, and `grow` actuator based on schedules and manual user input.
    - The net-Pi polls `/api/output` on a configurable interval.
    - Django returns a signed desired-state configuration.
    - The net-Pi forwards this config to the core-Pi over UART.
    - The core-Pi verifies the signature and applies the actuator states.

### Binary protocol
> core → net: telemetry frames  
> core → net: image chunk frames  
> net → core: signed actuator config frames

Features of the binary protocol:
- Framing with COBS encoding allows messages to be separated reliably
- CRC32 checksums for detecting corrupted frames
- Receiver resynchronization after bad data
- Configs are versioned to protect against replay attacks
- Config expiry results in a default safe state on the core-Pi
- Configs are signed to prevent tampering by a compromised net-Pi
- No acknowledgements or retries: communication is unidirectional in both directions even though the UART link is physically bidirectional

Because of the unidirectional nature of the protocol, delivery is not guaranteed. This is acceptable: loss of a sensor batch, image, or delayed configuration retrieval is not a problem. The sending and polling rates can be adjusted accordingly.

Configuration messages are signed by Django and verified on the core-Pi. This is intended to keep the physical system safe if the network-facing Pi is compromised: the net-Pi can forward configurations, but it cannot create valid actuator commands by itself.

## Deployment
The services are configured using **environment variables**:
- `core.env` (see `deploy/core/core.env.example`)
- `net.env` (see `deploy/net/net.env.example`)

Suggested OS: **Raspberry Pi OS Lite (64-bit)**

Suggested file locations:

| Content           | Suggested location                                |
|-------------------|---------------------------------------------------|
| This repository   | /opt/kweekkast/app or /opt/kweekkast/kweekkast-pi |
| `deploy.sh` files | /opt/kweekkast                                    |
| `.env` files      | /etc/kweekkast                                    |
| `.service` files  | /etc/systemd/system                               |

### Automation
Automatically start services on boot (and restart on failure):
- `systemctl daemon-reload`
- `systemctl enable kweekkast-core` or `systemctl enable kweekkast-net`
- `systemctl start kweekkast-core` or `systemctl start kweekkast-net`

Automate deployment:
- The `deploy.sh` scripts will automatically pull the latest changes and restart the application.
- Change the Git branch to deploy from in the script if necessary.
- If this repository is private, ensure the host gains access to it (using an SSH GitHub deploy key for example).

### Hardening
A non-exhaustive list of recommended security measures:
- Disable all connectivity on the hosts except for the wired network interface on the network Raspberry Pi.
- Disable root login.
- Create a service user with limited privileges to run the app.
- Follow SSH best security practices (prefer keys to complex passwords).