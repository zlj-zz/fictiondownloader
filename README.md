# noval

```
                       _
 _ __   _____   ____ _| |
| '_ \ / _ \ \ / / _` | |
| | | | (_) \ V / (_| | |
|_| |_|\___/ \_/ \__,_|_| Configurable novel downloader.
```

## Usage

`noval -h` to get help message.

```
usage: noval [-h] [-n fiction_name] [--conf path] [--save-to path] [--range RANGE] [--split SPLIT | --append] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -n fiction_name, --name fiction_name
                        custom fiction name.
  --conf path           custom config path.
  --save-to path        custom fiction save path.
  --range RANGE         Download chapter range, like: --range "10,20"
  --split SPLIT         Download segmented storage.
  --append              Whether it is in append mode. It is recreated by default.
  -v, --version         Show version and exit.
```

## Installation

### Pip

```
pip3 install noval --upgrade
```

### Source

```
git clone --dep 1 https://github.com/zlj-zz/noval.git
cd noval && python3 setup.py install
```
