"""
## CnuB temperature test

<img src="plots.svg" width=100% />

This test checks that in the universe filled with photons, neutrons, protons, electrons\
and neutrinos (which decouple at temperatures around $\sim 3 MeV$:

  * $a * T$ is not conserved by a factor around `1.401` in presence of additional species

At temperatures $\sim 1 MeV$ electron-positron pairs annihilate, effectively disappearing from the\
plasma. This leads to increasing of the entropy and plasma temperature approximately `1.401` times.

[Log file](log.txt)


"""

import os
from particles import Particle
from evolution import Universe
from common import Params, UNITS
from semianalytic import step_monitor
from library.SM import particles as SMP


folder = os.path.split(__file__)[0]

params = Params(T=10 * UNITS.MeV,
                dy=0.025)
T_final = 0.0008 * UNITS.MeV


Particles = []
photon = Particle(**SMP.photon)
neutron = Particle(**SMP.hadrons.neutron)
proton = Particle(**SMP.hadrons.proton)
neutrino_e = Particle(**SMP.leptons.neutrino_e)
neutrino_mu = Particle(**SMP.leptons.neutrino_mu)
neutrino_tau = Particle(**SMP.leptons.neutrino_tau)
electron = Particle(**SMP.leptons.electron)
muon = Particle(**SMP.leptons.muon)
tau = Particle(**SMP.leptons.tau)

Particles += [
    photon,
    neutron,
    proton,
    neutrino_e,
    neutrino_mu,
    neutrino_tau,
    electron,
    muon,
    tau
]

universe = Universe(params=params, folder=folder)
universe.add_particles(Particles)
universe.init_kawano(electron=electron, neutrino=neutrino_e)
universe.step_monitor = step_monitor

T_final = 3 * UNITS.MeV
universe.evolve(T_final, export=False)
T_final = 0.0008 * UNITS.MeV
params.dy = 0.003125
universe.evolve(T_final)

from tests.plots import cosmic_neutrino_temperature
cosmic_neutrino_temperature(universe)

print """
    Cosmic photon background temperature is {:.3f} times bigger than cosmic neutrinos temperature.
    Relative error is {:.3f} %
    """.format(universe.params.aT / UNITS.MeV,
               (universe.params.aT / UNITS.MeV - 1.401) / 1.401 * 100)
