# Copyright 2009 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Some code for creating chart images."""

__author__ = 'tstromberg@google.com (Thomas Stromberg)'

import base64
import io
import itertools
import math
import re
import urllib.parse

# Use matplotlib for chart generation
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend
import matplotlib.pyplot as plt

# external dependencies (from nb_third_party)
from graphy import common
from graphy.backends import google_chart_api

CHART_URI = 'http://chart.apis.google.com/chart'
BASE_COLORS = ('ff9900', '1a00ff', 'ff00e6', '80ff00', '00e6ff', 'fae30a',
               'BE81F7', '9f5734', '000000', 'ff0000', '3090c0', '477248f',
               'ababab', '7b9f34', '00ff00', '0000ff', '9900ff', '405090',
               '051290', 'f3e000', '9030f0', 'f03060', 'e0a030', '4598cd')
CHART_WIDTH = 720
CHART_HEIGHT = 415


def _FigureToDataUri(fig):
  """Convert a matplotlib figure to a base64-encoded data URI."""
  buf = io.BytesIO()
  fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
  buf.seek(0)
  img_base64 = base64.b64encode(buf.read()).decode('utf-8')
  plt.close(fig)
  return f'data:image/png;base64,{img_base64}'


def DarkenHexColorCode(color, shade=1):
  """Given a color in hex format (for HTML), darken it X shades."""
  rgb_values = [int(x, 16) for x in re.findall(r'\w\w', color)]
  new_color = []
  for value in rgb_values:
    value -= shade*32
    if value <= 0:
      new_color.append('00')
    elif value <= 16:
      # Google Chart API requires that color values be 0-padded.
      new_color.append('0' + hex(value)[2:])
    else:
      new_color.append(hex(value)[2:])

  return ''.join(new_color)


def _GoodTicks(max_value, tick_size=2.5, num_ticks=10.0):
  """Find a good round tick size to use in graphs."""
  try_tick = tick_size
  while try_tick < max_value:
    if (max_value / try_tick) > num_ticks:
      try_tick *= 2
    else:
      return int(round(try_tick))
  # Fallback
  print("Could not find good tick size for %s (size=%s, num=%s)" % (max_value, tick_size, num_ticks))
  simple_value = int(max_value  / num_ticks)
  if simple_value > 0:
    return simple_value
  else:
    return 1

def _BarGraphHeight(bar_count):
  # TODO(tstromberg): Fix hardcoding.
  proposed_height = 52 + (bar_count*13)
  if proposed_height > CHART_HEIGHT:
    return CHART_HEIGHT
  else:
    return proposed_height


def PerRunDurationBarGraph(run_data, scale=None):
  """Output a base64-encoded PNG showing per-run durations."""
  max_run_avg = -1
  runs = {}
  ns_names = []

  for (ns, run_averages) in run_data:
    ns_names.append(ns)
    for run_num, run_avg in enumerate(run_averages):
      if run_num not in runs:
        runs[run_num] = []
      runs[run_num].append(run_avg)
      if run_avg > max_run_avg:
        max_run_avg = run_avg

  if max_run_avg < 0:
    print("No decent data to graph: %s" % run_data)
    return None

  if not scale:
    scale = int(math.ceil(max_run_avg / 5) * 5)

  # Create matplotlib figure
  bar_count = sum(len(runs[r]) for r in runs)
  height = _BarGraphHeight(bar_count) / 100.0
  fig, ax = plt.subplots(figsize=(CHART_WIDTH/100.0, height))

  y_positions = list(range(len(ns_names)))

  if len(runs) == 1:
    ax.barh(y_positions, runs[0], color='#4684ee')
  else:
    # Multiple runs - group bars
    bar_height = 0.8 / len(runs)
    for run_num in sorted(runs):
      offset = (run_num - len(runs)/2 + 0.5) * bar_height
      positions = [y + offset for y in y_positions]
      color = '#' + DarkenHexColorCode('4684ee', run_num*3)
      ax.barh(positions, runs[run_num], bar_height,
              label=f'Run {run_num+1}', color=color)
    ax.legend()

  ax.set_yticks(y_positions)
  ax.set_yticklabels(ns_names)
  ax.set_xlabel('Duration in ms.')
  ax.set_xlim(0, scale)
  ax.grid(axis='x', alpha=0.3)
  plt.tight_layout()

  return _FigureToDataUri(fig)


def MinimumDurationBarGraph(fastest_data, scale=None):
  """Output a base64-encoded PNG showing minimum-run durations."""
  durations = [x[1] for x in fastest_data]
  ns_names = [x[0].name for x in fastest_data]

  slowest_time = fastest_data[-1][1]
  if not scale:
    scale = int(math.ceil(slowest_time / 5) * 5)

  # Create matplotlib figure
  height = _BarGraphHeight(len(ns_names)) / 100.0
  fig, ax = plt.subplots(figsize=(CHART_WIDTH/100.0, height))

  y_positions = list(range(len(ns_names)))
  ax.barh(y_positions, durations, color='#4684ee')

  ax.set_yticks(y_positions)
  ax.set_yticklabels(ns_names)
  ax.set_xlabel('Duration in ms.')
  ax.set_xlim(0, scale)
  ax.grid(axis='x', alpha=0.3)
  plt.tight_layout()

  return _FigureToDataUri(fig)


def _MakeCumulativeDistribution(run_data, x_chunk=1.5, percent_chunk=3.5):
  """Given run data, generate a cumulative distribution (X in Xms).

  Args:
    run_data: a tuple of nameserver and query durations
    x_chunk: How much value should be chunked together on the x-axis
    percent_chunk: How much percentage should be chunked together on y-axis.

  Returns:
    A list of tuples of tuples: [(ns_name, ((percentage, time),))]

  We chunk the data together to intelligently minimize the number of points
  that need to be passed to the Google Chart API later (URL limitation!)
  """
  # TODO(tstromberg): Use a more efficient algorithm. Pop values out each iter?
  dist = []
  for (ns, results) in run_data:
    if not results:
      continue
    
    host_dist = [(0, 0)]
    max_result = max(results)
    chunk_max = min(results)
    # Why such a low value? To make sure the delta for the first coordinate is
    # always >percent_chunk. We always want to store the first coordinate.
    last_percent = -99

    while chunk_max < max_result:
      values = [x for x in results if x <= chunk_max]
      percent = float(len(values)) / float(len(results)) * 100

      if (percent - last_percent) > percent_chunk:
        host_dist.append((percent, max(values)))
        last_percent = percent

      # TODO(tstromberg): Think about using multipliers to degrade precision.
      chunk_max += x_chunk

    # Make sure the final coordinate is exact.
    host_dist.append((100, max_result))
    dist.append((ns, host_dist))
  return dist


def _MaximumRunDuration(run_data):
  """For a set of run data, return the longest duration.

  Args:
    run_data: a tuple of nameserver and query durations

  Returns:
    longest duration found in runs_data (float)
  """
  times = [x[1] for x in run_data]
  return max(itertools.chain(*times))


def _SortDistribution(a, b):
  """Sort distribution graph by nameserver name."""
  # Python 3: cmp() builtin was removed, use manual comparison
  # Handle None values - treat None as less than any value
  a_sys = a[0].system_position
  b_sys = b[0].system_position
  if a_sys is None and b_sys is None:
    sys_pos_cmp = 0
  elif a_sys is None:
    sys_pos_cmp = 1  # a is None, so b > a
  elif b_sys is None:
    sys_pos_cmp = -1  # b is None, so a > b
  else:
    sys_pos_cmp = (b_sys > a_sys) - (b_sys < a_sys)

  if sys_pos_cmp:
    return sys_pos_cmp

  preferred_cmp = (b[0].is_keeper > a[0].is_keeper) - (b[0].is_keeper < a[0].is_keeper)
  if preferred_cmp:
    return preferred_cmp

  return (a[0].name > b[0].name) - (a[0].name < b[0].name)


def DistributionLineGraph(run_data, scale=None, sort_by=None):
  """Return a base64-encoded PNG showing duration distribution per ns."""
  distribution = _MakeCumulativeDistribution(run_data)
  colors = ['#' + c for c in BASE_COLORS[0:len(distribution)]]

  if not sort_by:
    sort_by = _SortDistribution

  max_value = _MaximumRunDuration(run_data)
  if not scale:
    scale = max_value
  elif scale < max_value:
    max_value = scale

  # Create matplotlib figure
  fig, ax = plt.subplots(figsize=(CHART_WIDTH/100.0, CHART_HEIGHT/100.0))

  import functools
  for idx, (ns, xy_pairs) in enumerate(sorted(distribution, key=functools.cmp_to_key(sort_by))):
    label = ns.name if len(ns.name) > 1 else ns.ip
    x = []
    y = []
    for (percentage, duration) in xy_pairs:
      if duration > max_value:
        # Add one point past max and stop
        x.append(max_value)
        y.append(percentage)
        break
      x.append(duration)
      y.append(percentage)

    color = colors[idx % len(colors)]
    ax.plot(x, y, label=label, color=color, linewidth=2)

  ax.set_xlabel('Duration in ms')
  ax.set_ylabel('Percentage (%)')
  ax.set_xlim(0, max_value)
  ax.set_ylim(0, 100)
  ax.grid(True, alpha=0.3)
  ax.legend(loc='lower right', fontsize=8)
  plt.tight_layout()

  return _FigureToDataUri(fig)
