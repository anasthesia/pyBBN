"""
## Photon universe test

<img src="plots.svg" width=100% />

This test checks that in the photon universe:

  * $a * T$ is conserved exactly.
  * $a \propto t^{1/2}$

[Log file](log.txt)

"""

import numpy

from particles import Particle
from evolution import Universe
from library.SM import particles as SMP
from common import Params, UNITS


T_final = 100 * UNITS.keV
params = Params(T=100 * UNITS.MeV,
                dy=0.05)

universe = Universe(params=params, folder="tests/photon_universe")

photon = Particle(**SMP.photon)

universe.add_particles([photon])
universe.evolve(T_final)

initial_aT = universe.data['aT'][0]
print "a * T is conserved: {}".format(all([initial_aT == value for value in universe.data['aT']]))
initial_a = universe.data['a'][len(universe.data['a'])/2]
initial_t = universe.data['t'][len(universe.data['a'])/2] / UNITS.s
last_a = universe.data['a'].iloc[-1]
last_t = universe.data['t'].iloc[-1] / UNITS.s

print "a scaling discrepancy is: {:.2f}%"\
    .format(100 * (last_a / initial_a / numpy.sqrt(last_t / initial_t) - 1))

universe.graphics.save(__file__)

raw_input("...")
