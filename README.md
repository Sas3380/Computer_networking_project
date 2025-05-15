# Making UDP Reliable Communication - Stop-and-Wait and Go-Back-N ARQ

## Overview
This project demonstrates reliable data transmission over UDP by implementing two protocols:
- **Stop-and-Wait ARQ** (Automatic Repeat reQuest)
- **Go-Back-N ARQ**

UDP by default does not guarantee packet delivery or ordering. These protocols add reliability by using sequence numbers, acknowledgments (ACKs), timeouts, and retransmissions.

---

## How It Works

### Stop-and-Wait ARQ
- Sender transmits one packet at a time.
- Waits for an ACK from the receiver before sending the next packet.
- If no ACK is received within a timeout period, the sender retransmits the packet.
- Ensures reliable and ordered delivery but can be slow due to waiting after each packet.

### Go-Back-N ARQ
- Sender transmits multiple packets up to a window size without waiting for ACKs.
- Receiver only accepts packets in order; out-of-order packets are discarded.
- If a timeout occurs waiting for an ACK, the sender retransmits all unacknowledged packets starting from the oldest.
- More efficient than Stop-and-Wait as it keeps the network pipeline full.

---

## Files
- `sender.py` : Implements the sender logic. Supports both Stop-and-Wait and Go-Back-N protocols (selectable via a flag).
- `receiver.py` : Implements the receiver logic. Simulates packet loss and sends ACKs accordingly.

---

## Usage
1. Run the receiver first:
   ```bash
   python receiver.py
   
   python sender.py
