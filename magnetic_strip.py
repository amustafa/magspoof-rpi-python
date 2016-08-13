"""
Magnetic Strip

This packaged represents the different types of inforamtion that can be held on magnetic
strip on cards such as a credit card.

Information taken from:
    http://www.abacus21.com/magnetic-strip-encoding-1586.html
"""


class Track(object):

    def __init__(self, data, data_validator, track_number, recording_density, character_conf,
                 info_length, info_validator, start_sentinel, end_sentinel,
                 field_separator, check_format_code=False):
        self.data_validator = data_validator
        self.track_number = track_number
        self.recording_density = recording_density
        self.character_bitlen = character_conf
        self.info_length = info_length
        self.info_validator = info_validator
        self.start_sentinel = start_sentinel
        self.end_sentinel = end_sentinel
        self.field_separator = field_separator
        self.check_format_code = check_format_code
        self._LRC = None
        self.data_validator(data)
        self.str_data = data

        self._data = None
        self._hex_data = None
        self._bit_data = None # includes parity bit

        self.magstrip_bit_seq = None

    @property
    def data(self):
        """
        Returns the data as a series of integer values.

        Track 1 encodes in ANSI/ISO ALPHA Data Format
                Same as ascii except all values are 32 lower.

        Track 2 encodes in ANSI/ISO BCD  Data Format
                hex value is ascii value minus 48
        :return:
        """
        if self._data is None:
            self._data = []
            if self.track_number == 1:
                for c in self.str_data:
                    self._data.append(ord(c)-32)
            else:
                for c in self.str_data:
                    self._data.append(ord(c) - 48)
        return self._data

    @property
    def hex_data(self):
        if self._hex_data is None:
            self._hex_data = []
            for val in self.data:
                self._hex_data.append(hex(val))

        return self._hex_data

    @property
    def bit_data(self):
        """
        Returns a list of strings representing the bitsequence of the data. This will NOT
        include the parity bit.
        """
        if self._bit_data is None:
            self._bit_data = []
            for val in self.data:
                b = bin(val)[2:].zfill(self.character_bitlen - 1)
                self._bit_data.append(b)
        return self._bit_data

    @property
    def lrc(self):
        lrc = 0
        for val in self.data:
            lrc ^= val
        return lrc

    def get_parity_bit(self, val):
        """
        1 if the parity is even
        0 if the parity is odd

        :param val:
        :return:
        """
        return (bin(val).count('1') + 1) % 2

    @property
    def output_bitsequence(self):
        """
        returns a number that is created from taking each data value, returning a bit sequence, reversing it into
            least significant digit first, adding an odd parity check bit, calculating the LRC and adding that to the
            end.
        :return:
        """
        bit_seq_str = ''
        for binval in self.bit_data:
            parity_bit = (binval.count('1') + 1) % 2
            bit_seq_str += "{}{}".format(binval[::-1], parity_bit)

        lrc_bit_seq = bin(self.lrc)[2:].zfill(self.character_bitlen - 1)
        lrc_bit_parity = (lrc_bit_seq.count('1') +1) % 2
        bit_seq_str += "{}{}".format(lrc_bit_seq[::-1],lrc_bit_parity)
        return bit_seq_str






class MagnetStripEncoding(object):

    TRACK1_SETTINGS = {
        "track_number":1,
        "recording_density":210,
        "character_conf":7,
        "info_length":79,
        "info_validator": lambda x: x.isalnum(),
        "start_sentinel": '%',
        "end_sentinel": '?',
        "field_separator": '^',
        "check_format_code":True
    }

    TRACK2_SETTINGS = {
        "track_number":2,
        "recording_density":75,
        "character_conf":5,
        "info_length":40,
        "info_validator": lambda x: x.isnumeric(),
        "start_sentinel": ';',
        "end_sentinel": '?',
        "field_separator": '=',
    }

    @classmethod
    def track1_validator(cls, data):
        if len(data) > cls.TRACK1_SETTINGS["info_length"]:
            raise ValueError("Track 1 data wrong length")
        if data[0] != cls.TRACK1_SETTINGS["start_sentinel"]:
            raise ValueError("Track 1 data has incorrect start sentinel")
        if data[-1] != cls.TRACK1_SETTINGS["end_sentinel"]:
            raise ValueError("Track 1 data has incorrect end sentinel")
        if len(data[1:-1].split(cls.TRACK1_SETTINGS["field_separator"])) != 3:
            raise ValueError("Track 1 data has incorrect data items")
        # if not cls.TRACK1_SETTINGS["info_validator"](data):
        #     raise ValueError("Data is the wrong type")
        return True

    @classmethod
    def track2_validator(cls, data):
        if len(data) > cls.TRACK2_SETTINGS["info_length"]:
            raise ValueError("Track 1 data wrong length")
        if data[0] != cls.TRACK2_SETTINGS["start_sentinel"]:
            raise ValueError("Track 1 data has incorrect start sentinel")
        if data[-1] != cls.TRACK2_SETTINGS["end_sentinel"]:
            raise ValueError("Track 1 data has incorrect end sentinel")
        if len(data[1:-1].split(cls.TRACK2_SETTINGS["field_separator"])) != 2:
            raise ValueError("Track 1 data has incorrect data items")
        # if not cls.TRACK2_SETTINGS["info_validator"](data):
        #     raise ValueError("Data is the wrong type")
        return True

    def __init__(self, card_data):
        """
        Card data may be either a single string with all the tracks or a list of string,
        separated by track.

        :param card_data:
        """
        self.track1 = None
        self.track2 = None

        if not isinstance(card_data, list):
            track1_end = card_data.index(self.TRACK1_SETTINGS["end_sentinel"])
            card_data = [card_data[:track1_end+1], card_data[track1_end+1:]]

        self.track1 = self.create_track_one(card_data[0])
        self.track2 = self.create_track_two(card_data[1])

        self.num_tracks = 1
        self.num_tracks += 1 if self.track2 is not None else 0

    @classmethod
    def create_track_one(cls, data):
        return Track(data, cls.track1_validator, **cls.TRACK1_SETTINGS)

    @classmethod
    def create_track_two(cls, data):
        return Track(data, cls.track2_validator, **cls.TRACK2_SETTINGS)




# x = MagnetStripEncoding('%B0123456789101112^SCHMOE/JOSEPH X^01020304050607080910?;0123456789101112=01020304050607080910?')
# print x.track1.str_data
# print x.track1.data
# print x.track1.hex_data
# print x.track1.bit_data
# print x.track1.lrc
# print x.track1.output_bitsequence
# print int(x.track1.output_bitsequence,2)