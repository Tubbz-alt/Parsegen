#! /usr/bin/env python3

# This file is part of Parsegen and is licensed as follows:
#
# Copyright (c) 2012 Will Speak
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import sys

class ParsegenError(Exception):
	"""Parsegen Error
	
	Root class for all exceptions in this module
	"""
	
	def __init__(self, error_name, string):	
		string = "parsegen: {0}: {1}".format(error_name, string)
		Exception.__init__(self, string)
	
class ParseError(ParsegenError):
	"""Parse Error
	
	Represents a failure to parse a grammar file. The reason for the failure is
	provided as a string.
	"""
	
	def __init__(self, string):
		"""ParseError Constructor
		
		Create a new parse error from a string. The string is automatically
		formatted for pretty printing in context with other errors. 
		"""
		
		ParsegenError.__init__(self, 'parse error', string)

class GrammarError(ParsegenError):
	"""Grammar Error
	
	Represent a logical error in one of the grammar expansions. The reason for 
	the failure is provided as a string.
	"""
	
	def __init__(self, string):
		"""GrammarError Constructor
		
		Create a new grammar error from a string. The string is automatically
		formatted.
		"""
		
		ParsegenError.__init__(self, 'grammar error', string)

class Header(object):
	"""Grammar File Header
	
	Represents the header section of the grammar file. Contains two mappings
	that represent the options and the terminal definitions.
	"""
	
	def __init__(self, terms, opts):
		"""Header Constructor
		
		Creates a new header from a given set of terminals and options. Both of
		these should be `dict`s containing mappings from the option/terminal 
		names to their values.
		"""
		
		self.options = opts
		self.terminals = terms
		
	def get_option(self, option, default=""):
		return self.options.get(option, default)

class Symbol(object):
	"""Grammar Symbol
	
	Represents the expansions of a given symbol.
	"""
	
	def __init__(self):
		self.expansions = []
		self.nullable = False
		self.first = set()
		self.follow = set()
	
	def __len__(self):
		return len(self.expansions)
	
	def add_expansion(self, expansion):
		"""Add Expansion
		
		Adds a list of token names to the expansions of this symbol. This method
		automatically sets the symbol to nullable if a null expansion is passed
		in.
		"""

		self.expansions.append(expansion)
		if not expansion:
			# We _know_ this symbol is nullable now, so set it
			self.set_nullable()

	def set_nullable(self):
		"""Set Nullable
		
		Mark the symbol as nullable. Nullable symbols are those that can expand
		to an empty string.
		"""
		
		self.nullable = True
	
	def is_nullable(self):
		"""Is Nullable
		
		Returns true if the symbol is nullable and false otherwise. A symbol with
		no expansions is considered nullable.
		"""
		
		if len(self.expansions) == 0:
			return True
		else:
			return self.nullable
			
	def _union_set_with_values(self, set_ref, values):
		"""Union Set With Values
		
		Set union helper method
		"""
		
		values = set(values)
		set_ref = set_ref.union(values)
		return set_ref
		
	def add_first(self, values):
		"""Add First
		
		Adds values to the first set. If any of the values are in the first set.
		This is a *set union* operation. `values` can be a set or a list.
		"""
		
		self.first = self._union_set_with_values(self.first, values)
		
	def add_follow(self, values):
		"""Add Follow
		
		Adds values to the follow set. If any of the values are in the first
		set. This is a *set union* operation. `values` can be a set or a list.
		"""
		
		self.follow = self._union_set_with_values(self.follow, values)
	
def parse_buffer(buffer):
	"""Parse Buffer
	
	Parse the given buffer and return a 3-tuple of the contents. The first
	element of the tuple is a Header object representing the definitions
	and options used, the second is a list of expansions and the third is a 
	string containing the contents of the user code section.
	"""
	
	try:
		sects = buffer.split("%%")
		header, expansions, user_code = sects
	except ValueError:
		raise ParseError("expected 3 sections but found {0}".format(len(sects)))
		
	# process the header section, to extract the options and stuff
	header = _process_header(header)
	
	# now we can process the expansions
	expansions = _process_expansions(expansions)
	expansions = _compute_sets_for_expansions(header, expansions)
	
	# Return the processed parts
	return header, expansions, user_code

def parse_file(file):
	"""Parse File
	
	Reads the contents of the file and parses the contents. Returns the same
	as `parse_buffer`.
	"""
	
	try:
		return parse_buffer(file.read())
	except AttributeError:
		pass
	
	with open(file, "r") as file:
		return parse_buffer(file.read())

def write_grammar(header, expansions, user_code, file=sys.stdout):
	"""Write Grammar
	
	Write a program out to the file that represents an automaton that parses
	the given grammar.
	"""
	
	_write_header_to_file(header, file)
	_write_helpers_to_file(header, file)

	_write_expansions_to_file(header, expansions, file)
	
	_write_user_code_to_file(user_code, file)


def _write_section_header(heading, file):
	"""Write Section Header
	
	Prints a commented header to mark a section within the output file.
	"""
	
	file.write('\n/' + '*' * 77 + '\n')
	file.write(" * {0} *\n".format(heading.center(73)))
	file.write(' ' + '*' * 77 + '/\n')

def _prefixed_default(header, default=None):
	"""Prefixed Default
	
	Returns a the string prefixed with the correct scope. This allows things to
	be namespaced and the user to control what string is used.
	"""
	
	prefix = header.get_option("prefix", 'yy')
	return prefix + '_' + default if default else prefix

def _write_header_to_file(header, file):
	"""Write Header to File
	
	Writes the beginning of the file. This is everything that should appear 
	before the utilities.
	"""
	
	_write_section_header("global includes", file)
	
	file.write("""
#include <stdio.h>
#include <stdlib.h>
#include {0}
	""".format(
		header.get_option("lexer_include", '<lexer.h>')
	))

def _write_helpers_to_file(header, file):
	"""Write Helpers to File
	
	Write out any functions and definitions required for the automaton to work.
	These would usually be the `get` and `peek` definitions.
	"""
	
	_write_section_header("utility methods", file)
	
	file.write("""

static {0} next_token;
static int token_buffered = 0;

{0} {1}_peek_next_token(void)
{{
	
	if (!token_buffered) {{
		next_token = {2};
		token_buffered = 1;
	}}
	
	return next_token;
}}

int {1}_eat_token({0} expected_token)
{{
	{0} token = {1}_peek_next_token();
	
	if (token == expected_token) {{
		token_buffered = 0;
		return 1;
	}}
	
	return 0;
}}
	""".format(
		header.get_option("token_type", _prefixed_default(header, 'token_t')),
		_prefixed_default(header),
		header.get_option(
			'lexer_function', _prefixed_default(header, 'get_next_token'))
	))

def _write_expansions_to_file(header, expansions, file):
	
	_write_section_header('main automaton', file)
	
	for name, symbol in expansions.items():
		_write_symbol_function_begin(header, name, symbol, file)
		for expansion in symbol.expansions:
			_write_body_for_expansion(header, expansions, name, expansion, file)
		_write_symbol_function_end(header, file)

def _get_counts(header, symbol):
	node_count = 0

	for expansion in symbol.expansions:
		n = 0
		for e in expansion:
			if not e in header.terminals:
				n += 1
		if n > node_count: node_count = n
	return node_count

def _write_symbol_function_begin(header, name, symbol, file):
	node_count = _get_counts(header, symbol)
	
	file.write("""
static {0}_node_t* {1}(void)
{{
	{0}_node_t* nodes[{3}];
	{2} token = {0}_peek_next_token();
	
	switch (token) {{
""".format(
		_prefixed_default(header),
		name,
		header.get_option("token_type", _prefixed_default(header, 'token_t')),
		node_count
	))

def _write_body_for_expansion(header, expansions, name, expansion, file):
	
	if not expansion:
		return
	
	terms = None
	if expansion and expansion[0] in header.terminals:
		terms = [expansion[0]]
	else:
		terms = expansions[expansion[0]].first
	
	for term in terms:
		file.write('\tcase {0}:\n'.format(header.terminals[term]))

	params = []
	node = 0
	
	for sym in expansion:
		if sym in header.terminals:
			file.write(
				"\t\tif (!eat_terminal({0}))\n\t\t\tgoto error;\n".format(
					header.terminals[sym]))
			params.append(header.terminals[sym])
		else:
			node_temp = "nodes[{0}]".format(node)
			node += 1
			file.write("\t\t{0} = {1}();\n".format(
				node_temp,
				sym
			))
			params.append(node_temp)
	
	file.write("\t\ttoken_action_{0}({1});\n".format(name, ", ".join(params)))
	file.write('\t\tbreak;\n\n')
	
def _write_symbol_function_end(header, file):
	file.write("\t}\n}\n")

def _write_user_code_to_file(code_block, file):
	"""Write User Code to File
	
	Writes a given block of code to the file prefixed with a user code header.
	"""
	
	_write_section_header('user code', file)
	file.write(code_block)

def _processed_lines(text):
	"""Processed Lines
	
	Returns an iterable containing all non-empty lines within the text with
	comments removed.
	"""
	for l in text.split("\n"):
		l, _, _ = l.partition("#")
		l = l.strip()
		if len(l):
			yield l

def _kv_with_sep(opt_line, sep="="):
	"""Key Value Pair
	
	Extracts a key-value pair from the `opt_line` using the separator, if given.
	"""
	key, _, val = opt_line.partition(sep)
	
	key = key.strip()
	val = val.strip()
	
	return key, val

def _add_opt_to_dict(opt_line, dict, sep="="):
	"""Add Option to Dictionary
	
	Extracts a `key = value` pair from the `opt_line` and adds the pair to the
	`dict`, uaing the optional separator `sep` to separate them.
	"""
	key, val = _kv_with_sep(opt_line, sep)
	
	dict[key] = val

def _process_header(header):
	"""Process Header
	
	Process the header section, splits the header definitions into two `dict`s
	so that they can be looked up later.
	"""
	
	terms = {}
	opts = {}
	
	for l in _processed_lines(header):
		if l[:1] == "%":
			_add_opt_to_dict(l[1:], opts)
		else:
			_add_opt_to_dict(l, terms)
	
	return Header(terms, opts)

def _process_expansions(expansions):
	"""Process Expansions
	
	Processes a block of text containing grammar expansions into a `dict`
	containing mappings from symbol names to Symbol objects.
	"""
	
	exps = {}
	
	for l in _processed_lines(expansions):
		sym, exp = _kv_with_sep(l, ":=")
		
		s = exps.get(sym, Symbol())
		s.add_expansion(exp.split())
		exps[sym] = s
		
	return exps

def _initialise_expansions_state(header, expansions):
	"""Initialise Expansions State
	
	Sets up the expansions ready to have the first and follow sets computed.
	"""
	
	for name, symbol in expansions.items():
		if name in header.terminals:
			raise GrammarError("expansion for nonterminal {0}".format(name))
		
		for exp in symbol.expansions:
			# This creates the initial first sets for each symbol
			if exp and exp[0] in header.terminals:
				symbol.add_first(exp[:1])
			
			for e in exp:
				if not (e in header.terminals or e in expansions):
					raise GrammarError(
					"{0} is not defined as a terminal or nonterminal".format(e))

def _each_expansion(expansions):
	"""Each Expansion
	
	Returns an iterator that yields a 3-tuple of name, symbol and expansion for
	each expansion in the given expansion `dict`.
	"""
	
	for name, symbol in expansions.items():
		for expansion in symbol.expansions:
			yield name, symbol, expansion

def _update_first_from_expansion(header, expansions, name, symbol, expansion):
	"""Update First from Expansion
	
	Updates the first set fro a given symbol based on one of it's expansions.
	Returns true if an update is made to the symbol and false otherwise.
	"""
	
	changed = False
	
	for e in expansion:
		if e in header.terminals:
			break
		other_sym = expansions[e]
		if not other_sym.first.issubset(symbol.first):
			symbol.add_first(other_sym.first)
			changed = True
		if not other_sym.is_nullable():
			break
	else:
		# if all of the expansions are nullable and there are no terminals then 
		# the symbol is nullable too
		if not symbol.is_nullable():
			symbol.set_nullable()
			changed = True
	
	return changed

def _update_follow_from_expansion(header, name, symbol, expansion):
	"""Update Follow from Expansion
	
	Updates the follow set for a given symbol based on one of it's expansions.
	Returns true if an update is made to the symbol and false otherwise.
	"""
	
	# TODO: implement follow sets
	
	return False

def _compute_sets_for_expansions(header, expansions):
	"""Compute Sets for Expansions
	
	Iteratively computes the first and follow sets for the grammar defined
	by the `header` and `expansions`. Will raise a GrammarError if 
	one of the expansions attempts to use an undefined nonterminal or if an
	expansion is defined for a terminal.
	"""
	
	_initialise_expansions_state(header, expansions)

	changed = True
	while changed:
		changed = False
		
		for name, symbol, expansion in _each_expansion(expansions):
			r = _update_first_from_expansion(
				header, expansions, name, symbol, expansion)
			s = _update_follow_from_expansion(header, name, symbol, expansion)
			changed = changed or r or s
	
	return expansions