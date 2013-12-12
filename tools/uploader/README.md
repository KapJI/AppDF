# appdf-publisher

Publisher for [AppDF](https://github.com/onepf/AppDF).

## Install

1) Ensure "pip" is installed. If not try this:
```shell
easy_install pip
```

2) Uploader uses webkit-server (requires Qt webkit) and xml libraries, so ensure you have following packets installed:
```shell
libxml
libxslt
qt5-devel	(contains webkit)
python-devel (Python.h is required for building bindings)
```

Install it using your system installer:
Linux: 
```shell
sudo apt-add-repository ppa:ubuntu-sdk-team/ppa
sudo apt-get update
sudo apt-get install qtdeclarative5-dev
...
```
MacOS X:
```shell
brew install qt5
...
```

3) Ensure "qmake" use Qt5:
```shell
qmake --version
```

4) Call "make" to install webkit-server and other requirements
```shell
make
```
Webkit-server and other stuff should be installed

## Usage

Run publisher 

```shell
python appdf --username GOOGLE_PLAY_EMAIL --password GOOGLE_PLAY_PASSWORD PATH_TO_APPDF
```