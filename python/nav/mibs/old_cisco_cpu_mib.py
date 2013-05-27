#
# Copyright (C) 2013 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
from twisted.internet import defer
from nav.mibs import mibretriever


class OldCiscoCpuMib(mibretriever.MibRetriever):
    from nav.smidumps.old_cisco_cpu_mib import MIB as mib

    @defer.inlineCallbacks
    def get_avgbusy(self):
        avgbusy5 = yield self.get_next('avgBusy5')
        avgbusy1 = yield self.get_next('avgBusy1')
        if avgbusy5 or avgbusy1:
            defer.returnValue(dict(cpu=(avgbusy5, avgbusy1)))
