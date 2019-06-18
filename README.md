# HANS

HANS is a musical experiment, which focuses on the possibilities of
human – computer musical interactions in artistic works. The three
main pillars of this project are the following: (1) computer as an
autonomous actor, (2) computer network as a platform for
musician–audience interactions, and (3) computers as musical
instruments.

HANS is an autonomous [computer program](src/) that is capable
of playing together with human actors interactively. The program
listens to musicians and via its adaptive, self-controlling artificial
intelligence actively participates in performance by managing its
internal sampler and effect chain.

HANS involves massive softwarization of redesigning existing musical
instruments such as the [virtual theremin](util/theremin.py) or
the [drum module](util/drum/).

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
* [python-osc>=1.6.7](https://github.com/attwad/python-osc)
* [wxPython](https://wxpython.org)
* [Flask](http://flask.pocoo.org)

## Clone the Repository

```sh
git clone https://github.com/levaitamas/HANS.git
```

## Prepare Samples

Create a directory for your samples with the following sub-directories:

| Subdir    | Examples                                     |
| :---:     | :---                                         |
| `Beep`    | alarms, signals (microwave, tram), DTMF      |
| `Human`   | speech, spoken words, yawns                  |
| `Machine` | washing machine, electric razor, transformer |
| `Music`   | short melodies, single notes                 |
| `Nature`  | soundscapes, birds, water                    |
| `Other`   | all the WTF stuff                            |

```sh
cd HANS/src/server
mkdir samples
cd samples
mkdir Beep Human Machine Music Nature Other
```

Copy your `aiff` samples to the specific directories.

## Musical Instruments

The preparations of the software musical instruments vary. For further
information check the source code:

- [drum module](util/drum/)

- [virtual theremin](util/theremin.py)

# Usage

HANS follows a client-server architecture. It provides various
clients: a web interface on which the audience can trigger the server,
and a graphical user interface on which OSC triggers can be sent or
parameters of the server's AI component can be set.

## 1. Start Your Audio and Midi System

Plug in your MIDI device and start your preferred audio system
(e.g. jack).

Alternatively you can trigger HANS via its OSC interface at `/hans/midi`.

## 2. Run the Server

**Important**: on non-Windows operating systems the server uses JACK to
access the audio system.

The server is configurable with its command line arguments. The MIDI
input channel can be set interactively.

To start the server listening on all MIDI input channel use a similar
command:

```sh
cd HANS/src/server
python3 hans-server.py -m 99
```

# License
HANS is a free software and licensed under [(GPLv3+)](LICENSE).
