# Can of Proxy

*Note: socks protocol is not supported because of the lack of free proxies*

## Installation

```bash
pip install can-of-proxy
```

usage:

```python
import can_of_proxy as cop
```

## Description

### AutoCan

Like the name says, it creates a proxy can automatically for you. It will auto refresh the can if the proxys don't work
anymore.
And remove proxies from the list if they are not working.
This script does maintain the can op proxies for you.
Best use for looping scraping scripts or for easy use of proxy.

**There are arguments you can pass to the AutoCan for Configuration:**

```python
auto_can = cop.AutoCan()
```

### Can

```python
can = cop.Can()
```