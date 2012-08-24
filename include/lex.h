#pragma once
#ifndef __LEX_HEADER__
#define __LEX_HEADER__

/**
 * Main Public Lexer API
 */

/**
 * Type Definitions
 *
 * These types are used later in the module to 
 * describe the tokens in the token stream. 
 */
typedef enum   _Lex_TokenType Lex_TokenType;
typedef struct _Lex_Token     Lex_Token;

/**
 * Lexer TokenType Enum
 *
 * This enum lists all the possible tokens that this lexer
 * can return.
 */
enum _Lex_TokenType {
	Lex_eof,
	Lex_number,
	Lex_id,
	Lex_module,
	Lex_semicolon,
	Lex_plus,
	Lex_minus,
	Lex_equals,
	Lex_var,
	Lex_lbrace,
	Lex_rbrace
};

/**
 * Lexer Token Structure
 * 
 * This structure contains all the information about a given 
 * token. The value is valid until at least the next call to 
 * getNextToken or peekNextToken;
 */
struct _Lex_Token {
	Lex_TokenType type;
	char * value;
};

/**
 * Token Accessor Methods
 * 
 * Calling these methods runs the lexer over the input buffer 
 * and returns the next token in the stream. If peekNextToken 
 * is called the token is not discarded and will be returned 
 * by the next call to either method.
 */
Lex_Token* Lex_getNextToken(void);
Lex_Token* Lex_peekNextToken(void);

/**
 * Token Printing Funciton
 * 
 * Prints a description of the given token to the standarard 
 * output stream. Mainly used for debugging purposes. 
 */
void Lex_printToken(Lex_Token* token);

#endif