# -*- encoding: utf-8 -*-
# thai_strftime()
# Thai date and time string formatter
# Formatting directives similar to datetime.strftime()
#
# จัดรูปแบบข้อความวันที่และเวลา แบบเดียวกับ datetime.strftime()
# โดยจะใช้ชื่อเดือนเป็นภาษาไทย และปีเป็นพุทธศักราช
# (ไม่รองรับปีก่อน พ.ศ. 2484 - ก่อนการเปลี่ยนวันปีใหม่ไทย)
#
# No Rights Reserved
# PUBLIC DOMAIN or CC0 1.0 Universal
# Author: @bact Arthit Suriyawongkul
#
# Included in PyThaiNLP 2.0
# For a more complete code, see PyThaiNLP:
# https://github.com/PyThaiNLP/pythainlp/blob/dev/pythainlp/util/strftime.py
#
# It uses Thai names and Thai Buddhist era for these directives:
# - %a abbreviated weekday name
# - %A full weekday name
# - %b abbreviated month name
# - %B full month name
# - %y year without century
# - %Y year with century
# - %c date and time representation
# - %v short date representation (undocumented directive, please avoid)
#
# Other directives will be passed to datetime.strftime()
#
# Example:
# >>> datetime_obj = datetime(year=1976, month=10, day=6)
# >>> thai_strftime(datetime_obj, "%a %-d %b %y")
# 'พ 6 ต.ค. 19'
#
# See Python document for strftime:
# https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
#
# Note 1:
# The Thai Buddhist Era (BE) year is simply converted from AD by adding 543.
# This is certainly not accurate for years before 1941 AD,
# due to the change in Thai New Year's Day.
#
# Note 2:
# This meant to be an interrim solution, since Python standard's locale module
# (which relied on C's strftime()) does not support "th" or "th_TH" locale yet.
# If supported, we can just locale.setlocale(locale.LC_TIME, "th_TH") and
# then use native datetime.strftime().
#
# Gist:
# https://gist.github.com/bact/b8afe49cb1ae62913e6c1e899dcddbdb

import warnings
from datetime import datetime

_TH_ABBR_WEEKDAYS = ["จ", "อ", "พ", "พฤ", "ศ", "ส", "อา"]
_TH_FULL_WEEKDAYS = [
    "วันจันทร์",
    "วันอังคาร",
    "วันพุธ",
    "วันพฤหัสบดี",
    "วันศุกร์",
    "วันเสาร์",
    "วันอาทิตย์",
]

_TH_ABBR_MONTHS = [
    "ม.ค.",
    "ก.พ.",
    "มี.ค.",
    "เม.ย.",
    "พ.ค.",
    "มิ.ย.",
    "ก.ค.",
    "ส.ค.",
    "ก.ย.",
    "ต.ค.",
    "พ.ย.",
    "ธ.ค.",
]
_TH_FULL_MONTHS = [
    "มกราคม",
    "กุมภาพันธ์",
    "มีนาคม",
    "เมษายน",
    "พฤษภาคม",
    "มิถุนายน",
    "กรกฎาคม",
    "สิงหาคม",
    "กันยายน",
    "ตุลาคม",
    "พฤศจิกายน",
    "ธันวาคม",
]

_BE_AD_DIFFERENCE = 543

_NEED_L10N = "AaBbCcDFGgvXxYy+"  # flags that need localization
_EXTENSIONS = "EO-_0^#"  # extension flags


# Standard conversion support for thai_strftime()
def _std_strftime(dt_obj, fmt_char):
    """
    Standard datetime.strftime() with normalization and exception handling.
    """
    str_ = ""
    try:
        str_ = dt_obj.strftime("%{}".format(fmt_char))
        if not str_ or str_ == "%{}".format(fmt_char):
            # normalize outputs for unsupported directives
            # in different platforms
            # "%Q" may result "%Q", "Q", or "", make it "Q"
            str_ = fmt_char
    except ValueError as err:
        # Unsupported directives may raise ValueError on Windows,
        # in that case just use the fmt_char
        warnings.warn(
            (
                "String format directive unknown/not support: %{}"
                "The system raises this ValueError: {}".format(fmt_char, err)
            ),
            UserWarning,
        )
        str_ = fmt_char
    return str_


# Thai conversion support for thai_strftime()
def _thai_strftime(
        dt_obj, fmt_char, buddhist_era = True
):
    """
    Conversion support for thai_strftime().

    The fmt_char should be in _NEED_L10N when call this function.
    """
    str_ = ""
    year = dt_obj.year
    if buddhist_era:
        year = year + _BE_AD_DIFFERENCE

    if fmt_char == "A":
        # National representation of the full weekday name
        str_ = _TH_FULL_WEEKDAYS[dt_obj.weekday()]
    elif fmt_char == "a":
        # National representation of the abbreviated weekday
        str_ = _TH_ABBR_WEEKDAYS[dt_obj.weekday()]
    elif fmt_char == "B":
        # National representation of the full month name
        str_ = _TH_FULL_MONTHS[dt_obj.month - 1]
    elif fmt_char == "b":
        # National representation of the abbreviated month name
        str_ = _TH_ABBR_MONTHS[dt_obj.month - 1]
    elif fmt_char == "C":
        # Thai Buddhist century (AD+543)/100 + 1 as decimal number;
        str_ = str(int(year / 100) + 1).zfill(2)
    elif fmt_char == "c":
        # Locale’s appropriate date and time representation
        # Wed  6 Oct 01:40:00 1976
        # พ   6 ต.ค. 01:40:00 2519  <-- left-aligned weekday, right-aligned day
        str_ = "{:<2} {:>2} {} {} {}".format(
            _TH_ABBR_WEEKDAYS[dt_obj.weekday()],
            dt_obj.day,
            _TH_ABBR_MONTHS[dt_obj.month - 1],
            dt_obj.strftime("%H:%M:%S"),
            str(year).zfill(4),
        )
    elif fmt_char == "D":
        # Equivalent to ``%m/%d/%y''
        str_ = "{}/{}".format(
            dt_obj.strftime("%m/%d"), (str(year)[-2:]).zfill(2),
        )
    elif fmt_char == "F":
        # Equivalent to ``%Y-%m-%d''
        str_ = "{}-{}".format(str(year).zfill(4), dt_obj.strftime("%m-%d"), )
    elif fmt_char == "G":
        # ISO 8601 year with century representing the year that contains
        # the greater part of the ISO week (%V). Monday as the first day
        # of the week.
        year_G = int(dt_obj.strftime("%G"))
        if buddhist_era:
            year_G = year_G + _BE_AD_DIFFERENCE
        str_ = str(year_G).zfill(4)
    elif fmt_char == "g":
        # Same year as in ``%G'',
        # but as a decimal number without century (00-99).
        year_G = int(dt_obj.strftime("%G"))
        if buddhist_era:
            year_G = year_G + _BE_AD_DIFFERENCE
        str_ = (str(year_G)[-2:]).zfill(2)
    elif fmt_char == "v":
        # BSD extension, ' 6-Oct-1976'
        str_ = "{:>2}-{}-{}".format(
            dt_obj.day, _TH_ABBR_MONTHS[dt_obj.month - 1], str(year).zfill(4),
        )
    elif fmt_char == "X":
        # Locale’s appropriate time representation.
        str_ = dt_obj.strftime("%H:%M:%S")
    elif fmt_char == "x":
        # Locale’s appropriate date representation.
        str_ = "{}/{}/{}".format(
            str(dt_obj.day).zfill(2),
            str(dt_obj.month).zfill(2),
            str(year).zfill(4),
        )
    elif fmt_char == "Y":
        # Year with century
        str_ = (str(year)).zfill(4)
    elif fmt_char == "y":
        # Year without century
        str_ = (str(year)[-2:]).zfill(2)
    elif fmt_char == "+":
        # National representation of the date and time
        # (the format is similar to that produced by date(1))
        # Wed  6 Oct 1976 01:40:00
        str_ = "{:<2} {:>2} {} {} {}".format(
            _TH_ABBR_WEEKDAYS[dt_obj.weekday()],
            dt_obj.day,
            _TH_ABBR_MONTHS[dt_obj.month - 1],
            year,
            dt_obj.strftime("%H:%M:%S"),
        )
    else:
        # No known localization available, use Python's default
        str_ = _std_strftime(dt_obj, fmt_char)

    return str_


def thai_strftime(
        dt_obj,
        fmt = "%-d %b %y",
        thai_digit = False,
        buddhist_era = True,
):
    """
    Convert :class:`datetime.datetime` into Thai date and time format.

    The formatting directives are similar to :func:`datatime.strrftime`.

    This function uses Thai names and Thai Buddhist Era for these directives:
        * **%a** - abbreviated weekday name
          (i.e. "จ", "อ", "พ", "พฤ", "ศ", "ส", "อา")
        * **%A** - full weekday name
          (i.e. "วันจันทร์", "วันอังคาร", "วันเสาร์", "วันอาทิตย์")
        * **%b** - abbreviated month name
          (i.e. "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ธ.ค.")
        * **%B** - full month name
          (i.e. "มกราคม", "กุมภาพันธ์", "พฤศจิกายน", "ธันวาคม",)
        * **%y** - year without century (i.e. "56", "10")
        * **%Y** - year with century (i.e. "2556", "2410")
        * **%c** - date and time representation
          (i.e. "พ   6 ต.ค. 01:40:00 2519")
        * **%v** - short date representation
          (i.e. " 6-ม.ค.-2562", "27-ก.พ.-2555")

    Other directives will be passed to datetime.strftime()

    :Note:
        * The Thai Buddhist Era (BE) year is simply converted from AD
          by adding 543. This is certainly not accurate for years
          before 1941 AD, due to the change in Thai New Year's Day.
        * This meant to be an interrim solution, since
          Python standard's locale module (which relied on C's strftime())
          does not support "th" or "th_TH" locale yet. If supported,
          we can just locale.setlocale(locale.LC_TIME, "th_TH")
          and then use native datetime.strftime().

    We trying to make this platform-independent and support extentions
    as many as possible. See these links for strftime() extensions
    in POSIX, BSD, and GNU libc:

        * Python
          https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
        * C http://www.cplusplus.com/reference/ctime/strftime/
        * GNU https://metacpan.org/pod/POSIX::strftime::GNU
        * Linux https://linux.die.net/man/3/strftime
        * OpenBSD https://man.openbsd.org/strftime.3
        * FreeBSD https://www.unix.com/man-page/FreeBSD/3/strftime/
        * macOS
          https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man3/strftime.3.html
        * PHP https://secure.php.net/manual/en/function.strftime.php
        * JavaScript's implementation https://github.com/samsonjs/strftime
        * strftime() quick reference http://www.strftime.net/

    :param datetime dt_obj: an instantiatetd object of
                            :mod:`datetime.datetime`
    :param str fmt: string containing date and time directives
    :param bool thaidigit: If `thaidigit` is set to **False** (default),
                           number will be represented in Arabic digit.
                           If it is set to **True**, it will be represented
                           in Thai digit.

    :return: Date and time text, with month in Thai name and year in
             Thai Buddhist era. The year is simply converted from AD
             by adding 543 (will not accurate for years before 1941 AD,
             due to change in Thai New Year's Day).
    :rtype: str

    :Example:
    ::

        from datetime import datetime
        from pythainlp.util import thai_strftime

        datetime_obj = datetime(year=2019, month=6, day=9, \\
            hour=5, minute=59, second=0, microsecond=0)

        print(datetime_obj)
        # output: 2019-06-09 05:59:00

        thai_strftime(datetime_obj, "%A %d %B %Y")
        # output: 'วันอาทิตย์ 09 มิถุนายน 2562'

        thai_strftime(datetime_obj, "%a %-d %b %y")  # no padding
        # output: 'อา 9 มิ.ย. 62'

        thai_strftime(datetime_obj, "%a %_d %b %y")  # space padding
        # output: 'อา  9 มิ.ย. 62'

        thai_strftime(datetime_obj, "%a %0d %b %y")  # zero padding
        # output: 'อา 09 มิ.ย. 62'

        thai_strftime(datetime_obj, "%-H นาฬิกา %-M นาที", thaidigit=True)
        # output: '๕ นาฬิกา ๕๙ นาที'

        thai_strftime(datetime_obj, "%D (%v)")
        # output: '06/09/62 ( 9-มิ.ย.-2562)'

        thai_strftime(datetime_obj, "%c")
        # output: 'อา  9 มิ.ย. 05:59:00 2562'

        thai_strftime(datetime_obj, "%H:%M %p")
        # output: '01:40 AM'

        thai_strftime(datetime_obj, "%H:%M %#p")
        # output: '01:40 am'
    """
    thaidate_parts = []

    i = 0
    fmt_len = len(fmt)
    while i < fmt_len:
        str_ = ""
        if fmt[i] == "%":
            j = i + 1
            if j < fmt_len:
                fmt_char = fmt[j]
                if fmt_char in _NEED_L10N:  # requires localization?
                    str_ = _thai_strftime(dt_obj, fmt_char, buddhist_era)
                elif fmt_char in _EXTENSIONS:
                    fmt_char_ext = fmt_char
                    k = j + 1
                    if k < fmt_len:
                        fmt_char = fmt[k]
                        if fmt_char in _NEED_L10N:
                            str_ = _thai_strftime(
                                dt_obj, fmt_char, buddhist_era
                            )
                        else:
                            str_ = _std_strftime(dt_obj, fmt_char)

                        if fmt_char_ext == "-":
                            # GNU libc extension,
                            # no padding
                            if str_[0] and str_[0] in " 0":
                                str_ = str_[1:]
                        elif fmt_char_ext == "_":
                            # GNU libc extension,
                            # explicitly specify space (" ") for padding
                            if str_[0] and str_[0] == "0":
                                str_ = " " + str_[1:]
                        elif fmt_char_ext == "0":
                            # GNU libc extension,
                            # explicitly specify zero ("0") for padding
                            if str_[0] and str_[0] == " ":
                                str_ = "0" + str_[1:]
                        elif fmt_char_ext == "^":
                            # GNU libc extension,
                            # convert to upper case
                            str_ = str_.upper()
                        elif fmt_char_ext == "#":
                            # GNU libc extension,
                            # swap case - useful for %Z
                            str_ = str_.swapcase()
                        elif fmt_char_ext == "E":
                            # POSIX extension,
                            # uses the locale's alternative representation
                            # Not implemented yet
                            pass
                        i = i + 1  # consume char after format char
                    else:
                        # format char at string's end has no meaning
                        str_ = fmt_char_ext
                else:  # not in _NEED_L10N nor _EXTENSIONS
                    # no known localization available, use Python's default
                    str_ = _std_strftime(dt_obj, fmt_char)

                i = i + 1  # consume char after "%"
            else:
                # % char at string's end has no meaning
                str_ = "%"
        else:
            str_ = fmt[i]

        thaidate_parts.append(str_)
        i = i + 1

    thaidate_text = "".join(thaidate_parts)

    return thaidate_text
