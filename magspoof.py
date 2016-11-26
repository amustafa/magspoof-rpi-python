import RPi.GPIO as GPIO
import time
import ConfigParser
from magnetic_stripe import MagnetStripEncoding
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
GPIO_STATE = {
        'COIL_PIN_A': None,
        'COIL_PIN_B': None,
        'ENABLE_PIN': None
        }

def set_pin(pin_name, pin_state):
    """
    Keeps the pin and the pin state variable synced
    """

    GPIO_STATE[pin_name] = pin_state
    GPIO.output(pin_name, pin_state)

def enable_coil():
    set_pin('ENABLE_PIN', True)

def disable_coil():
    set_pin(COIL_PIN_A, False)
    set_pin(COIL_PIN_B, False)
    set_pin(ENABLE_PIN, False)


def blink(pin, delay, times):
    """
    Directs the onboard LED to blink
    """
    for i in range(times):
        set_pin(pin, True)
        time.sleep(delay)
        set_pin(pin, False)
        time.sleep(delay)

def reverse_current(gpio_state):
    """
    Takes the state of the gpio bins, switches the values in the
    dictionary and then sets the outputs.
    """
    set_pin(COIL_PIN_A, not gpio_state['COIL_PIN_A'])
    set_pin(COIL_PIN_B, not gpio_state['COIL_PIN_B'])


def send_bit(bit, gpio_state):
    """
    Info from: http://dewimorgan.livejournal.com/48917.html
    A bit in a magnetic strip is designated by having time polarity shifts.

    For example,

    NnsSSsnN SssssnnnN NnnnnsssS NnsSSsnN NnsSSsnN
        1        0         0         1       1

    So in order to send a bit, we must know what the existing polarity is and
    either switch it once during a clock step for a zero or switch it twice
    for a one.

    By sending current through the wire in one direction, the magnetic field is
    oriented one way. By sending in the other direction the magnetic field is
    oriented the opposite way. current_dir will designate the direction.
    """
    print bit

    reverse_current(gpio_state)
    time.sleep(CLOCK_INTERVAL)

    if (bit):
        reverse_current(gpio_state)

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
    Converts the different tracks into
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
    except KeyboardInterrupt as e:
        print e
    finally:
        print "Cleaning up"
        GPIO.cleanup()
