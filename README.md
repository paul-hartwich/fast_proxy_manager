# Can of Proxy

[![CodeFactor](https://www.codefactor.io/repository/github/paul-hartwich/can_of_proxy/badge)](https://www.codefactor.io/repository/github/paul-hartwich/can_of_proxy)

*Note: Please use this library with caution.
Don't use this library for illegal activities, we
will not take responsibility for any misuse of this library.*

## Installation

*Python 3.12.8 is recommended and is the one worked with. But others will probably work too.*

```bash
pip install can-of-proxy # currently not working
```

## Description/Usage

### AutoCan

Like the name says, it creates a proxy-can automatically for you.
It will auto refresh the can if the proxys don't work
anymore.
And remove proxies from the list if they are not working.
This script does maintain the can proxies for you entirely.
Best use for looping scraping scripts (legal) or for easy/fast use of proxy.

**Example:**

```python
import can_of_proxy as cop

auto_can = cop.AutoCan()
```

### Can

This is the main class of the library.
It is the base class for the AutoCan but with the need of manual action to make
it work properly.
It is still simple to use but needs some manual "work" (can be automated) to maintain the proxies.

**Example:**

```python
import can_of_proxy as cop

can = cop.Can()
```
