import argparse
import sys
from threading import Thread
import time
import numpy as np
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, ranges
from bokeh.plotting import figure
from bokeh.server.server import Server
from tornado import gen
from functools import partial
from bokeh.palettes import Category10
import Pyro4
import base64


if __name__ == '__main__':
    for i, arg in enumerate(sys.argv):
        if (arg[0] == '-') and arg[1].isdigit(): sys.argv[i] = ' ' + arg
    parser = argparse.ArgumentParser(description='arguments')
    parser.add_argument("--win_len", "-l", type=int, default=150)
    parser.add_argument("--data_rate", "-d", type=float, default=16000/2048)
    parser.add_argument("--overlap", "-o", type=int, default=0)
    parser.add_argument("--plot_width", "-pw", type=int, default=1500)
    parser.add_argument("--plot_height", "-ph", type=int, default=400)
    parser.add_argument("--ranges", "-r", default="0:100,auto")
    parser.add_argument("--titles", "-t",
                        default='Sampling rate offset estimation,Time offset estimation'
                        )
    parser.add_argument("--xlabels", "-x", default='Time / s,Time / s')
    parser.add_argument("--ylabels", "-y", default='SRO / ppm,Time offset / smp')
    parser.add_argument("--font_size", "-f", type=int, default=30)
    parser.add_argument("--name_server", "-n", default='monitoring')
    parser.add_argument("--host_ip", "-ip")
    args = parser.parse_args()

    host_ip = args.host_ip
    if host_ip is not None:
        name_server = Pyro4.locateNS(host=host_ip)
    else:
        name_server = Pyro4.locateNS()
    monitoring = Pyro4.Proxy(name_server.lookup(args.name_server))
    titles = args.titles.split(',')
    xlabels = args.xlabels
    if xlabels is not None:
        xlabels = xlabels.split(',')
    ylabels = args.ylabels
    if ylabels is not None:
        ylabels = ylabels.split(',')
    font_size = args.font_size
    n_channels = monitoring.get_channels()
    block_len = monitoring.get_block_len()
    overlap = args.overlap
    buffer_size = int(args.data_rate * args.win_len)
    plot_width = args.plot_width
    plot_height = args.plot_height
    y_ranges = args.ranges.split(',')
    y_mins = []
    y_maxs = []
    for range_id, range_ in enumerate(y_ranges):
        if range_ == 'auto':
            y_mins.append(None)
            y_maxs.append(None)
        else:
            lims = range_.split(':')
            y_mins.append(float(lims[0]))
            y_maxs.append(float(lims[1]))

    def modify_doc(doc):
        sources = [ColumnDataSource(
            data=dict(
                x=np.linspace(0, args.win_len, buffer_size, dtype=np.float32),
                y=np.zeros(buffer_size).astype(np.float32)
            )
        ) for _ in range(n_channels)]
        plots = []
        for plt_id, title in enumerate(titles):
            if y_maxs[plt_id] is None:
                plots.append(figure(
                    y_range=ranges.DataRange1d(default_span=20,
                                               range_padding_units='absolute',
                                               range_padding=10),
                    title=title, plot_width=plot_width,
                    plot_height=plot_height, toolbar_location=None,
                ))
            else:
                plots.append(figure(
                    y_range=(y_mins[plt_id], y_maxs[plt_id]),
                    title=title, plot_width=plot_width,
                    plot_height=plot_height, toolbar_location=None,
                ))
        for plot_id, plt in enumerate(zip(sources, plots)):
            source, plot = plt
            plot.line(
                'x', 'y', source=source, line_width=5, color=(Category10[10])[0]
            )
            plot.x_range.range_padding = 0
            if xlabels is not None:
                plot.xaxis.axis_label = xlabels[plot_id]
            if ylabels is not None:
                plot.yaxis.axis_label = ylabels[plot_id]
            plot.title.text_font_size = f'{font_size}pt'
            plot.axis.major_label_text_font_size = f'{font_size}pt'
            plot.xaxis.axis_label_text_font_size = f'{font_size}pt'
            plot.yaxis.axis_label_text_font_size = f'{font_size}pt'


        @gen.coroutine
        def update(y):
            y = [yi for yi in y]
            for i, yi in enumerate(y):
                sources[i].data['y'] = yi

        def blocking_task():
            block_idx = 0
            buffer = np.zeros((buffer_size, n_channels)).astype(np.float32)
            while True:
                # do some blocking computation
                data = monitoring.get_data(block_idx)
                if data is not None:
                    block_idx, y = data
                    y = np.fromstring(
                        base64.b64decode(y['data']), dtype=np.float32
                    ).reshape((block_len, n_channels))
                    buffer[:buffer_size - block_len] = buffer[block_len - overlap:]
                    buffer[-block_len:] = y
                    # but update the document from callback
                    doc.add_next_tick_callback(partial(update, y=buffer.T))
                else:
                    time.sleep(.01)

        doc.add_root(column(*plots))

        thread = Thread(target=blocking_task)
        thread.start()

    server = Server({'/': modify_doc})
    server.start()
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()
