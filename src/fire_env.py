import numpy as np
import gym
from gym import spaces
import constants
from dynamic_action import DynamicSpace

class FireMageEnv(gym.Env):

    def __init__(self, config):
        super(FireMageEnv, self).__init__()
        self._config = config
        self._C = constant.Constant()
        self.reset()
        self.action_space = DynamicSpace(self._C._CASTS)
        
    def step(self, action):
        self._apply_decision(action)
        while self._advance():
            if self._state['global']['running_time'] < self._state['global']['duration']:
                self._state['global']['total_damage'] += self._state['global']['damage']

        # set action space
        next_hit = np.argmin(self._state['player']['cast_timer'])
        actions = set(range(self._C._CAST_GCD))
        actions.remove(self._C._CAST_FIRE_BLAST) # no cooldown on it anyway
        if self._state['player']['comb_avail'][next_hit] > 0:
            actions.add(self._C._CAST_COMBUSTION)
        if self._state['player']['buff_avail'][self._C._BUFF_POWER_INFUSION][next_hit] > 0:
            actions.add(self._C._CAST_POWER_INFUSION)
        if self._state['player']['buff_avail'][self._C._BUFF_MQG][next_hit] > 0:
            actions.add(self._C._CAST_MQG)
        self.action_space.set_actions(actions)

        # thoughts on observation:
        # self buffs
        # boss debuffs (all)
        # current spell
        # buff remaining
        # casts

        # thoughts on reward:
        # total damage since last cast
        reward = self._['global']['total_damage'] - self._state['player']['damage'][next_hit]
        

    def reset(self):
        num_mages = self._config['num_mages']
        duration = self._config['duration_average'] +\
                   self._config['duration_sigma']*np.random.randn()
        spell_power = self._config['sp_average'] +\
                      self._config['sp_sigma']*np.random.randn(num_mages)
        # first mage may be scorch mage, last is finisher
        spell_power.sort()
        hit_chance = self._config['hit_average'] +\
                     self._config['hit_sigma']*np.random.randn(num_mages)
        crit_chance = self._config['crit_average'] +\
                     self._config['crit_sigma']*np.random.randn(num_mages)
        cast_timer = np.abs(config._['response_time']*np.random.randn(num_mages))
        duration += np.min(cast_timer)
        cast_timer -= np.min(cast_timer)
        buff_avail = [[0 for bb in range(num_mages)] for aa in range(self._C._BUFFS)]
        buff_avail[self._C._BUFF_POWER_INFUSION][(num_mages - self._config['power_infusion']):-1] = 1
        buff_avail[self._C._BUFF_MQG][(num_mages - self._config['mqg']):-1] = 1
        self._state = {
            'global': {
                'total_damage': 0.0,
                'running_time': 0.0,
                'duration': duration,
                'decision': True
            },
            'boss': {
                'ignite_timer': 0.0,
                'ignite_count': 0,
                'ignite_value': 0.0,
                'ignite_multiplier': 0.0,
                'tick_timer': self._C._LONG_TIME,
                'scorch_timer': 0.0,
                'scorch_count': 0,
                'debuff_timer': [0.0 for aa in range(self._C._DEBUFFS)],
                'debuff_avail': [0 for aa in range(C._DEBUFFS)]
            },
            'player': {
                'cast_timer': cast_timer,
                'cast_type': C._CAST_GCD*np.ones(num_mages),
                'spell_timer': C._LONG_TIME*np.ones(num_mages),
                'spell_type': C._CAST_GCD*np.ones(num_mages).astype(np.int32),
                'comb_stack': np.zeros(num_mages).astype(np.int32),
                'comb_left': np.zeros(num_mages).astype(np.int32),
                'comb_avail': np.ones(num_mages).astype(np.int32),
                'cast_number': np.zeros(num_mages).astype(np.int32),
                'buff_timer': [[0.0 for bb in range(num_mages)] for aa in range(self._C._BUFFS)],
                'buff_avail': buff_avail,
                'spell_power': spell_power,
                'hit_chance': hit_chance,
                'crit_chance': crit_chance,
                'gcd': np.zeros(num_mages),
                'damage': np.zeros(num_mages)
            }
        }

        return

    def _subtime(self, add_time):
        self._state['global']['running_time'] += add_time
        self._state['player']['cast_timer'] -= add_time
        self._state['player']['spell_timer'] -= add_time
        self._state['boss']['ignite_timer']] -= add_time
        self._state['boss']['tick_timer'] -= add_time
        self._state['boss']['scorch_timer'] -= add_time
        for buff in range(self._C._BUFFS):
            self._state['player']['buff_timer'][buff] -= add_time
        for debuff in range(self._C._DEBUFFS):
            self._state['boss']['debuff_timer'][debuff] -= add_time

        return

    def _do_cast(self, add_time):
        next_hit = np.argmin(self._state['player']['cast_timer'])
        self._subtime(add_time)

        if self._C._LOG_SIM:
            message = '         ({:6.2f}): player {:d} finished casting {:s}'
            message = message.format(self._state['global']['running_time'],
                                     next_hit + 1,
                                     self._C._LOG_SPELL[self._state['player']['cast_type'][next_hit]])
            print(message)

        # transfer to spell
        if self._state['player']['cast_type'][next_hit] < self._C._CAST_GCD:
            self._state['player']['spell_type'][next_hit] = self._state['player']['cast_type'][next_hit]
            self._state['player']['spell_timer'][next_hit] = self._C._SPELL_TIME[self._state['player']['cast_type'][no_instant]]

        # apply instant spells
        if self._state['player']['cast_type'][next_hit] == self._C._CAST_COMBUSTION):
            self._state['player']['comb_left'][next_hit] = self._C._COMBUSTIONS
            self._state['player']['comb_stack'][next_hit] = 0
            self._state['player']['comb_avail'][next_hit] -= 1

        for buff in range(self._C._BUFFS):
            if self._state['player']['cast_type'][next_hit] == self._C._BUFF_CAST_TYPE[buff]:
                self._state['player']['buff_timer'][buff][next_hit] = self._C._BUFF_DURATION[buff]
                self._state['player']['buff_avail'][buff][next_hit] -= 1

        # determine gcd        
        gcd_array = self._state['player']['gcd'][cst, next_hit] > 0.0
        yes_gcd = np.where(gcd_array)[0]
        no_gcd = np.where(np.logical_not(gcd_array))[0]
        
        # push gcd
        if self._state['player']['gcd'][next_hit] > 0.0:
            self._state['player']['cast_type'][next_hit] = self._C._self._CAST_GCD
            self._state['player']['cast_timer'][next_hit] = self._state['player']['gcd'][next_hit]
            self._state['player']['gcd'][next_hit] = 0.0

            # inc cast number
            self._state['global']['decision'] = False
        else:
            self._state['global']['decision'] = True
            self._state['player']['cast_number'][next_hit] += 1 # attempt at batching

        return

    def do_spell(self, add_time):
        epsilon = 1.0e-6
    
        next_hit = np.argmin(self._state['player']['spell_timer'])
        self._subtime(add_time)

        # reset timer
        self._state['player']['spell_timer'][next_hit] = self._C._LONG_TIME

        if self._C._LOG_SIM:
            message = ' ({:6.2f}): player {:d} {:s} landed '
            message = message.format(self._state['global']['running_time'],
                                     next_hit + 1,
                                     self._C._LOG_SPELL[self._state['player']['spell_type'][next_hit]])
            message2 = 'misses         '

        if np.random.rand() < self._state['player']['hit_chance'][next_hit]:
            spell_type = self._state['player']['spell_type'][next_hit]

            spell_damage = self._C._SPELL_BASE[spell_type] + \
                           self._C._SPELL_RANGE[spell_type]*np.random.rand() +\
                           self._C._SP_MULTIPLIER[spell_type]*self._state['player']['spell_power'][next_hit]
            # self._CoE + talents
            spell_damage *= self._C._self._COE_MULTIPLIER*self._C._DAMAGE_MULTIPLIER[spell_type] 
            scorch = self._C._IS_FIRE[spell_type]*self._C._SCORCH_MULTIPLIER*self._state['boss']['scorch_count']
            spell_damage *= 1.0 + scorch*(self._state['boss']['scorch_timer'] > 0.0).astype(np.float)
            pi = (self._state['player']['buff_timer'][self._C._BUFF_POWER_INFUSION][next_hit] > 0.0).astype(np.float)
            spell_damage *= 1.0 + self._C._POWER_INFUSION*pi
            spell_damage *= self._C._DMF_BUFF
            self._state['global']['damage'] += spell_damage
            # ADD ADDITIONAL OVERALL MULTIPLIERS TO _DAMAGE_MULTIPLIER

            # handle critical hit/ignite ** READ HERE FOR MOST OF THE IGNITE MEself._CHANIself._CS **
            comb_crit = self._C._PER_COMBUSTION*self._state['player']['comb_stack'][next_hit]
            comb_crit *= (self._state['player']['comb_left'][next_hit] > 0).astype(np.float)
            comb_crit *= self._C._IS_FIRE[spell_type]
            crit_chance = self._state['player']['crit_chance'][next_hit] + comb_crit + self._C._INCIN_BONUS[spell_type]
            if np.random.rand() < crit_chance:
                if self._C._IS_FIRE[spell_type].astype(np.bool):
                    if self._C._LOG_SIM:
                        message2 = 'crits for {:4.0f} '.format((1.0 + self._C._ICRIT_DAMAGE)*spell_damage)
                    # remove ignite if expired
                    if self._state['boss']['ignite_timer'] <= 0.0:
                        self._state['boss']['ignite_count'] = 0
                        self._state['boss']['ignite_value'] = 0.0
            
                    # refresh ignite to full 4 seconds
                    self._state['boss']['ignite_timer'] = self._C._IGNITE_TIME + epsilon
            
                    # if we dont have a full stack
                    if self._state['boss']['ignite_count'] < self._C._IGNITE_STACK:
                        # add to the ignite tick damage -- 1.5 x  0.2 x spell hit damage
                        self._state['boss']['ignite_value'] += (1.0 + self._C._ICRIT_DAMAGE)*self._C._IGNITE_DAMAGE*spell_damage
                        self._state['boss']['ignite_multiplier'] = self._C._DMF_BUFF*(1.0 + self._C._POWER_INFUSION*pi)

                    # first in stack, set the tick
                    if not self._state['boss']['ignite_count']:
                        self._state['boss']['tick_timer'] = self._C._IGNITE_TICK

                    # increment to max of five (will do nothing if already at 5)
                    self._state['boss']['ignite_count'] = min([self._state['boss']['ignite_count'] + 1,
                                                               self._C._IGNITE_STACK])

                    # add crit to damage
                    self._state['global']['damage'][gbl_icrits] += self._C._ICRIT_DAMAGE*spell_damage
            
                    # remove from combustion
                    self._state['player']['comb_left'][next_hit] = max([self._state['player']['comb_left'][next_hit] - 1, 0])
                else:
                    if self._C._LOG_SIM:
                        message2 = 'crits for {:4.0f} '.format((1.0 + self._C._CRIT_DAMAGE)*spell_damage)
                    self._state['global']['damage'] += self._C._CRIT_DAMAGE*spell_damage
            else:
                if self._C._LOG_SIM:
                    message2 = ' hits for {:4.0f} '.format(spell_damage)

            # scorch
            if self._state['boss']['scorch_timer'] <= 0.0:
                self._state['boss']['scorch_count'] = 0
            
            if self._C._IS_SCORCH[spell_type]:
                self._state['boss']['scorch_timer'] = self._C._SCORCH_TIME
                self._state['boss']['scorch_count'] = min([self._state['boss']['scorch_count'] + 1,
                                                           self._C._SCORCH_STACK])
                    
            if self._C._IS_FIRE[spell_type]:
                self._state['player']['comb_stack'][next_hit] += 1

        if self._C._LOG_SIM:
            dam_done = ' {:7.0f}'.format(self._state['global']['total_damage'] + self._state['global']['damage'])
            message3 = self._C._LOG_SPELL[self._state['player']['cast_type'][next_hit]]
            message = message + message2 + 'next is ' + message3
            status = ' ic {:d} it {:4.2f} in {:s} id {:4.0f} sc {:d} st {:5.2f} cs {:2d} cl {:d}'
            ival = self._state['boss']['tick_timer']
            istat = '{:4.2f}'.format(ival) if ival > 0.0 and ival <= 2.0 else ' off'
            status = status.format(self._state['boss']['ignite_count'],
                                   max([self._state['boss']['ignite_timer'], 0.0]),
                                   istat,
                                   self._state['boss']['ignite_value'],
                                   self._state['boss']['scorch_count'],
                                   max([self._state['boss']['scorch_timer'], 0.0]),
                                   self._state['player']['comb_stack'][next_hit],
                                   self._state['player']['comb_left'][next_hit])
            print(dam_done + message + status)

    def _do_tick(self, add_time):
        self._subtime(add_time)
        
        if self._state['boss']['ignite_timer'] <= 0.0:
            self._state['boss']['tick_timer'] = self._C._LONG_TIME

        else:
            self._state['boss']['tick_timer'] = self._C._IGNITE_TICK

            scorch = self._C._SCORCH_MULTIPLIER*self._state['boss']['scorch_count']
            multiplier = self._C._COE_MULTIPLIER*self._state['boss']['ignite_multiplier']
            multiplier *= 1.0 + scorch*(self._state['boss']['scorch_timer'] > 0.0).astype(np.float)
            self._state['global']['damage'] += multiplier*self._state['boss']['ignite_value']
            if self._C._LOG_SIM:
                message = ' {:7.0f} ({:6.2f}): ignite ticked   {:4.0f} damage done'
                print(message.format(self._state['global']['total_damage'] + self._state['global']['damage'],
                                     self._state['global']['running_time'],
                                     multiplier[sub_index]*self._state['boss']['ignite_value']))
        return

    def _advance(self):
        self._state['global']['damage'] = 0.0

        if self._state['global']['running_time'] >= self._state['global']['duration'] or\
           self._state['global']['decision']:
            return False

        # cast finished
        cast_timer = mp.min(self._state['player']['cast_timer'])
        spell_timer = np.min(self._state['player']['spell_timer'])
        tick_timer = self._state['boss']['tick_timer']
        if cast_timer < spell_timer and cast_timer < tick_timer:
            self._do_cast(cast_timer)
        elif spell_timer < tick_timer:
            self._do_spell(spell_timer)
        else:
            self._do_tick(tick_timer)
    
        return True

    def _apply_decision(self, cast_type):
        next_hit = np.argmin(self._state['player']['cast_timer'])
        self._state['player']['damage'][next_hit] = self._['global']['total_damage']
        
        react_time = np.abs(self._config['react_time']*np.random.randn())
        self._state['player']['cast_type'][next_hit] = cast_type
        if cast_type < self._C._CAST_GCD:
            self._state['player']['cast_timer'][next_hit] = self._C._CAST_TIME[cast_type]
            if self._state['player']['buff_timer'][self._C._BUFF_MQG][next_hit] > 0.0:
                self._state['player']['cast_timer'][next_hit] /= 1.0 + self._C._MQG
        else:
            self._state['player']['cast_timer'][next_hit] = 0.0
    
        if self._state['player']['cast_type'][next_hit] < self._C._CAST_GCD:
            self._state['player']['gcd'] = np.max([0.0, self._C._GLOBAL_COOLDOWN + react_time - self._state['player']['cast_timer'][next_hit]])
    
        self._state['global']['decision'] = False

        return
  
def get_damage(sp, hit, crit, num_mages, response, sim_size):
    self._C = constants.Constant(sim_size=sim_size)
    self._state = constants.init_const_self._state(self._C, sp, hit, crit, num_mages, response)
    if  self._C._LOG_SIM >= 0:
        constants.log_message(sp, hit, crit)
    while True:
        
    if  self._C._LOG_SIM >= 0:
        print('total damage = {:7.0f}'.format(self._state['global']['total_damage'][ self._C._LOG_SIM]))

    return (self._state['global']['total_damage']/self._state['global']['duration']).mean()

def get_crit_damage_diff(sp, hit, crit, num_mages, response, sim_size):
    dcrit = 0.025
    dsp = 25.0
    factor = dsp/dcrit/100.0

    dm_sp = get_damage(sp - dsp, hit, crit, num_mages, response, sim_size)
    dp_sp = get_damage(sp + dsp, hit, crit, num_mages, response, sim_size)
    dm_crit = get_damage(sp, hit, crit - dcrit, num_mages, response, sim_size)
    dp_crit = get_damage(sp, hit, crit + dcrit, num_mages, response, sim_size)

    return factor*(dp_crit - dm_crit)/(dp_sp - dm_sp)

def get_hit_damage_diff(sp, hit, crit, num_mages, rotation, response, sim_size):
    dhit = 0.01
    dsp = 25.0
    factor = dsp/dhit/100.0

    dm_sp = get_damage(sp - dsp, hit, crit, num_mages, rotation, response, sim_size)
    dp_sp = get_damage(sp + dsp, hit, crit, num_mages, rotation, response, sim_size)
    dm_hit = get_damage(sp, hit - dhit, crit, num_mages, rotation, response, sim_size)
    dp_hit = get_damage(sp, hit + dhit, crit, num_mages, rotation, response, sim_size)

    return factor*(dp_hit - dm_hit)/(dp_sp - dm_sp)

