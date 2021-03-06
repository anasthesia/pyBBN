# -*- coding: utf-8 -*-
import math
import numpy
import operator
from common import integrators
from interactions.boltzmann import BoltzmannIntegral


class ThreeParticleM(object):

    """ ## Three-particle interaction matrix element
        Matrix elements of the interest for three-particle interactions are constant """

    K = 0.

    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def __str__(self):
        return "K={: .2e}".format(self.K)

    def __iadd__(self, M):
        self.K += M.K
        return self

    def __idiv__(self, div):
        self.K /= div
        return self

    def __imul__(self, mul):
        self.K *= mul
        return self


class ThreeParticleIntegral(BoltzmannIntegral):

    def __init__(self, **kwargs):
        super(ThreeParticleIntegral, self).__init__(**kwargs)

        if self.grids is None:
            self.grids = tuple([self.reaction[1].specie.grid])

    def initialize(self):
        """
        Initialize collision integral constants and save them to the first involved particle
        """
        params = self.particle.params
        if params.T > self.decoupling_temperature and not self.particle.in_equilibrium:
            self.constant = sum(M.K for M in self.Ms)
            self.particle.collision_integrals.append(self)

    def integrate(self, p0, fau=None, bounds=None):
        if p0 == 0:
            return self.rest_integral(fau)

        if bounds is None:
            bounds = (self.grids[0].MIN_MOMENTUM, self.grids[0].MAX_MOMENTUM)

        def prepared_integrand(p1):
            return self.integrand(p0, p1, fau)

        integral, error = integrators.integrate_1D(
            prepared_integrand,
            bounds=bounds
        )
        constant = self.particle.params.a / 16. / math.pi

        return constant * integral

    def rest_integral(self, fau=None):
        a = self.particle.params.a
        m = [particle.specie.mass for particle in self.reaction]

        if m[0] == 0:
            return 0

        signs = ((1, 1, 1), (1, -1, -1),
                 (1, -1, 1), (1, 1, -1))

        p1 = a * math.sqrt(reduce(operator.mul, (
            reduce(operator.add, map(operator.mul, m, sign))
            for sign in signs
        ))) / (2. * m[0])

        p = [0, p1, 0]
        p, E, m = self.calculate_kinematics(p)

        return (
            a * self.constant / (8 * math.pi * self.particle.conformal_mass)
            * p1**2 / E[1] / E[2] * fau(p)
        )

    def integrand(self, p0, p1, fau=None):

        """
        Collision integral interior.
        """

        p = [p0, p1, 0]
        p, E, m = self.calculate_kinematics(p)

        integrand = self.in_bounds(p, E, m) * self.constant

        if p[0] != 0:
            integrand /= p[0] * E[0]

            # Avoid rounding errors and division by zero
            if m[1] != 0:
                integrand *= p[1] / E[1]
        else:
            if m[0] == 0:
                integrand *= 0
                return integrand

            integrand *= 2 * p[1]**2
            if m[1] != 0:
                integrand *= p[1] / E[1]
            if m[2] != 0:
                integrand *= p[1] / E[2]

        integrand *= numpy.array([fau([p[0], p[1][i], p[2][i]]) for i in range(len(p[1]))])

        return integrand

    """ ### Integration region bounds methods """

    def in_bounds(self, p, E=None, m=None):
        """ The kinematically allowed region in momentum space """
        if not E or not m:
            p, E, m = self.calculate_kinematics(p)

        is_in = (
            (E[2] >= m[2])
            * (p[0] + p[1] > p[2])
            * (p[0] + p[2] > p[1])
            * (p[1] + p[2] > p[0])
        )

        return is_in
