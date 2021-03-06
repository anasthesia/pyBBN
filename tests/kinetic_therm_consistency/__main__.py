"""
## Kinetics-thermodynamics consistency test

<img src="plots.svg" width=100% />
<img src="particles.svg" width=100% />

This test checks that active neutrinos do not get any non-equilibrium corrections at temperatures\
$\sim 50 \div 10 MeV$

[Log file](log.txt)
[Distribution functions](distributions.txt)


"""

import os
import numpy
import matplotlib

from plotting import plt
from particles import Particle
from library.SM import particles as SMP, interactions as SMI
from evolution import Universe
from common import UNITS, Params


folder = os.path.split(__file__)[0]

T_initial = 50. * UNITS.MeV
T_final = 10 * UNITS.MeV
params = Params(T=T_initial,
                dy=0.025)

universe = Universe(params=params, folder=folder)

photon = Particle(**SMP.photon)
electron = Particle(**SMP.leptons.electron)
neutrino_e = Particle(**SMP.leptons.neutrino_e)
neutrino_mu = Particle(**SMP.leptons.neutrino_mu)
neutrino_tau = Particle(**SMP.leptons.neutrino_tau)

universe.add_particles([
    photon,
    electron,
    neutrino_e,
    neutrino_mu,
    neutrino_tau,
])

neutrinos = [neutrino_e, neutrino_mu, neutrino_tau]
for neutrino in neutrinos:
    neutrino.decoupling_temperature = T_initial

universe.interactions += \
    SMI.neutrino_interactions(leptons=[electron], neutrinos=neutrinos)

if universe.graphics:
    from plotting import RadiationParticleMonitor
    universe.graphics.monitor([
        (neutrino_e, RadiationParticleMonitor),
        (neutrino_mu, RadiationParticleMonitor),
        (neutrino_tau, RadiationParticleMonitor)
    ])


universe.evolve(T_final)

universe.graphics.save(__file__)


""" ## Plots for comparison with articles """

plt.ion()

"""
### JCAP10(2012)014, Figure 9
<img src="figure_9.svg" width=100% /> """

plt.figure(9)
plt.title('Figure 9')
plt.xlabel('MeV/T')
plt.ylabel(u'aT')
plt.xscale('log')
plt.xlim(0.5, UNITS.MeV/universe.params.T)
plt.xticks([1, 2, 3, 5, 10, 20])
plt.axes().get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
plt.plot(UNITS.MeV / numpy.array(universe.data['T']), numpy.array(universe.data['aT']) / UNITS.MeV)
plt.show()
plt.savefig(os.path.join(folder, 'figure_9.svg'))

"""
### JCAP10(2012)014, Figure 10
<img src="figure_10.svg" width=100% />
<img src="figure_10_full.svg" width=100% /> """

plt.figure(10)
plt.title('Figure 10')
plt.xlabel('Conformal momentum y = pa')
plt.ylabel('f/f_eq')
plt.xlim(0, 20)

f_e = neutrino_e._distribution
feq_e = neutrino_e.equilibrium_distribution()
plt.plot(neutrino_e.grid.TEMPLATE/UNITS.MeV, f_e/feq_e, label="nu_e")

f_mu = neutrino_mu._distribution
feq_mu = neutrino_mu.equilibrium_distribution()
plt.plot(neutrino_mu.grid.TEMPLATE/UNITS.MeV, f_mu/feq_mu, label="nu_mu")

f_tau = neutrino_tau._distribution
feq_tau = neutrino_tau.equilibrium_distribution()
plt.plot(neutrino_tau.grid.TEMPLATE/UNITS.MeV, f_tau/feq_tau, label="nu_tau")

plt.legend()
plt.draw()
plt.show()
plt.savefig(os.path.join(folder, 'figure_10_full.svg'))

plt.xlim(0, 10)
plt.ylim(0.99, 1.06)
plt.draw()
plt.show()
plt.savefig(os.path.join(folder, 'figure_10.svg'))

# Distribution functions arrays
distributions_file = open(os.path.join(folder, 'distributions.txt'), "w")
numpy.savetxt(distributions_file, (f_e, feq_e, f_e/feq_e), header=str(neutrino_e),
              footer='-'*80, fmt="%1.5e")
numpy.savetxt(distributions_file, (f_mu, feq_mu, f_mu/feq_mu), header=str(neutrino_mu),
              footer='-'*80, fmt="%1.5e")
numpy.savetxt(distributions_file, (f_tau, feq_tau, f_tau/feq_tau), header=str(neutrino_tau),
              footer='-'*80, fmt="%1.5e")

distributions_file.close()

# Just to be sure everything is okay
import ipdb
ipdb.set_trace()

raw_input("...")
