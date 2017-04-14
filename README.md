# HANS

HANS is a musical experiment, which focuses on the possibilities of
human – computer musical interactions in artistic works. The three
main pillars of this project are the following: (1) computer as an
autonomous actor, (2) computer network as a platform for
musician–audience interactions, and (3) computers as musical
instruments.

HANS is an autonomous [computer program](HANS/util/) that is capable
of playing together with human actors interactively. The program
listens to musicians and via its adaptive, self-controlling artificial
intelligence actively participates in performance by managing its
internal sampler and effect chain.

HANS involves massive softwarization of redesigning existing musical
instruments such as the [virtual theremin](HANS/util/theremin.py) or
the [drum module](HANS/util/drum/).

HANS is also a free improvising noisy experimental abstract electronic
band with computers, electric bass zither, drums, synths and other
instruments.

## Links

* [bandcamp](https://hans-music.bandcamp.com)
* [facebook](https://www.facebook.com/hansexperiment)
* [youtube](https://www.youtube.com/channel/UCbEil33Hz9sZZZ9DxmT1d_Q)

# Installation

## Dependencies

Recommended:

* [Python-Pyo>=0.7.6](http://ajaxsoundstudio.com/software/pyo/)

Suggested:

* [JACK Audio Connection Kit](http://www.jackaudio.org/downloads/)
* [wxPython](https://wxpython.org)
* [Flask](http://flask.pocoo.org)

## Prepare Samples

Create a directory for your samples with the following subdirectories:

* Beep
* Human
* Machine
* Music
* Nature
* Other

Copy your samples to the specific subdirectory. Samples must be in
aiff format.

## Musical Instruments

The preparations of the software musical instruments vary. Please,
take a look at their source code.

# Usage

HANS follows a basic client-server architecture. It provides various
clients: a web interface on which the audience can signal the server,
and a graphical user interface on which various parameters of the
server's artificial intelligence can be set.

## Start Your Audio and Midi System

Plug in your MIDI device and start your preferred audio system
(e.g. jack).

## Run the Server

Important: on non-Windows operating systems the server requires JACK
to access the audio system.

Server configuration can be done via command line arguments, however,
the MIDI input channel can be set interactively.

To start the server listening on all MIDI input channel issue a
similar command:

``` bash
cd HANS/src/server
python2 hans-server.py -m 99 -s /path/to/your/samples
```
