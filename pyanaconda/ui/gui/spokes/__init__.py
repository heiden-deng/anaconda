# Base classes for Spokes
#
# Copyright (C) 2011  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
# Red Hat Author(s): Chris Lumens <clumens@redhat.com>
#

from pyanaconda.ui.gui import UIObject, collect

__all__ = ["Spoke", "StandaloneSpoke", "NormalSpoke", "PersonalizationSpoke",
           "collect_spokes"]

class Spoke(UIObject):
    """A Spoke is a single configuration screen.  There are several different
       places where a Spoke can be displayed, each of which will have its own
       unique class.  A Spoke is typically used when an element in the Hub is
       selected but can also be displayed before a Hub or between multiple
       Hubs.

       What amount of the UI layout a Spoke provides depends upon where it is
       to be shown.  Regardless, the UI of a Spoke should be given by an
       interface description file like glade as often as possible, though this
       is not a strict requirement.

       Class attributes:

       category   -- Under which SpokeCategory shall this Spoke be displayed
                     in the Hub?  This is a reference to a Hub subclass (not an
                     object, but the class itself).  If no category is given,
                     this Spoke will not be displayed.  Note that category is
                     not required for any Spokes appearing before or after a
                     Hub.
       icon       -- The name of the icon to be displayed in the SpokeSelector
                     widget corresponding to this Spoke instance.  If no icon
                     is given, the default from SpokeSelector will be used.
       title      -- The title to be displayed in the SpokeSelector widget
                     corresponding to this Spoke instance.  If no title is
                     given, the default from SpokeSelector will be used.
    """
    category = None
    icon = None
    title = None

    def __init__(self, data, devicetree, payload, instclass):
        """Create a new Spoke instance.

           The arguments this base class accepts defines the API that spokes
           have to work with.  A Spoke does not get free reign over everything
           in the anaconda class, as that would be a big mess.  Instead, a
           Spoke may count on the following:

           ksdata       -- An instance of a pykickstart Handler object.  The
                           Spoke uses this to populate its UI with defaults
                           and to pass results back after it has run.
           devicetree   -- An instance of storage.devicetree.DeviceTree.  This
                           is useful for determining what storage devices are
                           present and how they are configured.
           payload      -- An instance of a packaging.Payload subclass.  This
                           is useful for displaying and selecting packages to
                           install, and in carrying out the actual installation.
           instclass    -- An instance of a BaseInstallClass subclass.  This
                           is useful for determining distribution-specific
                           installation information like default package
                           selections and default partitioning.
        """
        if self.__class__ is Spoke:
            raise TypeError("Spoke is an abstract class")

        UIObject.__init__(self, data)
        self.devicetree = devicetree
        self.payload = payload
        self.instclass = instclass

    def apply(self):
        """Apply the selections made on this Spoke to the object's preset
           data object.  This method must be provided by every subclass.
        """
        raise NotImplementedError

    @property
    def completed(self):
        """Has this spoke been visited and completed?  If not, a special
           warning icon will be shown on the Hub and installation will not be
           allowed to proceed.
        """
        return False

    @property
    def status(self):
        """Given the current status of whatever this Spoke configures, return
           a very brief string.  The purpose of this is to display something
           on the Hub under the Spoke's title so the user can tell at a glance
           how things are configured.
        """
        raise NotImplementedError

class StandaloneSpoke(Spoke):
    """A StandaloneSpoke is a Spoke subclass that is displayed apart from any
       Hub.  It is suitable to be used as a Welcome screen.

       From a layout perspective, a StandaloneSpoke provides a full screen
       interface.  However, it also provides navigation information at the top
       and bottom of the screen that makes it look like the StandaloneSpoke
       fits into some other UI element.

       Class attributes:

       preForHub/postForHub   -- A reference to a Hub subclass this Spoke is
                                 either a pre or post action for.  Only one of
                                 these may be set at a time.  Note that all
                                 post actions will be run for one hub before
                                 any pre actions for the next.
       priority               -- This value is used to sort pre and post
                                 actions.  The lower a value, the earlier it
                                 will be run.  So a value of 0 for a post action
                                 ensures it will run immediately after a Hub,
                                 while a value of 0 for a pre actions means
                                 it will run as the first thing.
    """
    preForHub = None
    postForHub = None

    priority = 100

    def __init__(self, data, devicetree, payload, instclass):
        """Create a StandaloneSpoke instance."""
        if self.__class__ is StandaloneSpoke:
            raise TypeError("StandaloneSpoke is an abstract class")

        if self.preForHub and self.postForHub:
            raise AttributeError("StandaloneSpoke instance %s may not have both preForHub and postForHub set" % self)

        Spoke.__init__(self, data, devicetree, payload, instclass)

    def _on_continue_clicked(self, cb):
        self.apply()
        cb()

    def register_event_cb(self, event, cb):
        if event == "continue":
            self.window.connect("continue-clicked", lambda *args: self._on_continue_clicked(cb))
        elif event == "quit":
            self.window.connect("quit-clicked", lambda *args: cb())

class NormalSpoke(Spoke):
    """A NormalSpoke is a Spoke subclass that is displayed when the user
       selects something on a Hub.  This is what most Spokes in anaconda will
       be based on.

       From a layout perspective, a NormalSpoke takes up the entire screen
       therefore hiding the Hub and its action area.  The NormalSpoke also
       provides some basic navigation information (where you are, what you're
       installing, how to get back to the Hub) at the top of the screen.
    """
    def __init__(self, data, devicetree, payload, instclass):
        """Create a NormalSpoke instance."""
        if self.__class__ is NormalSpoke:
            raise TypeError("NormalSpoke is an abstract class")

        Spoke.__init__(self, data, devicetree, payload, instclass)
        self.selector = None

    def check(self):
        """This method runs any special checks the spoke requires.  It will
           be run in a separate thread and is triggered by the Back button
           being clicked.  Only one check thread per spoke may run at a time.
           Should the check thread not finish before the user clicks Continue
           on the hub, the hub will display a dialog while it finishes.

           This method should first clean up from any previous runs, even
           those terminated prematurely.
        """
        pass

    @property
    def ready(self):
        """Returns True if the Spoke has all the information required to be
           displayed.  Almost all spokes should keep the default value here.
           Only override this method if the Spoke requires some potentially
           long-lived process (like storage probing) before it's ready.
        """
        return True

    def on_back_clicked(self, window):
        from gi.repository import Gtk
        from pyanaconda.threads import threadMgr
        from threading import Thread

        self.window.hide()
        Gtk.main_quit()

        # A spoke may only have one check thread running at a time.  If one's
        # already running, we must ask it to kill itself (there's no API in
        # Python for killing a thread) and then wait for it to exit.
        threadName = "Ana" + self.title.replace(" ", "") + "Check"
        thr = threadMgr.get(threadName)
        if thr:
            thr.kill = True
            thr.join()

        # And now start a new instance of the check thread.
        threadMgr.add(Thread(name=threadName, target=self.check))

class PersonalizationSpoke(Spoke):
    """A PersonalizationSpoke is a Spoke subclass that is displayed when the
       user selects something on the Hub during package installation.

       From a layout perspective, a PersonalizationSpoke takes up the middle
       of the screen therefore hiding the Hub but leaving its action area
       displayed.  This allows the user to continue seeing package installation
       progress being made.  The PersonalizationSpoke also provides the same
       basic navigation information at the top of the screen as a NormalSpoke.
    """
    def __init__(self, data, devicetree, payload, instclass):
        """Create a PersonalizationSpoke instance."""
        if self.__class__ is PersonalizationSpoke:
            raise TypeError("PersonalizationSpoke is an abstract class")

        Spoke.__init__(self, data, devicetree, payload, instclass)

def collect_spokes(category):
    """Return a list of all spoke subclasses that should appear for a given
       category.
    """
    return collect("spokes", lambda obj: hasattr(obj, "category") and obj.category != None and obj.category.__name__ == category)