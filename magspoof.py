import RPi.GPIO as GPIO
import time
import ConfigParser
from magnetic_strip import MagnetStripEncoding
conf = ConfigParser.ConfigParser()
conf.readfp(open('conf.ini', 'r'))



## GPIO Config
BUTTON_SIGNAL_PIN = conf.getint('RPi', 'BUTTON_SIGNAL_PIN')  # PB2 connecting to switch
ENABLE_PIN = conf.getint('RPi', 'ENABLE_PIN')  # PB3 connecting to pin 1 on IC1
COIL_PIN_A = conf.getint('RPi', 'COIL_PIN_A')  # PB0 connecting to pin 2 in IC1 and PIN_A in code
COIL_PIN_B = conf.getint('RPi', 'COIL_PIN_B')  # PB1 connecting to pin 7 on IC1 and PIN_B in code
CLOCK_INTERVAL = conf.getfloat('RPi', 'CLOCK_INTERVAL')
BETWEEN_ZERO = conf.getint('RPi', 'BETWEEN_ZERO') # how long to wait between sending tracks

# Card Info
TRACK_COUNT = conf.getint('Card Info', 'TRACK_COUNT')
TRACKS = [conf.get('Card Info', 'TRACK{}'.format(i+1)) for i in range(TRACK_COUNT)]

CARD = MagnetStripEncoding(TRACKS)


SENDING_LOCKED = False


def enable_coil():
    GPIO.output(ENABLE_PIN, True)


def disable_coil():

    GPIO.output(COIL_PIN_A, False)
    GPIO.output(COIL_PIN_B, False)
    GPIO.output(ENABLE_PIN, False)


def blink(pin, delay, times):
    for i in range(times):
        GPIO.output(pin, True)
        time.sleep(delay)
        GPIO.output(pin, False)
        time.sleep(delay)


def send_bit(bit, signal_direction=1):
    print bit
    signal_direction ^= 1

    GPIO.output(COIL_PIN_A, signal_direction)
    GPIO.output(COIL_PIN_B, not signal_direction)
    time.sleep(CLOCK_INTERVAL)

    if (bit):
        signal_direction ^= 1
        GPIO.output(COIL_PIN_A, signal_direction)
        GPIO.output(COIL_PIN_B, not signal_direction)

    time.sleep(CLOCK_INTERVAL)


def transmit_signal(bitseq):
    print "Sending:", bitseq
    try:
        print "Attempting to send %i bits" % len(bitseq)
        IS_SENDING = True
        signal_direction = 0
        enable_coil()

        for bit in bitseq:
            send_bit(bit == '1')

        disable_coil()

    except Exception as e:
        print e
    finally:
        IS_SENDING = False
        print "Finished Sending"


def transmit_card(card):
    """

    :param card:
    :type card: MagnetStripEncoding
    :return:
    """
    buffer_signal = '0'*BETWEEN_ZERO
    track1_signal = card.track1.output_bitsequence
    track2_signal = card.track2.output_bitsequence
    card_bit_seq = "{}{}{}{}".format(
        buffer_signal,
        track1_signal,
        buffer_signal,
        track2_signal
    )
    transmit_signal(card_bit_seq)




def setup_mag_spoof():
    print "Running Setup"
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(BUTTON_SIGNAL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ENABLE_PIN, GPIO.OUT)
    GPIO.setup(COIL_PIN_A, GPIO.OUT)
    GPIO.setup(COIL_PIN_B, GPIO.OUT)
    blink(ENABLE_PIN, .2, 3)


def run_mag_spoof():
    print "Listening for Button Press"
    while True:
        if not SENDING_LOCKED and GPIO.input(BUTTON_SIGNAL_PIN) == False:
            print ('Button Pressed')
            transmit_card(CARD)
        time.sleep(.2)


if __name__ == "__main__":
    try:
        setup_mag_spoof()
        run_mag_spoof()
    except  KeyboardInterrupt as e:
        print e
    finally:
        print "Cleaning up"
        GPIO.cleanup()
