# Copyright (C) 2011 Bruno Finger <bruno.finger12@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
from xl.nls import gettext as _

name = _('Last.fm Buttons')
basedir = os.path.dirname(os.path.realpath(__file__))
ui = os.path.join(basedir + '/data', "preferences_pane.ui")
