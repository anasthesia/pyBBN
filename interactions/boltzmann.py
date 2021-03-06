# -*- coding: utf-8 -*-
import numpy
from common import integrators
from common.utils import PicklableObject


class DistributionFunctional(object):
    """ ## $\mathcal{F}(f_\alpha)$ functional """

    """ ### Naive form

        \begin{align}
            \mathcal{F} &= (1 \pm f_1)(1 \pm f_2) f_3 f_4 - f_1 f_2 (1 \pm f_3) (1 \pm f_4)
            \\\\ &= \mathcal{F}_B + \mathcal{F}_A
        \end{align}
    """

    def F_A(self, p, skip_index=None):
        """
        Forward reaction distribution functional term

        \begin{equation}
            \mathcal{F}_A = - f_1 f_2 (1 \pm f_3) (1 \pm f_4)
        \end{equation}

        :param skip_index: Particle to skip in the expression
        """
        temp = -1.

        for i, particle in enumerate(self.reaction):
            if skip_index is None or i != skip_index:
                if particle.side == -1:
                    temp *= particle.specie.distribution(p[i])
                else:
                    temp *= 1. - particle.specie.eta * particle.specie.distribution(p[i])

        return temp

    def F_B(self, p, skip_index=None):
        """
        Backward reaction distribution functional term

        \begin{equation}
            \mathcal{F}_B = f_3 f_4 (1 \pm f_1) (1 \pm f_2)
        \end{equation}

        :param skip_index: Particle to skip in the expression
        """
        temp = 1.

        for i, particle in enumerate(self.reaction):
            if skip_index is None or i != skip_index:
                if particle.side == 1:
                    temp *= particle.specie.distribution(p[i])
                else:
                    temp *= 1. - particle.specie.eta * particle.specie.distribution(p[i])

        return temp

    """
    ### Linearized in $\, f_1$ form

    \begin{equation}
        \mathcal{F}(f) = f_3 f_4 (1 \pm f_1) (1 \pm f_2) - f_1 f_2 (1 \pm f_3) (1 \pm f_4)
    \end{equation}

    \begin{equation}
        \mathcal{F}(f) = f_1 (\mp f_3 f_4 (1 \pm f_2) - f_2 (1 \pm f_3) (1 \pm f_4)) \
        + f_3 f_4 (1 \pm f_2)
    \end{equation}

    \begin{equation}
        \mathcal{F}(f) = \mathcal{F}_B^{(1)} + f_1 (\mathcal{F}_A^{(1)} \pm_1 \mathcal{F}_B^{(1)})
    \end{equation}

    $^{(i)}$ in $\mathcal{F}^{(i)}$ means that the distribution function $f_i$ was omitted in the\
    corresponding expression. $\pm_j$ represents the $\eta$ value of the particle $j$.
    """
    def F_f(self, p):
        """ Variable part of the distribution functional """
        return (
            self.F_A(p=p, skip_index=0) - self.particle.eta * self.F_B(p=p, skip_index=0)
        )

    def F_1(self, p):
        """ Constant part of the distribution functional """
        return self.F_B(p=p, skip_index=0)


class BoltzmannIntegral(PicklableObject, DistributionFunctional):

    """ ## Integral
        Representation of the concrete collision integral for a specific particle \
        `Integral.reaction[0]` """

    _saveable_fields = [
        'particle', 'reaction', 'decoupling_temperature', 'constant', 'Ms', 'grids',
    ]

    reaction = None  # All particles involved

    """ ### Crossed particles in the integral

        If the Boltzmann integral is obtained as a crossing of some other process, the mass of the\
        crossed fermion in the matrix element has to change sign.

        For example, compare the matrix elements of reactions

        \begin{align}
            \nu + e &\to \nu + e \\\\
            \nu + \overline{\nu} &\to e + e^+
        \end{align}

        In particular, this has something to do with the `K2` term in the `FourParticleIntegral`.
    """

    # Temperature when the typical interaction time exceeds the Hubble expansion time
    decoupling_temperature = 0.
    constant = 0.

    """ Four-particle interactions of the interest can all be rewritten in a form

        \begin{equation}
            |\mathcal{M}|^2 = \sum_{\{i \neq j \neq k \neq l\}} K_1 (p_i \cdot p_j) (p_k \cdot p_l)\
                 + K_2 m_i m_j (p_k \cdot p_l)
        \end{equation} """

    Ms = None

    """ Grids corresponding to particles integrated over """
    grids = None

    def __init__(self, **kwargs):
        """ Update self with configuration `kwargs`, construct particles list and \
            energy conservation law of the integral. """

        for key in kwargs:
            setattr(self, key, kwargs[key])

        if not self.Ms:
            self.Ms = []

        self.integrand = numpy.vectorize(self.integrand, otypes=[numpy.float_])

    def __str__(self):
        """ String-like representation of the integral. Corresponds to the first particle """
        return (
            " + ".join([p.specie.symbol + ('\'' if p.antiparticle else '')
                        for p in self.reaction if p.side == -1])
            + " ⟶  "
            + " + ".join([p.specie.symbol + ('\'' if p.antiparticle else '')
                          for p in self.reaction if p.side == 1])
            + "\t({})".format(', '.join([str(M) for M in self.Ms]))
        )

    def __repr__(self):
        return self.__str__()

    def initialize(self):
        """
        Initialize collision integral constants and save them to the first involved particle
        """
        raise NotImplementedError()

    def calculate_kinematics(self, p):
        """ Helper procedure that caches conformal energies and masses of the reaction """
        particle_count = len(self.reaction)
        p = (p + [0.]*particle_count)[:particle_count]
        E = []
        m = []
        for i, particle in enumerate(self.reaction):
            E.append(particle.specie.conformal_energy(p[i]))
            m.append(particle.specie.conformal_mass)

        """ Parameters of one particle can be inferred from the energy conservation law
            \begin{equation}E_3 = -s_3 \sum_{i \neq 3} s_i E_i \end{equation} """
        E[particle_count-1] = self.reaction[particle_count-1].side \
            * sum([-self.reaction[i].side * E[i] for i in range(particle_count-1)])
        p[particle_count-1] = numpy.sqrt(numpy.abs(E[particle_count-1]**2 - m[particle_count-1]**2))
        return p, E, m

    def rates(self):
        def forward_integral(p):
            return numpy.vectorize(lambda p0: p0**2 / (2 * numpy.pi)**3
                                   * self.integrate(p0, self.F_A)[0])(p)

        def backward_integral(p):
            return numpy.vectorize(lambda p0: p0**2 / (2 * numpy.pi)**3
                                   * self.integrate(p0, self.F_B)[0])(p)

        grid = self.particle.grid

        forward_rate, _ = integrators.integrate_1D(forward_integral,
                                                   (grid.MIN_MOMENTUM, grid.MAX_MOMENTUM))

        backward_rate, _ = integrators.integrate_1D(backward_integral,
                                                    (grid.MIN_MOMENTUM, grid.MAX_MOMENTUM))

        return -forward_rate, backward_rate

    def rate(self):
        forward_rate, backward_rate = self.rates()
        return backward_rate - forward_rate

    @staticmethod
    def integrate(p0, integrand, bounds=None, kwargs=None):
        raise NotImplementedError()

    def integrand(self, *args, **kwargs):
        """ Collision integral interior. """
        raise NotImplementedError()

    """ ### Integration region bounds methods """

    def in_bounds(self, p, E=None, m=None):
        raise NotImplementedError()

    def bounds(self, p0):
        """ Coarse integration region based on the `self.particle.grid` points.
            Assumes that integration region is connected. """
        points = []
        for p1 in self.particle.grid.TEMPLATE:
            points.append((p1, self.lower_bound(p0, p1),))
            points.append((p1, self.upper_bound(p0, p1),))

        return points

    def lower_bound(self, p0, p1):
        """ Find the first `self.particle.grid` point in the integration region """

        index = 0
        while (index < self.particle.grid.MOMENTUM_SAMPLES
               and not self.in_bounds([p0, p1, self.particle.grid.TEMPLATE[index]])):
            index += 1

        if index == self.particle.grid.MOMENTUM_SAMPLES:
            return self.particle.grid.MIN_MOMENTUM

        return self.particle.grid.TEMPLATE[index]

    def upper_bound(self, p0, p1):
        """ Find the last `self.particle.grid` point in the integration region """

        index = int(
            (min(p0 + p1, self.particle.grid.MAX_MOMENTUM) - self.particle.grid.MIN_MOMENTUM)
            / self.particle.grid.MOMENTUM_STEP
        )

        while index >= 0 and not self.in_bounds([p0, p1, self.particle.grid.TEMPLATE[index]]):
            index -= 1

        if index == -1:
            return self.particle.grid.MIN_MOMENTUM

        return self.particle.grid.TEMPLATE[index]
