# RP2040 (Raspberry Pi Pico) - IR learn (RX) + transmit (TX) for a universal-remote app.
# MicroPython
#
#   IR receiver OUT -> GP0  (VCC 3V3, GND)
#   IR LED (via NPN transistor): GP15 -> 1k -> base ; VBUS(5V) -> LED -> 47R -> collector ; emitter -> GND
#
# RX (capture, used by the web app over Web Serial):
#   On every captured frame it prints a RAW on/off timing pattern (microseconds):
#       RAW(38000): 9000,4500,560,560, ...
#   plus a "# NEC ..." label line when it decodes.
#
# TX (used by the Android app over USB serial when the phone has no IR blaster):
#   Send one line:   TX:<carrier>:<csv durations>
#       e.g.         TX:38000:9000,4500,560,560,...
#   Board emits it on GP15 with a <carrier>Hz carrier and replies "OK" (or "ERR:...").

from machine import Pin, PWM
from array import array
import utime
import sys
import select

FW_VERSION = "1.1.0"  # 펌웨어 버전 (프로토콜 major / 기능 minor / 버그픽스 patch)
BOARD_NAME = "ZBD IR Board"
IR_RX_PIN = 0         # GP0  - IR receiver OUT
IR_TX_PIN = 15        # GP15 - IR LED (through transistor)
CARRIER = 38000       # 38kHz: standard for NEC and most consumer remotes
EDGE_MAX = 400        # max edges captured per frame
MIN_EDGES = 6         # ignore short noise bursts

# Captured edge timestamps (us). Filled inside the (hard) IRQ -> no allocation.
edges = array('i', [0] * EDGE_MAX)
idx = 0


def _edge(pin):
    # Hard IRQ: only allocation-free ops (small-int assigns, array store).
    global idx
    if idx < EDGE_MAX:
        edges[idx] = utime.ticks_us()
        idx += 1


def nec_label(d):
    # d = list of on/off durations (us). Returns a label string or "".
    if len(d) < 4:
        return ""
    if not (7000 < d[0] < 11000):
        return ""                      # not an NEC leader
    if 1500 < d[1] < 3000:
        return "NEC repeat"
    if not (3500 < d[1] < 5500):
        return ""
    val = 0
    nbits = 0
    i = 2
    while i + 1 < len(d) and nbits < 32:
        if d[i + 1] > 1000:            # long off (~1.69ms)=1, short (~560us)=0
            val |= (1 << nbits)
        nbits += 1
        i += 2
    if nbits < 32:
        return ""
    addr = val & 0xFFFF               # extended NEC -> 16-bit address
    cmd = (val >> 16) & 0xFF
    cmd_inv = (val >> 24) & 0xFF
    ok = "ok" if ((cmd ^ cmd_inv) == 0xFF) else "CHK?"
    return "NEC raw=0x%08X addr=0x%04X cmd=0x%02X %s" % (val, addr, cmd, ok)


def emit(n):
    if n < MIN_EDGES:
        return
    # durations between consecutive edges == Android transmit() pattern
    d = []
    for i in range(1, n):
        d.append(utime.ticks_diff(edges[i], edges[i - 1]))

    label = nec_label(d)
    if label:
        print("# " + label)
    print("RAW(%d): %s" % (CARRIER, ",".join(str(x) for x in d)))


# --- TX -------------------------------------------------------------------
_tx_pwm = None

def transmit(carrier, pattern):
    # pattern alternates carrier ON / OFF, starting with ON (the leader mark).
    global _tx_pwm
    if _tx_pwm is None:
        _tx_pwm = PWM(Pin(IR_TX_PIN))
    pwm = _tx_pwm
    pwm.freq(carrier)
    duty_on = 21845                    # ~33% of 65535 (typical IR carrier duty)
    on = True
    for dur in pattern:
        pwm.duty_u16(duty_on if on else 0)
        t = utime.ticks_us()
        while utime.ticks_diff(utime.ticks_us(), t) < dur:
            pass                       # busy-wait this segment (us precision)
        on = not on
    pwm.duty_u16(0)                    # carrier off


def handle_command(line):
    line = line.strip()
    if line == "VER?":
        print("VER:" + FW_VERSION)
        return
    if line == "INFO?":
        print("INFO:name=%s;ver=%s;rx=GP%d;tx=GP%d" % (BOARD_NAME, FW_VERSION, IR_RX_PIN, IR_TX_PIN))
        return
    if not line.startswith("TX:"):
        return
    try:
        parts = line.split(":", 2)     # ["TX", carrier, csv]
        carrier = int(parts[1])
        pattern = [int(x) for x in parts[2].split(",") if x]
        if len(pattern) < 2:
            print("ERR:short")
            return
        transmit(carrier, pattern)
        print("OK")
    except Exception as e:
        print("ERR:" + str(e))


def main():
    pin = Pin(IR_RX_PIN, Pin.IN, Pin.PULL_UP)   # IR receiver idles HIGH
    pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=_edge)

    # Non-blocking serial command reader (so RX capture keeps running).
    poller = select.poll()
    poller.register(sys.stdin, select.POLLIN)

    print("IR ready v%s: RX=GP%d, TX=GP%d (%dHz). Press a remote, or send 'TX:carrier:csv' / 'VER?'."
          % (FW_VERSION, IR_RX_PIN, IR_TX_PIN, CARRIER))

    global idx
    last_idx = 0
    last_change = utime.ticks_ms()
    while True:
        # 1) serial command — read the whole 'TX:...' line at once (readline).
        #    Char-by-char was ~수백 ms for a long NEC line; readline is ~2ms.
        if poller.poll(0):
            line = sys.stdin.readline()
            if line:
                handle_command(line)

        # 2) RX frame emit (unchanged capture logic)
        n = idx
        if n != last_idx:
            last_idx = n
            last_change = utime.ticks_ms()
        elif n > 0 and utime.ticks_diff(utime.ticks_ms(), last_change) > 30:
            emit(n)
            idx = 0
            last_idx = 0

        utime.sleep_ms(2)


main()
