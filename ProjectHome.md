GPhotoFrame is a photo frame gadget.

  * Local folders
  * [F-Spot](http://f-spot.org/) database
  * [Shotwell](http://yorba.org/shotwell/) database
  * [Facebook](http://www.facebook.com/) API
  * [Flickr](http://www.flickr.com/) API
  * [Picasa Web Album](http://picasaweb.google.com/) API
  * ~~[Tumblr](http://www.tumblr.com/dashboard) API~~
  * [Haikyo Clock](http://www.madin.jp/haikyo/)
  * RSS



_Translate gphotoframe: you can check the [gphotoframe transifex page](http://www.transifex.net/projects/p/gphotoframe/)._

![http://gphotoframe.googlecode.com/hg/help/C/figures/gphotoframe.png](http://gphotoframe.googlecode.com/hg/help/C/figures/gphotoframe.png)

# Latest News #

## 2.0.2 release (2015-03-27) ##

  * Added AppData ([issue 113](https://code.google.com/p/gphotoframe/issues/detail?id=113)).
  * Fixed bugs.

## 2.0.1 release (2014-11-30) ##

  * Added new Dutch translation by Heimen Stoffels.
  * Fixed bugs.

## 2.0 release (2014-08-12) ##

  * Added support for GTK 3 ([issue #99](https://code.google.com/p/gphotoframe/issues/detail?id=#99)).
  * Disabled Tumblr plugin temporally.
  * Fixed bugs.

## 1.5.1 release (2012-02-24) ##

  * Changed the product name to GPhotoFrame ([issue #104](https://code.google.com/p/gphotoframe/issues/detail?id=#104)).
  * Added Spanish translation. Thanks jorjuardo!

## 1.5 release (2012-01-14) ##

  * Improved loading speed for large image files ([issue #87](https://code.google.com/p/gphotoframe/issues/detail?id=#87)).
  * Added support for Facebook album selection ([issue #98](https://code.google.com/p/gphotoframe/issues/detail?id=#98)).
  * Added support for map on photo with python-champlain ([issue #100](https://code.google.com/p/gphotoframe/issues/detail?id=#100)).

### New added recommends ###

  * python-champlain

## 1.4.1 release (2011-11-27) ##

  * Added a workaround for an Xfwm gravity problem ([issue #97](https://code.google.com/p/gphotoframe/issues/detail?id=#97)).
  * Added new French translation by MathieuMD.


## 1.4 release (2011-07-03) ##

  * Added support for 'Share on Tumblr'.
  * Added new option for 'Exclude hidden files and folders' to Folder plugin ([issue #92](https://code.google.com/p/gphotoframe/issues/detail?id=#92)).
  * Added new Swedish translation by Daniel Nylander.
  * Added new Ukrainian translation by Sergiy Gavrylov.

## 1.3 release (2011-04-16) ##

  * Added support for Facebook ([issue #89](https://code.google.com/p/gphotoframe/issues/detail?id=#89)).
  * Added support for Shotwell ban icon.

# Installation #

Download gphotoframe and extract it.

You can install with the setup script.

> sudo python ./setup.py install --force

> sudo gconf-schemas --register gphotoframe.schemas

Or, you can launch without installation. (Some functions are restricted.)

> ./gphotoframe

## Depends ##

  * [PyGTK](http://www.pygtk.org/)
  * [Twisted (twisted.internet, twisted.web)](http://twistedmatrix.com/trac/)
  * [PyXDG](http://www.freedesktop.org/wiki/Software/pyxdg)
  * [Python-Distutils-Extra](http://www.glatzor.de/projects/python-distutils-extra/): for installation
  * python-oauth
  * gnome-doc-utils: for help documentation
  * pkg-config: for help documentation


## Recommends ##

  * [feedparser](http://www.feedparser.org/): for RSS
  * [gnome-python-desktop](http://ftp.gnome.org/pub/GNOME/sources/gnome-python-desktop) (gnomekeyring): for Picasa Web, Tumblr
  * [python-clutter-gtk](http://www.clutter-project.org/)
  * python-libproxy: for Gnome Proxy Settings

## Suggests ##

  * [NumPy](http://numpy.scipy.org/): for RSS
  * python-dbus: for checking session idle status
  * jQuery: for photo history html

# Translations #

You can check the [gphotoframe transifex page](http://www.transifex.net/projects/p/gphotoframe/).


# Screenshots #

![http://www.tsurukawa.org/~yendo/blog/images/090422-gpf-prefs.png](http://www.tsurukawa.org/~yendo/blog/images/090422-gpf-prefs.png)