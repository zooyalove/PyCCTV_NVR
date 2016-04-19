from gi.repository import Gst
import gi
gi.require_version('Gst', '1.0')


def nsec2time(nsec, str_time=True):
    s, ns = divmod(nsec, Gst.SECOND)
    if str_time:
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return '%02d:%02d:%02d' % (h, m, s)
    else:
        return s
