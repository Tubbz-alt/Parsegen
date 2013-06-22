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

from parsegen.output import OutputContext
from parsegen.utils import lazyprop, Namespace
import pystache
import os
	
class MustacheContext(OutputContext):
	"""Mustache Context
	
	Prints out a grammar using the mustache templating language.
	"""
	
	def __init__(self, template_file, *args):
		OutputContext.__init__(self, *args)
		self.template_file = template_file
		self.register_option("token_flag_type", default="int")

	@lazyprop
	def symbols(self):
		return [
			self._transform_symbol(symbol)
			for symbol in self.grammar.expansions.values()
		]
		
	def _transform_symbol(self, symbol):
		nterms, terms = self._get_counts(symbol)
		
		return {
			'name' : symbol.name,
			'nullable' : symbol.is_nullable(),
			'nonterminal_count' : nterms,
			'terminal_count' : terms,
			'expansions' : [
				self._transform_expansion(exp)
				for exp in symbol.expansions if exp
			]
		}
	
	def _transform_expansion(self, exp):
		predictions = self.predictions_for_expansion(exp)
		return {
			'predictions' : predictions,
			'tokens' : self._transform_tokens(exp)
		}
	
	def _transform_tokens(self, tokens):
		n, t = 0, 0
		token_list = []
		for tok in tokens:
			temp = self._transform_token(tok)
			if temp['terminal']:
				temp['index'] = t
				t += 1
			else:
				temp['index'] = n
				n += 1
			token_list.append(temp)
		if token_list:
			token_list[-1]['last'] = True
		return token_list
	
	def _transform_token(self, token):
		terminal = token in self.grammar.header.terminals
		if terminal:
			name =  self.grammar.header.terminals[token]
			nullable = False
		else:
			name = token
			nullable = self.grammar.expansions[token].is_nullable()
		
		return {
			'name' : name,
			'nullable' : nullable,
			'terminal' : terminal
		}
	
	def _read_template(self):
		"""Read Template
		
		Reads the mustache template from the filesystem and returns it to be
		processed.
		"""

		path = os.path.join(os.path.dirname(__file__), self.template_file)
		path = os.path.normpath(path)
		with open(path) as f:
			return f.read()
	
	def write(self, file):
		"""Write
		
		Output the grammar to the file using a Mustache template.
		"""
		
		template = self._read_template()
		
		file.write(pystache.render(template, self))
