# -*- coding: utf-8 -*-
from HARK.datasets.life_tables.us_ssa.SSATools import parse_ssa_life_table
from HARK.datasets.SCF.WealthIncomeDist.SCFDistTools \
    import income_wealth_dists_from_scf
from HARK.Calibration.Income.IncomeTools \
    import (parse_income_spec, parse_time_params, Cagetti_income)
from HARK.utilities import make_grid_exp_mult
# TODO: CDC 20210524: Below is clunky.  Presumably done with an eye toward
# writing general code that would work for any utility function; but that is
# not actually done in the actual code as written.
from HARK.utilities import CRRAutility
from HARK.utilities import CRRAutilityP
from HARK.utilities import CRRAutilityPP
from HARK.utilities import CRRAutilityP_inv
from HARK.utilities import CRRAutility_invP
from HARK.utilities import CRRAutilityP_invP
from HARK.utilities import CRRAutility_inv
from HARK.interpolation import (LinearInterp,
                                ValueFuncCRRA, MargValueFuncCRRA,
                                MargMargValueFuncCRRA)
import numpy as np
from copy import copy, deepcopy
# import dolo.misc.dprint as dprint
from types import SimpleNamespace
from ast import parse as parse  # Allow storing python stmts as objects


class TransitionFunctions(SimpleNamespace):
    """
    Transitions between stges of the solution process
    """
# TODO: Move (to core.py) when vetted/agreed
    pass


class ValueFunctions(SimpleNamespace):
    """
    Equations that define value functions
    """
# TODO: Move (to core.py) when vetted/agreed
    pass


class Information(SimpleNamespace):
    """
    Parameters, functions, etc needed for model equations
    """
    pass


def def_transitions(stge):
    stge = def_transition_BOP__to__choice(stge)  # Setup state for choice
    stge = def_transition_choice__to__chosen(stge)  # Consequences of choice
    stge = def_transition_chosen__to__EOP(stge)  # EOP=End of Period
    stge = def_transition_chosen__to__next_choice(stge)
    stge = def_transition_chosen__to__next_BOP(stge)  # BOP = Beginning of Period
    return stge


transitions_caused_by_shocks = {
    'RNrm': 'RNrm = Rfree / (PermGroFac * permShk)',
    'bNrm': 'bNrm = aNrm * RNrm',
    'yNrm': 'yNrm = tranShk',
    'mNrm': 'mNrm = bNrm + yNrm'
}

#    After the choices have been made, it is possible that
#    other shocks could be realized or other evolutions could
#    occur.

# This is here as a placeholder


def def_transition_BOP__to__choice(stge):
    """
    Transition from beginning of period to choice stage
    """

    # Dummy example variable
    eqns_source = {'BOP__to__choice': 'BOP__to__choice = "Done"'}

    BOP__to__choice = TransitionFunctions()
    BOP__to__choice.eqns = {}
    BOP__to__choice.vals = {}

    for eqn_name in eqns_source.keys():
        tree = parse(eqns_source[eqn_name], mode='exec')
        code = compile(tree, filename="<ast>", mode='exec')
        BOP__to__choice.eqns.update({eqn_name: code})

    BOP__to__choice.eqns_source = eqns_source
    stge.Modl.Transitions['BOP__to__choice'] = BOP__to__choice

    return stge


def def_transition_choice__to__chosen(stge):
    """
    Transition from state(s) before the choice to state(s) after.
    """

    eqns_source = {
        'aNrm': 'aNrm = mNrm - cNrm',
        'after_choice_states': 'after_choice_states = [aNrm]'
    }

    choice__to__chosen = TransitionFunctions()
    choice__to__chosen.eqns = {}
    choice__to__chosen.vals = {}

    for eqn_name in eqns_source.keys():
        tree = parse(eqns_source[eqn_name], mode='exec')
        code = compile(tree, filename="<ast>", mode='exec')
        choice__to__chosen.eqns.update({eqn_name: code})

    choice__to__chosen.eqns_source = eqns_source
    stge.Modl.Transitions['choice__to__chosen'] = choice__to__chosen

    return stge


def def_transition_chosen__to__EOP(stge):
    """
    After consumption has been chosen, realize the shocks
    (permShk, tranShk) required for the transition to the
    next period.
    """

    eqns_source = deepcopy(transitions_caused_by_shocks)
    eqns_source.update({'shocked_states': 'shocked_states = [mNrm]'})

    chosen__to__EOP = TransitionFunctions()
    chosen__to__EOP.eqns = {}
    chosen__to__EOP.vals = {}

    for eqn_name in eqns_source.keys():
        tree = parse(eqns_source[eqn_name], mode='exec')
        code = compile(tree, filename="<ast>", mode='exec')
        chosen__to__EOP.eqns.update({eqn_name: code})

    chosen__to__EOP.eqns_source = eqns_source
    stge.Modl.Transitions['chosen__to__EOP'] = chosen__to__EOP

    return stge


def def_transition_chosen__to__next_BOP(stge):
    """
    After consumption has been chosen, realize the shocks
    (permShk, tranShk) required for the transition to the
    beginning of the next period.
    """

    eqns_source = deepcopy(transitions_caused_by_shocks)
    eqns_source.update({'next_states': 'next_states = [mNrm]'})

    chosen__to__next_BOP = TransitionFunctions()
    chosen__to__next_BOP.eqns = {}
    chosen__to__next_BOP.vals = {}

    for eqn_name in eqns_source.keys():
        tree = parse(eqns_source[eqn_name], mode='exec')
        code = compile(tree, filename="<ast>", mode='exec')
        chosen__to__next_BOP.eqns.update({eqn_name: code})

    chosen__to__next_BOP.eqns_source = eqns_source
    stge.Modl.Transitions['chosen__to__next_BOP'] = chosen__to__next_BOP
    return stge


def make_transition_equations(stge, transition_name, equations):
    """
    Make transition equations from this stage to next.

    Parameters
    ----------
    stge : agent_solution
        A solution object
    transition_name : str
        The name of the transition
    equations : dict
        Equations in python code with names in keys
    """
    stge.Modl.Transitions[transition_name] = TransitionFunctions()
    setattr(stge.Modl.Transitions[transition_name], 'eqns_source', equations)
    setattr(stge.Modl.Transitions[transition_name], 'eqns', {})
    setattr(stge.Modl.Transitions[transition_name], 'vals', {})

    # Store the parsed executable code
    for eqn_name in equations.keys():
        tree = parse(equations[eqn_name], mode='exec')
        code = compile(tree, filename="<ast>", mode='exec')
        stge.Modl.Transitions[transition_name].eqns.update({eqn_name: code})


def def_transition_chosen__to__next_choice(stge):
    """
    Define transition from post-choice now to ready-to-choose.

    Equations must be evaluated in a namespace containing
    compatibly shaped variables aNrm, permShk, and tranShk.
    """
    eqns_source = deepcopy(transitions_caused_by_shocks)
    eqns_source.update({'next_states': 'next_states = [mNrm]'})

    chosen__to__next_choice = TransitionFunctions()
    chosen__to__next_choice.eqns = {}
    chosen__to__next_choice.vals = {}

    for eqn_name in eqns_source.keys():
        tree = parse(eqns_source[eqn_name], mode='exec')
        code = compile(tree, filename="<ast>", mode='exec')
        chosen__to__next_choice.eqns.update({eqn_name: code})

    chosen__to__next_choice.eqns_source = eqns_source
    stge.Modl.Transitions['chosen__to__next_choice'] = chosen__to__next_choice
    return stge


# End of this to beginning of next period


def def_transition_EOP_to_next_BOP(stge):
    """
    Transition from beginning of period to decision stage
    """

    # Dummy example variable
    eqns_source = {'EOP__to__next_BOP': 'EOP__to__next_BOP = "Done"'}

    EOP__to__next_BOP = TransitionFunctions()
    EOP__to__next_BOP.eqns = {}
    EOP__to__next_BOP.vals = {}

    for eqn_name in eqns_source.keys():
        tree = parse(eqns_source[eqn_name], mode='exec')
        code = compile(tree, filename="<ast>", mode='exec')
        EOP__to__next_BOP.eqns.update({eqn_name: code})

    EOP__to__next_BOP.eqns_source = eqns_source
    stge.Modl.Transitions['EOP__to__next_BOP'] = EOP__to__next_BOP

    return stge


def def_transition_EOP_to_next_choice(stge):
    """
    Transition from end of period to next choice stage
    """

    eqns_source = transitions_caused_by_shocks

    EOP__to__next_choice = TransitionFunctions()
    EOP__to__next_choice.eqns = {}
    EOP__to__next_choice.vals = {}

    for eqn_name in eqns_source.keys():
        tree = parse(eqns_source[eqn_name], mode='exec')
        code = compile(tree, filename="<ast>", mode='exec')
        EOP__to__next_choice.eqns.update({eqn_name: code})

    EOP__to__next_choice.eqns_source = eqns_source
    stge.Modl.Transitions['EOP__to__next_choice'] = EOP__to__next_choice

    return stge


def def_felicity(stge):
    stge = def_utility_CRRA(stge, stge.Pars.CRRA)
    return stge


def def_utility_CRRA(stge, CRRA):
    """
    Defines CRRA utility function for this period (and its derivatives,
    and their inverses), saving them as attributes of self for other methods
    to use.

    Parameters
    ----------
    stge : ConsumerSolutionOneStateCRRA

    Returns
    -------
    none
    """
    Bilt, Pars, Modl = stge.Bilt, stge.Pars, stge.Modl
    Info = Modl.Info = {**Bilt.__dict__, **Pars.__dict__}

    Modl.Rewards = SimpleNamespace()
    Modl.Rewards.eqns = {}
    Modl.Rewards.vals = {}

    # Add required funcs to Modl.Info
    for func in {'CRRAutility', 'CRRAutilityP', 'CRRAutilityPP',
                 'CRRAutility_inv', 'CRRAutility_invP', 'CRRAutilityP_inv',
                 'CRRAutilityP_invP'}:
        Info[func] = globals()[func]

    # Hard-wire the passed CRRA into the utility function and its progeny
    eqns_source = {
        'u_D0':
            'u = lambda c: CRRAutility(c,'+str(CRRA)+')',
        'u_D1':
            'u.dc = lambda c: CRRAutilityP(c, '+str(CRRA)+')',
        'u_D2':
            'u.dc.dc = lambda c: CRRAutilityPP(c, '+str(CRRA)+')',
        'uNvrs_D0':
            'u.Nvrs = lambda u: CRRAutility_inv(u, '+str(CRRA)+')',
        'uNvrs_D1':
            'u.Nvrs.du = lambda u: CRRAutility_invP(u, '+str(CRRA)+')',
        'u_D1_Nvrs':
            'u.dc.Nvrs = lambda uP: CRRAutilityP_inv(uP, '+str(CRRA)+')',
        'u_D1_Nvrs_D1':
            'u.dc.Nvrs.du = lambda uP: CRRAutilityP_invP(uP, '+str(CRRA)+')',
    }

    for eqn_name in eqns_source.keys():
        tree = parse(eqns_source[eqn_name], mode='exec')
        code = compile(tree, filename="<ast>", mode='exec')
        Modl.Rewards.eqns.update({eqn_name: code})
        exec(code, {**globals(), **Info}, Modl.Rewards.vals)

        Modl.Rewards.eqns_source = eqns_source

#     # Can't use partial() here because it does not allow positional arguments
#     # Google: how-to-fill-specific-positional-arguments-with-partial-in-python

#     Bilt.uFunc = lambda c: CRRAutility(c, CRRA)
#     Modl.reward.update({'uFunc': 'lambda c: CRRAutility(c, CRRA)'})
#     # marginal utility
#     # CDC 20210613: New syntax makes derivatives attributes of function
# #    Bilt.uFunc.dc = Bilt.uP = lambda c: CRRAutilityP(c, CRRA)  # dc is der wrt c
#     Bilt.uFunc.dc = lambda c: CRRAutilityP(c, CRRA)  # dc is der wrt c
#     Modl.reward.update({'uFunc.dc': 'lambda c: CRRAutilityP(c, CRRA)'})

#     # marginal marginal utility
# #    Bilt.uFuncPP = lambda c: CRRAutilityPP(c, CRRA)  # another der
#     Bilt.uFunc.dc.dc = lambda c: CRRAutilityPP(c, CRRA)  # another der
#     Modl.reward.update({'uFunc.dc.dc': 'lambda c: CRRAutilityPP(c, CRRA)'})

#     # Inverses thereof
# #    Bilt.uFunc.dc.Nvrs = Bilt.uPinv = lambda uP: CRRAutilityP_inv(uP, CRRA)
#     Bilt.uFunc.Nvrs = lambda u: CRRAutility_inv(u, CRRA)
#     Modl.reward.update({'uFunc.Nvrs': 'lambda u: CRRAutility_inv(u, CRRA)'})
#     Bilt.uFunc.dc.Nvrs = lambda uP: CRRAutilityP_inv(uP, CRRA)
#     Modl.reward.update({'uFunc.dc.Nvrs': 'lambda uP: CRRAutilityP_inv(uP, CRRA)'})
# #    Bilt.uFunc.dc.Nvrs.du = Bilt.uPinvP = lambda uP: CRRAutilityP_invP(uP, CRRA)
#     Bilt.uFunc.dc.Nvrs.du = lambda uP: CRRAutilityP_invP(uP, CRRA)
#     Modl.reward.update({'uFunc.dc.Nvrs.du': 'lambda uP: CRRAutilityP_invP(uP, CRRA)'})
# #    Bilt.uFuncinvP = lambda u: CRRAutility_invP(u, CRRA)
#     Bilt.uFunc.Nvrs.du = lambda u: CRRAutility_invP(u, CRRA)
#     Modl.reward.update({'uFunc.Nvrs.du': 'lambda u: CRRAutility_invP(u, CRRA)'})
# #    Bilt.uinvP = lambda u: CRRAutility_invP(u, CRRA)
# #    Bilt.uinv = lambda u: CRRAutility_inv(u, CRRA)

    Bilt.__dict__.update({k: v for k, v in Modl.Rewards.vals.items()})

    return stge


def def_value_funcs(stge, CRRA):
    """
    Defines the value and function and its derivatives for this period.
    See PerfForesightConsumerType.ipynb for a brief explanation
    and the links below for a fuller treatment.

    https://github.com/llorracc/SolvingMicroDSOPs/#vFuncPF

    Parameters
    ----------
    stge

    Returns
    -------
    None

    Notes
    -------
    Uses the fact that for an unconstrained perfect foresight CRRA,
    if the MPC in period t is :math:`\\kappa_{t}`, and relative risk
    aversion :math:`\\rho`, then the inverse value vFuncNvrs has a
    constant slope of :math:`\\kappa_{t}^{-\\rho/(1-\\rho)}` and
    vFuncNvrs has value of zero at the lower bound of market resources
    """

    Bilt, Pars, Modl = stge.Bilt, stge.Pars, stge.Modl

    # Info needed to create the model objects
    Info = Modl.Info = {**Bilt.__dict__, **Pars.__dict__}
    Info['about'] = {'Info available when model creation equations are executed'}

    Modl.Value = ValueFunctions()
    Modl.Value.eqns = {}  # Equations
    Modl.Value.vals = {}  # Compiled and executed result at time of exec

    eqns_source = {}  # For storing the equations
    # Pattern below: Equations needed to define value function and derivativfes
    # Each eqn is preceded by adding to the scope whatever is needed
    # to make sure the variables in the equation

#    CRRA, MPCmin = Pars.CRRA, Bilt.MPCmin
    eqns_source.update(
        {'vFuncNvrsSlopeLim':
         'vFuncNvrsSlopeLim = MPCmin ** (-CRRA / (1.0 - CRRA))'})

    # vFuncNvrs function
#    mNrmMin = Bilt.mNrmMin
    Info['LinearInterp'] = LinearInterp  # store so it can be retrieved later

    eqns_source.update(
        {'vFuncNvrs':
         'vFuncNvrs = LinearInterp(' +
            'np.array([mNrmMin, mNrmMin + 1.0]),' +
            'np.array([0.0, vFuncNvrsSlopeLim]))'})

    # vFunc and its derivatives
    Info['ValueFuncCRRA'] = ValueFuncCRRA
    Info['MargValueFuncCRRA'] = MargValueFuncCRRA
    Info['MargMargValueFuncCRRA'] = MargMargValueFuncCRRA

    # Derivative 0 (undifferentiated)
    eqns_source.update(
        {'vFunc_D0':
         'vFunc = ValueFuncCRRA(vFuncNvrs, CRRA)'})

#    cFunc = Bilt.cFunc

    # Derivative 1
    eqns_source.update(
        {'vFunc_D1':
         'vFunc.dm = MargValueFuncCRRA(cFunc, CRRA)'})

    # Derivative 2
    eqns_source.update(
        {'vFunc_D2':
         'vFunc.dm.dm = MargMargValueFuncCRRA(cFunc, CRRA)'})

    # Store the equations in Modl.Value.eqns so they can be retrieved later
    # then execute them now
    for eqn_name in eqns_source.keys():
        #        print(eqn_name+': '+eqns_source[eqn_name])
        tree = parse(eqns_source[eqn_name], mode='exec')
        code = compile(tree, filename="<ast>", mode='exec')
        Modl.Value.eqns.update({eqn_name: code})
        exec(code, {**globals(), **Modl.Info}, Modl.Value.vals)

    # Add newly created stuff to Bilt namespace
    Bilt.__dict__.update({k: v for k, v in Modl.Value.vals.items()})

    stge.vFunc = Bilt.vFunc  # vFunc needs to be on root as well as Bilt

    Modl.Value.eqns_source = eqns_source  # Save uncompiled source code

    return stge


def_value_CRRA = def_value_funcs


def apply_flat_income_tax(
        IncShkDstn, tax_rate, T_retire, unemployed_indices=None, transitory_index=2
):
    """
    Applies a flat income tax rate to all employed income states during the working
    period of life (those before T_retire).  Time runs forward in this function.

    Parameters
    ----------
    IncShkDstn : [distribution.Distribution]
        The discrete approximation to the income distribution in each time period.
    tax_rate : float
        A flat income tax rate to be applied to all employed income.
    T_retire : int
        The time index after which the agent retires.
    unemployed_indices : [int]
        Indices of transitory shocks that represent unemployment states (no tax).
    transitory_index : int
        The index of each element of IncShkDstn representing transitory shocks.

    Returns
    -------
    IncShkDstn_new : [distribution.Distribution]
        The updated income distributions, after applying the tax.
    """
    unemployed_indices = (
        unemployed_indices if unemployed_indices is not None else list()
    )
    IncShkDstn_new = deepcopy(IncShkDstn)
    i = transitory_index
    for t in range(len(IncShkDstn)):
        if t < T_retire:
            for j in range((IncShkDstn[t][i]).size):
                if j not in unemployed_indices:
                    IncShkDstn_new[t][i][j] = IncShkDstn[t][i][j] * (1 - tax_rate)
    return IncShkDstn_new

# =======================================================
# ================ Other useful functions ===============
# =======================================================


def construct_assets_grid(parameters):
    """
    Constructs the base grid of post-decision states, representing end-of-period
    assets above the absolute minimum.

    All parameters are passed as attributes of the single input parameters.  The
    input can be an instance of a ConsumerType, or a custom Parameters class.

    Parameters
    ----------
    aXtraMin:                  float
        Minimum value for the a-grid
    aXtraMax:                  float
        Maximum value for the a-grid
    aXtraCount:                 int
        Size of the a-grid
    aXtraExtra:                [float]
        Extra values for the a-grid.
    exp_nest:               int
        Level of nesting for the exponentially spaced grid

    Returns
    -------
    aXtraGrid:     np.ndarray
        Base array of values for the post-decision-state grid.
    """
    # Unpack the parameters
    aXtraMin = parameters.aXtraMin
    aXtraMax = parameters.aXtraMax
    aXtraCount = parameters.aXtraCount
    aXtraExtra = parameters.aXtraExtra
    grid_type = "exp_mult"
    exp_nest = parameters.aXtraNestFac

    # Set up post decision state grid:
    aXtraGrid = None
    if grid_type == "linear":
        aXtraGrid = np.linspace(aXtraMin, aXtraMax, aXtraCount)
    elif grid_type == "exp_mult":
        aXtraGrid = make_grid_exp_mult(
            ming=aXtraMin, maxg=aXtraMax, ng=aXtraCount, timestonest=exp_nest
        )
    else:
        raise Exception(
            "grid_type not recognized in __init__."
            + "Please ensure grid_type is 'linear' or 'exp_mult'"
        )
    # Add in additional points for the grid:
    for a in aXtraExtra:
        if a is not None:
            if a not in aXtraGrid:
                j = aXtraGrid.searchsorted(a)
                aXtraGrid = np.insert(aXtraGrid, j, a)
    return aXtraGrid


# Make a dictionary to specify a perfect foresight consumer type
init_perfect_foresight = {
    'CRRA': 2.0,          # Coefficient of relative risk aversion,
    'Rfree': 1.03,        # Interest factor on assets
    'DiscFac': 0.96,      # Intertemporal discount factor
    'LivPrb': [0.98],     # Survival probability
    'PermGroFac': [1.01],  # Permanent income growth factor
    'BoroCnstArt': None,  # Artificial borrowing constraint
    'T_cycle': 1,         # Num of periods in a finite horizon cycle (like, a life cycle)
    'PermGroFacAgg': 1.0,  # Aggregate income growth factor (multiplies individual)
    'MaxKinks': None,      # Maximum number of grid points to allow in cFunc
    'AgentCount': 10000,  # Number of agents of this type (only matters for simulation)
    'aNrmInitMean': 0.0,  # Mean of log initial assets (only matters for simulation)
    'aNrmInitStd': 1.0,  # Standard deviation of log initial assets (only for simulation)
    'pLvlInitMean': 0.0,  # Mean of log initial permanent income (only matters for simulation)
    # Standard deviation of log initial permanent income (only matters for simulation)
    'pLvlInitStd': 0.0,
    # Aggregate permanent income growth factor: portion of PermGroFac attributable to aggregate productivity growth (only matters for simulation)
    'T_age': None,       # Age after which simulated agents are automatically killed
    # Optional extra _fcts about the model and its calibration
}

# The info below is optional at present but may become mandatory as the toolkit evolves
# 'Primitives' define the 'true' model that we think of ourselves as trying to solve
# (the limit as approximation error reaches zero)
init_perfect_foresight.update(
    {'prmtv_par': ['CRRA', 'Rfree', 'DiscFac', 'LivPrb', 'PermGroFac', 'BoroCnstArt', 'PermGroFacAgg', 'T_cycle', 'cycles']})
# Approximation parameters define the precision of the approximation
# Limiting values for approximation parameters: values such that, as all such parameters approach their limits,
# the approximation gets arbitrarily close to the 'true' model
init_perfect_foresight.update(  # In principle, kinks exist all the way to infinity
    {'aprox_lim': {'MaxKinks': 'infinity'}})
# The simulation stge of the problem requires additional parameterization
init_perfect_foresight.update(  # The 'primitives' for the simulation
    {'prmtv_sim': ['aNrmInitMean', 'aNrmInitStd', 'pLvlInitMean', 'pLvlInitStd']})
init_perfect_foresight.update({  # Approximation parameters for monte carlo sims
    'sim_mcrlo': ['AgentCount', 'T_age']
})
init_perfect_foresight.update({  # Limiting values that define 'true' simulation
    'sim_mcrlo_lim': {
        'AgentCount': 'infinity',
        'T_age': 'infinity'
    }
})

# Optional more detailed _fcts about various parameters
CRRA_fcts = {
    'about': 'Coefficient of Relative Risk Aversion'}
CRRA_fcts.update({'latexexpr': '\providecommand{\CRRA}{\rho}\CRRA'})
CRRA_fcts.update({'_unicode_': 'ρ'})  # \rho is Greek r: relative risk aversion rrr
CRRA_fcts.update({'prmtv_par': 'True'})
init_perfect_foresight['prmtv_par'].append('CRRA')
# init_perfect_foresight['_fcts'].update({'CRRA': CRRA_fcts})
init_perfect_foresight.update({'CRRA_fcts': CRRA_fcts})

DiscFac_fcts = {
    'about': 'Pure time preference rate'}
DiscFac_fcts.update({'latexexpr': '\providecommand{\DiscFac}{\beta}\DiscFac'})
DiscFac_fcts.update({'_unicode_': 'β'})
DiscFac_fcts.update({'prmtv_par': 'True'})
init_perfect_foresight['prmtv_par'].append('DiscFac')
# init_perfect_foresight['_fcts'].update({'DiscFac': DiscFac_fcts})
init_perfect_foresight.update({'DiscFac_fcts': DiscFac_fcts})

LivPrb_fcts = {
    'about': 'Probability of survival from this period to next'}
LivPrb_fcts.update({'latexexpr': '\providecommand{\LivPrb}{\Pi}\LivPrb'})
LivPrb_fcts.update({'_unicode_': 'Π'})  # \Pi mnemonic: 'Probability of surival'
LivPrb_fcts.update({'prmtv_par': 'True'})
init_perfect_foresight['prmtv_par'].append('LivPrb')
# init_perfect_foresight['_fcts'].update({'LivPrb': LivPrb_fcts})
init_perfect_foresight.update({'LivPrb_fcts': LivPrb_fcts})

Rfree_fcts = {
    'about': 'Risk free interest factor'}
Rfree_fcts.update({'latexexpr': '\providecommand{\Rfree}{\mathsf{R}}\Rfree'})
Rfree_fcts.update({'_unicode_': 'R'})
Rfree_fcts.update({'prmtv_par': 'True'})
init_perfect_foresight['prmtv_par'].append('Rfree')
# init_perfect_foresight['_fcts'].update({'Rfree': Rfree_fcts})
init_perfect_foresight.update({'Rfree_fcts': Rfree_fcts})

PermGroFac_fcts = {
    'about': 'Growth factor for permanent income'}
PermGroFac_fcts.update({'latexexpr': '\providecommand{\PermGroFac}{\Gamma}\PermGroFac'})
PermGroFac_fcts.update({'_unicode_': 'Γ'})  # \Gamma is Greek G for Growth
PermGroFac_fcts.update({'prmtv_par': 'True'})
init_perfect_foresight['prmtv_par'].append('PermGroFac')
# init_perfect_foresight['_fcts'].update({'PermGroFac': PermGroFac_fcts})
init_perfect_foresight.update({'PermGroFac_fcts': PermGroFac_fcts})

PermGroFacAgg_fcts = {
    'about': 'Growth factor for aggregate permanent income'}
# PermGroFacAgg_fcts.update({'latexexpr': '\providecommand{\PermGroFacAgg}{\Gamma}\PermGroFacAgg'})
# PermGroFacAgg_fcts.update({'_unicode_': 'Γ'})  # \Gamma is Greek G for Growth
PermGroFacAgg_fcts.update({'prmtv_par': 'True'})
init_perfect_foresight['prmtv_par'].append('PermGroFacAgg')
# init_perfect_foresight['_fcts'].update({'PermGroFacAgg': PermGroFacAgg_fcts})
init_perfect_foresight.update({'PermGroFacAgg_fcts': PermGroFacAgg_fcts})

BoroCnstArt_fcts = {
    'about': 'If not None, maximum proportion of permanent income borrowable'}
BoroCnstArt_fcts.update({'latexexpr': r'\providecommand{\BoroCnstArt}{\underline{a}}\BoroCnstArt'})
BoroCnstArt_fcts.update({'prmtv_par': 'True'})
init_perfect_foresight['prmtv_par'].append('BoroCnstArt')
# init_perfect_foresight['_fcts'].update({'BoroCnstArt': BoroCnstArt_fcts})
init_perfect_foresight.update({'BoroCnstArt_fcts': BoroCnstArt_fcts})

MaxKinks_fcts = {
    'about': 'PF Constrained model solves to period T-MaxKinks,'
    ' where the solution has exactly this many kink points'}
MaxKinks_fcts.update({'prmtv_par': 'False'})
# init_perfect_foresight['prmtv_par'].append('MaxKinks')
# init_perfect_foresight['_fcts'].update({'MaxKinks': MaxKinks_fcts})
init_perfect_foresight.update({'MaxKinks_fcts': MaxKinks_fcts})

AgentCount_fcts = {
    'about': 'Number of agents to use in baseline Monte Carlo simulation'}
AgentCount_fcts.update(
    {'latexexpr': '\providecommand{\AgentCount}{N}\AgentCount'})
AgentCount_fcts.update({'sim_mcrlo': 'True'})
AgentCount_fcts.update({'sim_mcrlo_lim': 'infinity'})
# init_perfect_foresight['sim_mcrlo'].append('AgentCount')
# init_perfect_foresight['_fcts'].update({'AgentCount': AgentCount_fcts})
init_perfect_foresight.update({'AgentCount_fcts': AgentCount_fcts})

aNrmInitMean_fcts = {
    'about': 'Mean initial population value of aNrm'}
aNrmInitMean_fcts.update({'sim_mcrlo': 'True'})
aNrmInitMean_fcts.update({'sim_mcrlo_lim': 'infinity'})
init_perfect_foresight['sim_mcrlo'].append('aNrmInitMean')
# init_perfect_foresight['_fcts'].update({'aNrmInitMean': aNrmInitMean_fcts})
init_perfect_foresight.update({'aNrmInitMean_fcts': aNrmInitMean_fcts})

aNrmInitStd_fcts = {
    'about': 'Std dev of initial population value of aNrm'}
aNrmInitStd_fcts.update({'sim_mcrlo': 'True'})
init_perfect_foresight['sim_mcrlo'].append('aNrmInitStd')
# init_perfect_foresight['_fcts'].update({'aNrmInitStd': aNrmInitStd_fcts})
init_perfect_foresight.update({'aNrmInitStd_fcts': aNrmInitStd_fcts})

pLvlInitMean_fcts = {
    'about': 'Mean initial population value of log pLvl'}
pLvlInitMean_fcts.update({'sim_mcrlo': 'True'})
init_perfect_foresight['sim_mcrlo'].append('pLvlInitMean')
# init_perfect_foresight['_fcts'].update({'pLvlInitMean': pLvlInitMean_fcts})
init_perfect_foresight.update({'pLvlInitMean_fcts': pLvlInitMean_fcts})

pLvlInitStd_fcts = {
    'about': 'Mean initial std dev of log ppLvl'}
pLvlInitStd_fcts.update({'sim_mcrlo': 'True'})
init_perfect_foresight['sim_mcrlo'].append('pLvlInitStd')
# init_perfect_foresight['_fcts'].update({'pLvlInitStd': pLvlInitStd_fcts})
init_perfect_foresight.update({'pLvlInitStd_fcts': pLvlInitStd_fcts})

T_age_fcts = {
    'about': 'Age after which simulated agents are automatically killedl'}
T_age_fcts.update({'sim_mcrlo': 'False'})
# init_perfect_foresight['_fcts'].update({'T_age': T_age_fcts})
init_perfect_foresight.update({'T_age_fcts': T_age_fcts})

T_cycle_fcts = {
    'about': 'Number of periods in a "cycle" (like, a lifetime) for this agent type'}
# init_perfect_foresight['_fcts'].update({'T_cycle': T_cycle_fcts})
init_perfect_foresight.update({'T_cycle_fcts': T_cycle_fcts})

cycles_fcts = {
    'about': 'Number of times the sequence of periods/stages should be solved'}
# init_perfect_foresight['_fcts'].update({'cycle': cycles_fcts})
init_perfect_foresight.update({'cycles_fcts': cycles_fcts})
cycles_fcts.update({'prmtv_par': 'True'})
init_perfect_foresight['prmtv_par'].append('cycles')


# Make a dictionary to specify a perfect foresight consumer type
init_perfect_foresight = {
    'CRRA': 2.0,          # Coefficient of relative risk aversion,
    'Rfree': 1.03,        # Interest factor on assets
    'DiscFac': 0.96,      # Intertemporal discount factor
    'LivPrb': [0.98],     # Survival probability
    'PermGroFac': [1.01],  # Permanent income growth factor
    'BoroCnstArt': None,  # Artificial borrowing constraint
    'T_cycle': 1,         # Num of periods in a finite horizon cycle (like, a life cycle)
    'PermGroFacAgg': 1.0,  # Aggregate income growth factor (multiplies individual)
    'MaxKinks': None,      # Maximum number of grid points to allow in cFunc
    'AgentCount': 10000,  # Number of agents of this type (only matters for simulation)
    'aNrmInitMean': 0.0,  # Mean of log initial assets (only matters for simulation)
    'aNrmInitStd': 1.0,  # Standard deviation of log initial assets (only for simulation)
    'pLvlInitMean': 0.0,  # Mean of log initial permanent income (only matters for simulation)
    # Standard deviation of log initial permanent income (only matters for simulation)
    'pLvlInitStd': 0.0,
    # Aggregate permanent income growth factor: portion of PermGroFac attributable to aggregate productivity growth (only matters for simulation)
    'T_age': None,       # Age after which simulated agents are automatically killed
    # Optional extra _fcts about the model and its calibration
}

# The info below is optional at present but may become mandatory as the toolkit evolves
# 'Primitives' define the 'true' model that we think of ourselves as trying to solve
# (the limit as approximation error reaches zero)
init_perfect_foresight.update(
    {'prmtv_par': ['CRRA', 'Rfree', 'DiscFac', 'LivPrb', 'PermGroFac', 'BoroCnstArt', 'PermGroFacAgg', 'T_cycle', 'cycles']})
# Approximation parameters define the precision of the approximation
# Limiting values for approximation parameters: values such that, as all such parameters approach their limits,
# the approximation gets arbitrarily close to the 'true' model
init_perfect_foresight.update(  # In principle, kinks exist all the way to infinity
    {'aprox_lim': {'MaxKinks': 'infinity'}})
# The simulation stge of the problem requires additional parameterization
init_perfect_foresight.update(  # The 'primitives' for the simulation
    {'prmtv_sim': ['aNrmInitMean', 'aNrmInitStd', 'pLvlInitMean', 'pLvlInitStd']})
init_perfect_foresight.update({  # Approximation parameters for monte carlo sims
    'sim_mcrlo': ['AgentCount', 'T_age']
})
init_perfect_foresight.update({  # Limiting values that define 'true' simulation
    'sim_mcrlo_lim': {
        'AgentCount': 'infinity',
        'T_age': 'infinity'
    }
})

# Make a dictionary to specify an idiosyncratic income shocks consumer
init_idiosyncratic_shocks = dict(
    init_perfect_foresight,
    **{
        # Income process variables
        "permShkStd": [0.1],  # Standard deviation of log permanent income shocks
        "tranShkStd": [0.1],  # Standard deviation of log transitory income shocks
        "UnempPrb": 0.05,  # Probability of unemployment while working
        "UnempPrbRet": 0.005,  # Probability of "unemployment" while retired
        "IncUnemp": 0.3,  # Unemployment benefits replacement rate
        "IncUnempRet": 0.0,  # "Unemployment" benefits when retired
        "BoroCnstArt": 0.0,  # Artificial borrowing constraint; imposed minimum level of end-of period assets
        "tax_rate": 0.0,  # Flat income tax rate
        "T_retire": 0,  # Period of retirement (0 --> no retirement)
        # Parameters governing construction of income process
        "permShkCount": 7,  # Number of points in discrete approximation to permanent income shocks
        "tranShkCount": 7,  # Number of points in discrete approximation to transitory income shocks
        # parameters governing construction of grid of assets above min value
        "aXtraMin": 0.001,  # Minimum end-of-period "assets above minimum" value
        "aXtraMax": 20,     # Maximum end-of-period "assets above minimum" value
        "aXtraNestFac": 3,  # Exponential nesting factor when constructing "assets above minimum" grid
        "aXtraCount": 48,   # Number of points in the grid of "assets above minimum"
        # list other values of "assets above minimum" to add to the grid (e.g., 10000)
        "aXtraExtra": [None],
        "vFuncBool": False,  # Whether to calculate the value function during solution
        "CubicBool": False,  # Use cubic spline interpolation when True, linear interpolation when False
    }
)

# The info above is necessary and sufficient for defining the consumer
# The info below is supplemental
# Some of it is required for further purposes

# Parameters required for a (future) matrix-based discretization of the problem
init_idiosyncratic_shocks.update({
    'matrx_par': {
        'mcrlo_aXtraCount': '100',
        'mcrlo_aXtraMin': init_idiosyncratic_shocks['aXtraMin'],
        'mcrlo_aXtraMax': init_idiosyncratic_shocks['aXtraMax']
    }})
init_idiosyncratic_shocks.update({
    'matrx_lim': {
        'mcrlo_aXtraCount': float('inf'),
        'mcrlo_aXtraMin': float('inf'),
        'mcrlo_aXtraMax': float('inf')
    }})

#  add parameters that were not part of perfect foresight model
# Primitives
init_idiosyncratic_shocks['prmtv_par'].append('permShkStd')
init_idiosyncratic_shocks['prmtv_par'].append('tranShkStd')
init_idiosyncratic_shocks['prmtv_par'].append('UnempPrb')
init_idiosyncratic_shocks['prmtv_par'].append('UnempPrbRet')
init_idiosyncratic_shocks['prmtv_par'].append('IncUnempRet')
init_idiosyncratic_shocks['prmtv_par'].append('BoroCnstArt')
init_idiosyncratic_shocks['prmtv_par'].append('tax_rate')
init_idiosyncratic_shocks['prmtv_par'].append('T_retire')

# Approximation parameters and their limits (if any)
# init_idiosyncratic_shocks['aprox_par'].append('permShkCount')
init_idiosyncratic_shocks['aprox_lim'].update({'permShkCount': 'infinity'})
# init_idiosyncratic_shocks['aprox_par'].append('tranShkCount')
init_idiosyncratic_shocks['aprox_lim'].update({'tranShkCount': 'infinity'})
# init_idiosyncratic_shocks['aprox_par'].append('aXtraMin')
init_idiosyncratic_shocks['aprox_lim'].update({'aXtraMin': float('0.0')})
# init_idiosyncratic_shocks['aprox_par'].append('aXtraMax')
init_idiosyncratic_shocks['aprox_lim'].update({'aXtraMax': float('inf')})
# init_idiosyncratic_shocks['aprox_par'].append('aXtraNestFac')
init_idiosyncratic_shocks['aprox_lim'].update({'aXtraNestFac': None})
# init_idiosyncratic_shocks['aprox_par'].append('aXtraCount')
init_idiosyncratic_shocks['aprox_lim'].update({'aXtraCount': None})

IncShkDstn_fcts = {
    'about': 'Income Shock Distribution: .X[0] and .X[1] retrieve shocks, .pmf retrieves probabilities'}
IncShkDstn_fcts.update({'py___code': r'construct_lognormal_income_process_unemployment'})
# init_idiosyncratic_shocks['_fcts'].update({'IncShkDstn': IncShkDstn_fcts})
init_idiosyncratic_shocks.update({'IncShkDstn_fcts': IncShkDstn_fcts})

permShkStd_fcts = {
    'about': 'Standard deviation for lognormal shock to permanent income'}
permShkStd_fcts.update({'latexexpr': '\permShkStd'})
# init_idiosyncratic_shocks['_fcts'].update({'permShkStd': permShkStd_fcts})
init_idiosyncratic_shocks.update({'permShkStd_fcts': permShkStd_fcts})

tranShkStd_fcts = {
    'about': 'Standard deviation for lognormal shock to permanent income'}
tranShkStd_fcts.update({'latexexpr': '\tranShkStd'})
# init_idiosyncratic_shocks['_fcts'].update({'tranShkStd': tranShkStd_fcts})
init_idiosyncratic_shocks.update({'tranShkStd_fcts': tranShkStd_fcts})

UnempPrb_fcts = {
    'about': 'Probability of unemployment while working'}
UnempPrb_fcts.update({'latexexpr': r'\UnempPrb'})
UnempPrb_fcts.update({'_unicode_': '℘'})
# init_idiosyncratic_shocks['_fcts'].update({'UnempPrb': UnempPrb_fcts})
init_idiosyncratic_shocks.update({'UnempPrb_fcts': UnempPrb_fcts})

UnempPrbRet_fcts = {
    'about': '"unemployment" in retirement = big medical shock'}
UnempPrbRet_fcts.update({'latexexpr': r'\UnempPrbRet'})
# init_idiosyncratic_shocks['_fcts'].update({'UnempPrbRet': UnempPrbRet_fcts})
init_idiosyncratic_shocks.update({'UnempPrbRet_fcts': UnempPrbRet_fcts})

IncUnemp_fcts = {
    'about': 'Unemployment insurance replacement rate'}
IncUnemp_fcts.update({'latexexpr': '\IncUnemp'})
IncUnemp_fcts.update({'_unicode_': 'μ'})
# init_idiosyncratic_shocks['_fcts'].update({'IncUnemp': IncUnemp_fcts})
init_idiosyncratic_shocks.update({'IncUnemp_fcts': IncUnemp_fcts})

IncUnempRet_fcts = {
    'about': 'Size of medical shock (frac of perm inc)'}
# init_idiosyncratic_shocks['_fcts'].update({'IncUnempRet': IncUnempRet_fcts})
init_idiosyncratic_shocks.update({'IncUnempRet_fcts': IncUnempRet_fcts})

tax_rate_fcts = {
    'about': 'Flat income tax rate'}
tax_rate_fcts.update({
    'about': 'Size of medical shock (frac of perm inc)'})
# init_idiosyncratic_shocks['_fcts'].update({'tax_rate': tax_rate_fcts})
init_idiosyncratic_shocks.update({'tax_rate_fcts': tax_rate_fcts})

T_retire_fcts = {
    'about': 'Period of retirement (0 --> no retirement)'}
# init_idiosyncratic_shocks['_fcts'].update({'T_retire': T_retire_fcts})
init_idiosyncratic_shocks.update({'T_retire_fcts': T_retire_fcts})

permShkCount_fcts = {
    'about': 'Num of pts in discrete approx to permanent income shock dstn'}
# init_idiosyncratic_shocks['_fcts'].update({'permShkCount': permShkCount_fcts})
init_idiosyncratic_shocks.update({'permShkCount_fcts': permShkCount_fcts})

tranShkCount_fcts = {
    'about': 'Num of pts in discrete approx to transitory income shock dstn'}
# init_idiosyncratic_shocks['_fcts'].update({'tranShkCount': tranShkCount_fcts})
init_idiosyncratic_shocks.update({'tranShkCount_fcts': tranShkCount_fcts})

aXtraMin_fcts = {
    'about': 'Minimum end-of-period "assets above minimum" value'}
# init_idiosyncratic_shocks['_fcts'].update({'aXtraMin': aXtraMin_fcts})
init_idiosyncratic_shocks.update({'aXtraMin_fcts': aXtraMin_fcts})

aXtraMax_fcts = {
    'about': 'Maximum end-of-period "assets above minimum" value'}
# init_idiosyncratic_shocks['_fcts'].update({'aXtraMax': aXtraMax_fcts})
init_idiosyncratic_shocks.update({'aXtraMax_fcts': aXtraMax_fcts})

aXtraNestFac_fcts = {
    'about': 'Exponential nesting factor when constructing "assets above minimum" grid'}
# init_idiosyncratic_shocks['_fcts'].update({'aXtraNestFac': aXtraNestFac_fcts})
init_idiosyncratic_shocks.update({'aXtraNestFac_fcts': aXtraNestFac_fcts})

aXtraCount_fcts = {
    'about': 'Number of points in the grid of "assets above minimum"'}
# init_idiosyncratic_shocks['_fcts'].update({'aXtraMax': aXtraCount_fcts})
init_idiosyncratic_shocks.update({'aXtraMax_fcts': aXtraCount_fcts})

aXtraCount_fcts = {
    'about': 'Number of points to include in grid of assets above minimum possible'}
# init_idiosyncratic_shocks['_fcts'].update({'aXtraCount': aXtraCount_fcts})
init_idiosyncratic_shocks.update({'aXtraCount_fcts': aXtraCount_fcts})

aXtraExtra_fcts = {
    'about': 'List of other values of "assets above minimum" to add to the grid (e.g., 10000)'}
# init_idiosyncratic_shocks['_fcts'].update({'aXtraExtra': aXtraExtra_fcts})
init_idiosyncratic_shocks.update({'aXtraExtra_fcts': aXtraExtra_fcts})

aXtraGrid_fcts = {
    'about': 'Grid of values to add to minimum possible value to obtain actual end-of-period asset grid'}
# init_idiosyncratic_shocks['_fcts'].update({'aXtraGrid': aXtraGrid_fcts})
init_idiosyncratic_shocks.update({'aXtraGrid_fcts': aXtraGrid_fcts})

vFuncBool_fcts = {
    'about': 'Whether to calculate the value function during solution'
}
# init_idiosyncratic_shocks['_fcts'].update({'vFuncBool': vFuncBool_fcts})
init_idiosyncratic_shocks.update({'vFuncBool_fcts': vFuncBool_fcts})

CubicBool_fcts = {
    'about': 'Use cubic spline interpolation when True, linear interpolation when False'
}
# init_idiosyncratic_shocks['_fcts'].update({'CubicBool': CubicBool_fcts})
init_idiosyncratic_shocks.update({'CubicBool_fcts': CubicBool_fcts})

# Make a dictionary to specify a "kinked R" idiosyncratic shock consumer
init_kinked_R = dict(
    init_idiosyncratic_shocks,
    **{
        "Rboro": 1.20,  # Interest factor on assets when borrowing, a < 0
        "Rsave": 1.02,  # Interest factor on assets when saving, a > 0
        "BoroCnstArt": None,  # kinked R is a bit silly if borrowing not allowed
        "CubicBool": True,  # kinked R is now compatible with linear cFunc and cubic cFunc
        "aXtraCount": 48,  # ...so need lots of extra gridpoints to make up for it
    }
)
del init_kinked_R["Rfree"]  # get rid of constant interest factor

# Main calibration characteristics
birth_age = 25
death_age = 90
adjust_infl_to = 1992
# Use income estimates from Cagetti (2003) for High-school graduates
education = "HS"
income_calib = Cagetti_income[education]

# Income specification
income_params = parse_income_spec(
    age_min=birth_age,
    age_max=death_age,
    adjust_infl_to=adjust_infl_to,
    **income_calib,
    SabelhausSong=True
)

# Initial distribution of wealth and permanent income
dist_params = income_wealth_dists_from_scf(
    base_year=adjust_infl_to, age=birth_age, education=education, wave=1995
)

# We need survival probabilities only up to death_age-1, because survival
# probability at death_age is 1.
liv_prb = parse_ssa_life_table(
    female=False, cross_sec=True, year=2004, min_age=birth_age, max_age=death_age
    - 1)

# Parameters related to the number of periods implied by the calibration
time_params = parse_time_params(age_birth=birth_age, age_death=death_age)

# Update all the new parameters
init_lifecycle = copy(init_idiosyncratic_shocks)
init_lifecycle.update(time_params)
init_lifecycle.update(dist_params)
# Note the income specification overrides the pLvlInitMean from the SCF.
init_lifecycle.update(income_params)
init_lifecycle.update({"LivPrb": liv_prb})


# Make a dictionary to specify an infinite consumer with a four period cycle
init_cyclical = copy(init_idiosyncratic_shocks)
init_cyclical['PermGroFac'] = [1.082251, 2.8, 0.3, 1.1]
init_cyclical['permShkStd'] = [0.1, 0.1, 0.1, 0.1]
init_cyclical['tranShkStd'] = [0.1, 0.1, 0.1, 0.1]
init_cyclical['LivPrb'] = 4*[0.98]
init_cyclical['T_cycle'] = 4


# def def_reward(stge):
#     stge = def_utility_CRRA(stge, stge.Pars.CRRA)
#     return stge

def def_reward(stge, reward=def_utility_CRRA):
    stge = reward(stge, stge.Pars.CRRA)
    return stge
