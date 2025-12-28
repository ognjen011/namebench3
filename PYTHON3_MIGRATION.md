# Python 3 Migration Changes

This document outlines all changes made to migrate namebench from Python 2 to Python 3.

## Version Update
- Updated version from `1.5-DEVEL` to `2.0-py3`

## Python Version Requirements
- **Old**: Python 2.4-2.6
- **New**: Python 3.6+

## Major Changes

### 1. Print Statements → Print Functions
Converted all `print` statements to `print()` functions throughout the codebase.

**Files affected**: All Python files in the project
```python
# Before
print "Hello"

# After
print("Hello")
```

### 2. Import Statement Updates
Updated all renamed modules to their Python 3 equivalents:

| Python 2 | Python 3 |
|----------|----------|
| `ConfigParser` | `configparser` |
| `Queue` | `queue` |
| `Tkinter` | `tkinter` |
| `tkFont` | `tkinter.font` |
| `tkMessageBox` | `tkinter.messagebox` |
| `StringIO` | `io.StringIO` |
| `urllib` | `urllib.parse` |
| `httplib` | `http.client` |

### 3. Exception Handling Syntax
Updated exception handling to Python 3 syntax:
```python
# Before
except Exception, e:

# After
except Exception as e:
```

### 4. Internal Imports
Converted all internal package imports to relative imports:
```python
# Before
import config

# After
from . import config
```

### 5. Dictionary Methods
Updated dictionary iteration methods:
```python
# Before
dict.iteritems()
dict.iterkeys()
dict.itervalues()

# After
dict.items()
dict.keys()
dict.values()
```

### 6. Built-in Function Changes
- Replaced `basestring` with `str`
- Converted `range()` returns to lists where needed: `list(range(...))`
- Removed `cmp()` function, replaced with manual comparison: `(a > b) - (a < b)`
- Updated `sorted()` to use `functools.cmp_to_key()` instead of `cmp` parameter

### 7. String/Bytes Handling
- Updated file reading modes (text vs binary)
- Added proper encoding/decoding for bytes in network operations
- Fixed httplib2 bytes handling

### 8. DNS Library (dnspython) API Changes
Updated DNS response handling for dnspython 2.x:
```python
# Before
response.answer[0].items[0]

# After
list(response.answer[0].items)[0]
```

### 9. ConfigParser Changes
Added `interpolation=None` to all ConfigParser instances to handle '%' characters:
```python
config = configparser.ConfigParser(interpolation=None)
```

### 10. Chart Generation System
**Major Overhaul**: Replaced Google Chart API with matplotlib for local chart generation.

**Old System**:
- Used Google Chart API (`chart.apis.google.com`)
- Generated URLs to external chart service
- Service has been shut down

**New System**:
- Uses matplotlib for local chart generation
- Generates base64-encoded PNG images
- Embeds images directly in HTML reports as data URIs
- Works completely offline

## File-by-File Changes

### Core Entry Point
**namebench.py**
- Updated version check from Python 2.4-2.6 to Python 3.6+
- Changed `import Tkinter` to `import tkinter`
- Converted all print statements to print() functions

### Configuration Module
**libnamebench/config.py**
- Changed `import ConfigParser` to `import configparser`
- Changed `import StringIO` to `from io import StringIO`
- Added `interpolation=None` to all ConfigParser instances
- Fixed bytes/string handling for remote config downloads
- Converted to relative imports

### UI Modules
**libnamebench/tk.py**
- Changed `import Queue` to `import queue`
- Changed `import Tkinter` to `from tkinter import *`
- Changed `import tkFont` to `from tkinter import font as tkFont`
- Changed `import tkMessageBox` to `from tkinter import messagebox as tkMessageBox`
- Fixed Queue references

**libnamebench/cli.py**
- Converted 17 print statements to print() functions
- Converted to relative imports

### Data and Networking
**libnamebench/data_sources.py**
- Changed `import ConfigParser` to `import configparser`
- Added `interpolation=None` to ConfigParser instances
- Fixed file reading: changed from binary to text mode with UTF-8 encoding

**libnamebench/site_connector.py**
- Changed `import urllib` to `import urllib.parse`
- Changed `urllib.urlencode()` to `urllib.parse.urlencode()`

**libnamebench/charts.py**
- Changed `import urllib` to `import urllib.parse`
- Changed `urllib.quote_plus()` to `urllib.parse.quote_plus()`
- Fixed range() issue: `list(range(0, scale, tick)) + [scale]`
- Added functools for cmp_to_key conversion
- **Complete rewrite of chart generation functions**:
  - `PerRunDurationBarGraph()` - Now uses matplotlib
  - `MinimumDurationBarGraph()` - Now uses matplotlib
  - `DistributionLineGraph()` - Now uses matplotlib
  - Added `_FigureToDataUri()` helper for base64 encoding
- Fixed regex warning by using raw string: `r'\w\w'`
- Fixed `cmp()` function removal with manual comparison
- Added None handling for comparisons

### Core Functionality
**libnamebench/benchmark.py**
- Changed `import Queue` to `import queue`
- Fixed all Queue references

**libnamebench/nameserver_list.py**
- Changed `import Queue` to `import queue`
- Fixed all Queue references

**libnamebench/nameserver.py**
- Fixed exception syntax throughout
- Fixed DNS response handling for dnspython 2.x:
  - `GetTxtRecordWithDuration()` - Convert items to list
  - `GetIpFromNameWithDuration()` - Convert items to list

### Third-party Libraries
**nb_third_party/graphy/**
- Changed `basestring` to `str`
- Changed `.iteritems()` to `.items()`
- Changed `.iterkeys()` to `.keys()`
- Changed `urllib.quote()` to `urllib.parse.quote()`
- Added `import urllib.parse`

**nb_third_party/graphy/backends/google_chart_api/util.py**
- Changed `import urllib` to `import urllib.parse`
- Changed `urllib.quote()` to `urllib.parse.quote()`

## Disabled Third-party Libraries
The following bundled libraries were disabled in favor of system Python 3 versions:
- httplib2 (bundled version too old for Python 3)
- dns (using system dnspython)
- jinja2 (using system version)
- simplejson (using system version)

## New Dependencies
Added matplotlib for chart generation:
```bash
pip3 install matplotlib
```

## Configuration Files
No changes required to configuration files.

## Testing
All major functionality has been tested:
- DNS benchmarking works correctly
- Report generation (HTML and CSV) works
- Charts are generated and embedded in HTML reports
- All nameserver operations work correctly

## Known Issues
None at this time.

## Migration Summary
- **60+ files** converted from Python 2 to Python 3
- **All print statements** converted to functions
- **All imports** updated for Python 3
- **All exception handling** updated to Python 3 syntax
- **DNS library** API changes handled
- **Chart generation** completely rewritten with matplotlib
- **Version** updated to 2.0-py3

## Breaking Changes
1. **Python Version**: Now requires Python 3.6+ (was Python 2.4-2.6)
2. **Dependencies**: Requires matplotlib (new dependency)
3. **Charts**: Generated differently (matplotlib instead of Google Chart API)

## Benefits of Python 3 Migration
1. **Modern Python**: Uses current Python version with active support
2. **Better Performance**: Python 3 generally faster than Python 2
3. **Security**: Python 2 is no longer maintained or receiving security updates
4. **Offline Charts**: Charts work without external API dependency
5. **Future-proof**: Compatible with modern libraries and tools

## Notes
This migration was completed in December 2025. The original namebench was written for Python 2.4-2.6 and has been successfully updated to work with Python 3.6+.

All functionality has been preserved, with the addition of improved chart generation using matplotlib instead of the deprecated Google Chart API.

## Python 3.13+ Compatibility

### CGI Module Removal
The `cgi` module was removed in Python 3.13. Updated the code to use the `html` module instead.

**File**: `nb_third_party/graphy/backends/google_chart_api/util.py`

**Change**:
```python
# Before
import cgi
...
url = cgi.escape(url, quote=True)

# After
import html
...
url = html.escape(url, quote=True)
```

The `html.escape()` function is the direct replacement for `cgi.escape()` and provides the same functionality.
