#!/usr/bin/env python3

import random
import copy
import time
from collections import defaultdict

import signal
import sys


##########################################################
## The base class of a pattern, the basis of the game


class pattern:

	#subelems: the subelements of this pattern
	#mutators: list of: (functions that shuffle and manipulate the sub_elemes, args to said func)
	def __init__(self, sub_elems=[], mutators=[]):
		self.sub_elems = sub_elems
		self.mutators = mutators

	def read_and_mutate(self):
		out = []
		for e in self.sub_elems:
			if type(e)==str:
				out += [e]
			elif type(e)==pattern:
				out += [e.read_and_mutate()]

		self.mutate()
		return out

	def mutate(self):

		# print('mutators are', self.mutators)

		for mnum in range( len( self.mutators )):

			mfunc, margs = self.mutators[mnum]

			# print('doing mutation', mnum, 'func, args:', mfunc, margs)

			self.sub_elems, new_margs = mfunc( self.sub_elems, *margs )

			# print('new mut will be', (mfunc, new_margs))

			self.mutators[mnum] = (mfunc, new_margs)

		# for mutate_function, args in self.mutators:
		#    self.sub_elems, args = mutate_function( self.sub_elems, *args )


############
## Mutator functions:
##    accepts elems, and as many args as needed
##	  returns new elems, [args for next call]
##

def print_elems(elems):
	outstr = ''
	for e in elems:
		outstr += str(e)
	return outstr


#shift the elems either to the left or right
def mutate_shift( elems, direction ):
	if direction=='left':
		return elems[1:] + [elems[0]], [direction]
	elif direction=='right':
		return [elems[-1]] + elems[:-1], [direction]
	print( 'mutate_shift: error, invalid direction', direction )
	return elems, [direction]

def ret_mutate_shift( n_elems, subs_dat=[] ):
	return mutate_shift, [random.choice(['left', 'right'])]


#replace the element at <ind> with a different element
def mutate_replace( elems, ind, replace_elem ):

	# print( 'orig elems:', print_elems(elems), '' )

	old_elem = elems[ind]

	new_elems = copy.deepcopy( elems )
	new_elems[ind] = replace_elem

	# print( 'new, old elem at', ind, replace_elem, old_elem )
	# print( 'new elems:', print_elems(new_elems) )

	return new_elems, [ind, old_elem]

def ret_mutate_replace( n_elems, subs_dat=[] ):
	ind = random.randrange(n_elems)
	# print('constructing elem from', subs_dat)
	sub = random.choice(subs_dat)
	if type(sub) in (list, tuple):
		elem = constructor( *random.choice(subs_dat) )
	else: elem = sub
	return mutate_replace, [ind, elem]


#replace the elements and indexes <ind1> and <ind2>
def mutate_switch( elems, ind1, ind2 ):

	elems[ind1], elems[ind2] = elems[ind2], elems[ind1]

	return elems, [ind1, ind2]

def ret_mutate_switch( n_elems, subs_dat=[] ):
	ind1 = ind2 = 0
	while ind1==ind2: ind1, ind2 = random.randrange(n_elems), random.randrange(n_elems)
	return mutate_switch, [ind1, ind2]


#############
## Levels


#creates and gives a pattern
#subs_dat: list of either <string (color), or a list of arguments to pass to constructor() to make a sub pattern>
#mut_funcs: list of mutator constructor functions
def constructor(n_subs, n_muts, mut_funcs, subs_dat):

	# print('n_subs, n_muts, mut_funcs, subs_dat:', n_subs, n_muts, mut_funcs, subs_dat)

	#if passed in ranges of values, get definite values
	if type(n_muts)==list: n_muts = random.randrange( *n_muts )
	if type(n_subs)==list: n_subs = random.randrange( *n_subs )

	#generate the subs
	subs = []
	for s in range(n_subs):
		newsub = random.choice(subs_dat)
		if type(newsub)==str:
			subs += [newsub]
		elif type(newsub)==list:
			subs += [constructor(*newsub)]
		else: print('error: constructor: bad sub', sub)

	#generate the mutators
	muts = []
	for m in range(n_muts):
		mut_func = random.choice(mut_funcs)
		muts += [mut_func(n_subs, subs_dat)]

	#construct the pattern
	res_pat = pattern(subs, muts)

	#make sure it's different after mutation, if a mutation was specified
	if n_muts>0:
		elems1 = copy.deepcopy(res_pat.sub_elems)
		res_pat.mutate()
		elems2 = copy.deepcopy(res_pat.sub_elems)
		res_pat.mutate()
		elems3 = copy.deepcopy(res_pat.sub_elems)
		res_pat.mutate()
		
		if elems1==elems2==elems3:
			# print('pattern did not change, making a new one, elems are\n\t%s\n\t%s\n\t%s'%(print_elems(elems1),print_elems(elems2),print_elems(elems3)))
			# print('pattern did not change, making a new one')
			return constructor(n_subs, n_muts, mut_funcs, subs_dat)

	#return the new pattern
	return res_pat

###################################################
## Functions for actually playing the game

def test_guess_matches(guess, elem):

	#standardize input data
	test_elem = []
	for c in elem:
		if c in colored_colors:
			test_elem.append(uncolored_colors[colored_colors.index(c)])
			# pass
		else: 
			test_elem.append(c)

	test_guess=[]
	for c in guess:
		if c in ' \t-': continue
		test_guess.append(c.lower())

	#test equivalency
	if test_elem==test_guess:
		return True
	else:
		return False

def play_round(level_name, elems, n_guesses):
	
	cur_correct = 0
	total_nguesses = 0

	for e_ind, elem in enumerate(elems):

		#clear the screen
		print('\x1B[2J\x1B[H')

		banner = '%s:\n%d elements left\n%d/%d correct guesses to go' % (level_name, len(elems)-1-e_ind, n_guesses-cur_correct, n_guesses)

		print(banner)

		for print_e in range(e_ind+1):
			print('%3d: '%print_e,end='')
			line = elems[print_e]
			for c in line:
				print(c, end=' ')
			print()

		if e_ind+1==len(elems):
			print('Ran out of lines to guess\nRound lost')
			time.sleep(long_pausetime)
			return False


		uin = input('Guess: ')
		if uin in ['exit', 'quit', 'e', 'q']: return False
		total_nguesses += 1
		next_elem = elems[e_ind+1]
		if test_guess_matches(uin, next_elem):
			print('Correct!')
			cur_correct+=1
			if cur_correct==n_guesses:
				print('\n --- \nRound complete!')
				time.sleep(long_pausetime)
				return total_nguesses
		else:
			print('Incorrect')
			cur_correct = 0

		time.sleep(interaction_pausetime)


	print('Ran out of given lines to guess\nRound lost')
	time.sleep(long_pausetime)
	return False


def play_level(level_params, level_name):

	n_rounds = 3

	total_nguesses = 0

	#play for three rounds
	for i in range(1,n_rounds+1):
		print('RGBgame level %s: Round %d!'%(level_name, i))

		needed_correct, n_lines, params = level_params
		playpattern = constructor( *params )

		#read the play pattern
		elems = []
		while len(elems)<n_lines:
			elems += [playpattern.read_and_mutate()]
		elems = flatten_results(elems)
		elems = elems[:n_lines]

		res = play_round(level_name+' Round%d/%d'%(i,n_rounds), elems, needed_correct)

		if res==False:
			print('You\'ve lost level %s', level_name)
			return False
		else:
			total_nguesses += res

	print('\n ======== \nCongrats! You\'ve finished %s\nYou used %d guesses'%(level_name,total_nguesses))

	time.sleep(long_pausetime)

	return total_nguesses


def print_lobby(levelnames, completed):


	#clear the screen
	print('\x1B[2J\x1B[H')

	print(' === RGB Game lobby === ')

	#print available levels
	print(' Available levels:')
	for lnum, lname in enumerate(levelnames):
		if completed[lnum]: 
			lcomplete = '[\x1B[32m%d\x1B[0m]'%completed[lnum] #green X and level score
			lcomplete+=' '*(3-(len(str(completed[lnum]))))
		else: lcomplete = '[\x1B[31mO\x1B[0m]  ' #red O
		print( '   %d: %s%s' % (lnum, lcomplete, lname) )


def game_lobby(levels, levelnames, completed=defaultdict(int)):


	while True:

		print_lobby(levelnames, completed)

		uin = input('\nSelect level to play (input a number)\n : ')
		try:
			uin = int(uin)
		except ValueError:
			print('Invalid input:', uin, '\n(must be the number corresponding to a level)')
			time.sleep(interaction_pausetime)
			continue

		if uin >= len(levels) or uin<0:
			print('Invalid inputted number, please a number from 0 to %d'%(len(levelnames)-1))
			time.sleep(interaction_pausetime)
			continue

		print('\n ======= \n Playing level \'%s\' \n (type \'e\' or \'q\' to exit level)'%levelnames[uin])
		time.sleep(interaction_pausetime)

		level_res = play_level( levels[uin], levelnames[uin] )

		if level_res!=False:
			completed[uin] = level_res





#the colors. Colored & uncolored must be in same order
uncolored_colors = ['r', 'g', 'b', 'c', 'm', 'w', 'y', 'k']
colored_colors = ['\033[31;1mr\033[0m', '\033[32;1mg\033[0m', '\033[34;1mb\033[0m', '\033[36;1mc\033[0m', '\033[35;1mm\033[0m', '\033[37;1mw\033[0m', '\033[33;1my\033[0m', '\033[30;47mk\033[0m']

#How long to pause for interactions / events
interaction_pausetime = 1.7
long_pausetime = 5


def play():

	colors = colored_colors
	# colors = uncolored_colors

	#Level paramters
	# list of (number of correct guesses in a row to win a round, level parameters)
	# level parameters are the same as a set of constructor arguments:
	#     (number of sub-elems, number of mutators, mutator functions, sub_elems)
	#   sub_elems are either color-strings or the parameters for another pattern
	levels = [
		#level0
		( 3, 10, (4, 2, [ret_mutate_shift, ret_mutate_switch], colors[:3])),
		#level1
		( 4,  20, (2, 1, [ret_mutate_shift, ret_mutate_switch], 
			[ [4, 1, [ret_mutate_shift, ret_mutate_switch], colors[:4]] ])),
		#level2
		( 4,  20, (4, 2, [ret_mutate_shift, ret_mutate_switch],
			[ [3, 0, [], colors[:3]] ]
		)),
		#level3
		( 5,  20, (2, 0, [ret_mutate_shift, ret_mutate_switch], [
			[ 3, 1, [ret_mutate_shift, ret_mutate_switch], [
				[3, 0, [], colors[:3] ] 
			]]
		] )),
		#level4
		( 4, 25, (3, 2, [ret_mutate_switch, ret_mutate_shift],
			[
			[4, 1, [ret_mutate_switch, ret_mutate_shift], colors[:4]],
			[2, 1, [ret_mutate_shift], [
				[4, 1, [ret_mutate_switch, ret_mutate_shift], colors[:4]]
			]]
		]
		)),
		#level5
		( 3,  18, (2, 2, [ret_mutate_switch], [
			[ 4, 5, [ret_mutate_replace], colors[:5] ]
		] 
		)),
	]

	#create the names for the levels
	levelnames = []
	for lind in range(len(levels)): 
		levelnames.append( 'Level'+str(lind) )

	completed = defaultdict(int)
	game_lobby(levels, levelnames, completed)




def flatten_results(res):
	out = []
	for item in res:
		if type(item[0])==str:
			out.append(item)
		elif type(item[0])==list:
			out += flatten_results( item )
		else:
			print('error:flatten_results: invalid item', item)
	return out


#catch ctrl-c
def signal_handler(signal, frame):
        print('\n\nExiting.\n')
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
	play()



