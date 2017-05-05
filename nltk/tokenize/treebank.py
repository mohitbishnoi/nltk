# Natural Language Toolkit: Tokenizers
#
# Copyright (C) 2001-2017 NLTK Project
# Author: Edward Loper <edloper@gmail.com>
#         Michael Heilman <mheilman@cmu.edu> (re-port from http://www.cis.upenn.edu/~treebank/tokenizer.sed)
#
# URL: <http://nltk.sourceforge.net>
# For license information, see LICENSE.TXT

r"""

Penn Treebank Tokenizer

The Treebank tokenizer uses regular expressions to tokenize text as in Penn Treebank.
This implementation is a port of the tokenizer sed script written by Robert McIntyre
and available at http://www.cis.upenn.edu/~treebank/tokenizer.sed.
"""

import re
from nltk.tokenize.api import TokenizerI
from nltk.tokenize.util import align_tokens


class MacIntyreContractions:
    """
    List of contractions adapted from Robert MacIntyre's tokenizer.
    """
    CONTRACTIONS2 = [r"(?i)\b(can)(?#X)(not)\b",
                     r"(?i)\b(d)(?#X)('ye)\b",
                     r"(?i)\b(gim)(?#X)(me)\b",
                     r"(?i)\b(gon)(?#X)(na)\b",
                     r"(?i)\b(got)(?#X)(ta)\b",
                     r"(?i)\b(lem)(?#X)(me)\b",
                     r"(?i)\b(mor)(?#X)('n)\b",
                     r"(?i)\b(wan)(?#X)(na)\s"]
    CONTRACTIONS3 = [r"(?i) ('t)(?#X)(is)\b", r"(?i) ('t)(?#X)(was)\b"]
    CONTRACTIONS4 = [r"(?i)\b(whad)(dd)(ya)\b",
                     r"(?i)\b(wha)(t)(cha)\b"]


class TreebankWordTokenizer(TokenizerI):
    """
    The Treebank tokenizer uses regular expressions to tokenize text as in Penn Treebank.
    This is the method that is invoked by ``word_tokenize()``.  It assumes that the
    text has already been segmented into sentences, e.g. using ``sent_tokenize()``.

    This tokenizer performs the following steps:

    - split standard contractions, e.g. ``don't`` -> ``do n't`` and ``they'll`` -> ``they 'll``
    - treat most punctuation characters as separate tokens
    - split off commas and single quotes, when followed by whitespace
    - separate periods that appear at the end of line

        >>> from nltk.tokenize import TreebankWordTokenizer
        >>> s = '''Good muffins cost $3.88\\nin New York.  Please buy me\\ntwo of them.\\nThanks.'''
        >>> TreebankWordTokenizer().tokenize(s)
        ['Good', 'muffins', 'cost', '$', '3.88', 'in', 'New', 'York.', 'Please', 'buy', 'me', 'two', 'of', 'them.', 'Thanks', '.']
        >>> s = "They'll save and invest more."
        >>> TreebankWordTokenizer().tokenize(s)
        ['They', "'ll", 'save', 'and', 'invest', 'more', '.']
        >>> s = "hi, my name can't hello,"
        >>> TreebankWordTokenizer().tokenize(s)
        ['hi', ',', 'my', 'name', 'ca', "n't", 'hello', ',']
    """

    #starting quotes
    STARTING_QUOTES = [
        (re.compile(r'^\"'), r'``'),
        (re.compile(r'(``)'), r' \1 '),
        (re.compile(r'([ (\[{<])"'), r'\1 `` '),
    ]

    #punctuation
    PUNCTUATION = [
        (re.compile(r'([:,])([^\d])'), r' \1 \2'),
        (re.compile(r'([:,])$'), r' \1 '),
        (re.compile(r'\.\.\.'), r' ... '),
        (re.compile(r'[;@#$%&]'), r' \g<0> '),
        (re.compile(r'([^\.])(\.)([\]\)}>"\']*)\s*$'), r'\1 \2\3 '), # Handles the final period.
        (re.compile(r'[?!]'), r' \g<0> '),

        (re.compile(r"([^'])' "), r"\1 ' "),
    ]

    # Pads parentheses
    PARENS_BRACKETS = (re.compile(r'[\]\[\(\)\{\}\<\>]'), r' \g<0> ')

    # Optionally: Convert parentheses, brackets and converts them to PTB symbols.
    CONVERT_PARENTHESES = [
        (re.compile(r'\('), '-LRB-'), (re.compile(r'\)'), '-RRB-'),
        (re.compile(r'\['), '-LSB-'), (re.compile(r'\]'), '-RSB-'),
        (re.compile(r'\{'), '-LCB-'), (re.compile(r'\}'), '-RCB-')
    ]

    DOUBLE_DASHES = (re.compile(r'--'), r' -- ')

    #ending quotes
    ENDING_QUOTES = [
        (re.compile(r'"'), " '' "),
        (re.compile(r'(\S)(\'\')'), r'\1 \2 '),
        (re.compile(r"([^' ])('[sS]|'[mM]|'[dD]|') "), r"\1 \2 "),
        (re.compile(r"([^' ])('ll|'LL|'re|'RE|'ve|'VE|n't|N'T) "), r"\1 \2 "),
    ]

    # List of contractions adapted from Robert MacIntyre's tokenizer.
    _contractions = MacIntyreContractions()
    CONTRACTIONS2 = list(map(re.compile, _contractions.CONTRACTIONS2))
    CONTRACTIONS3 = list(map(re.compile, _contractions.CONTRACTIONS3))

    def tokenize(self, text, convert_parentheses=False, return_str=False):
        for regexp, substitution in self.STARTING_QUOTES:
            text = regexp.sub(substitution, text)

        for regexp, substitution in self.PUNCTUATION:
            text = regexp.sub(substitution, text)

        # Handles parentheses.
        regexp, substitution = self.PARENS_BRACKETS
        text = regexp.sub(substitution, text)
        # Optionally convert parentheses
        if convert_parentheses:
            for regexp, substitution in self.CONVERT_PARENTHESES:
                text = regexp.sub(substitution, text)

        # Handles double dash.
        regexp, substitution = self.DOUBLE_DASHES
        text = regexp.sub(substitution, text)

        #add extra space to make things easier
        text = " " + text + " "

        for regexp, substitution in self.ENDING_QUOTES:
            text = regexp.sub(substitution, text)

        for regexp in self.CONTRACTIONS2:
            text = regexp.sub(r' \1 \2 ', text)
        for regexp in self.CONTRACTIONS3:
            text = regexp.sub(r' \1 \2 ', text)

        # We are not using CONTRACTIONS4 since
        # they are also commented out in the SED scripts
        # for regexp in self._contractions.CONTRACTIONS4:
        #     text = regexp.sub(r' \1 \2 \3 ', text)

        return text if return_str else text.split()

    def span_tokenize(self, text):
        """
        Uses the post-hoc nltk.tokens.align_tokens to return the offset spans.

            >>> from nltk.tokenize import TreebankWordTokenizer
            >>> s = '''Good muffins cost $3.88\\nin New (York).  Please (buy) me\\ntwo of them.\\n(Thanks).'''
            >>> expected = [(0, 4), (5, 12), (13, 17), (18, 19), (19, 23),
            ... (24, 26), (27, 30), (31, 36), (38, 44), (45, 48), (49, 51),
            ... (52, 55), (56, 58), (59, 64), (65, 71), (71, 72)]
            >>> TreebankWordTokenizer().span_tokenize(s) == expected
            True
        """
        tokens = self.tokenize(text)
        return align_tokens(tokens, text)


class TreebankWordDetokenizer(TokenizerI):
    """
    The Treebank detokenizer uses the reverse regex operations corresponding to
    the Treebank tokenizer's regexes.

    Note:
    - There're additional assumption mades when undoing the padding of [;@#$%&]
      punctuation symbols that isn't presupposed in the TreebankTokenizer.
    - There're additional regexes added in reversing the parentheses tokenization,
       - the r'([\]\)\}\>])\s([:;,.])' removes the additional right padding added
         to the closing parentheses precedding [:;,.].
    - It's not possible to return the original whitespaces as they were because
      there wasn't explicit records of where '\n', '\t' or '\s' were removed at
      the text.split() operation.

        >>> from nltk.tokenize.treebank import TreebankWordTokenizer, TreebankWordDetokenizer
        >>> s = '''Good muffins cost $3.88\\nin New York.  Please buy me\\ntwo of them.\\nThanks.'''
        >>> d = TreebankWordDetokenizer()
        >>> t = TreebankWordTokenizer()
        >>> toks = t.tokenize(s)
        >>> d.detokenize(toks)
        'Good muffins cost $3.88 in New York. Please buy me two of them. Thanks.'

    The MXPOST parentheses substitution can be undone using the `convert_parentheses`
    parameter:

    >>> s = '''Good muffins cost $3.88\\nin New (York).  Please (buy) me\\ntwo of them.\\n(Thanks).'''
    >>> expected_tokens = ['Good', 'muffins', 'cost', '$', '3.88', 'in',
    ... 'New', '-LRB-', 'York', '-RRB-', '.', 'Please', '-LRB-', 'buy',
    ... '-RRB-', 'me', 'two', 'of', 'them.', '-LRB-', 'Thanks', '-RRB-', '.']
    >>> expected_tokens == t.tokenize(s, convert_parentheses=True)
    True
    >>> expected_detoken = 'Good muffins cost $3.88 in New (York). Please (buy) me two of them. (Thanks).'
    >>> expected_detoken == d.detokenize(t.tokenize(s, convert_parentheses=True), convert_parentheses=True)
    True
    """
    _contractions = MacIntyreContractions()
    CONTRACTIONS2 = [re.compile(pattern.replace('(?#X)', '\s'))
                    for pattern in _contractions.CONTRACTIONS2]
    CONTRACTIONS3 = [re.compile(pattern.replace('(?#X)', '\s'))
                    for pattern in _contractions.CONTRACTIONS3]

    #ending quotes
    ENDING_QUOTES = [
        (re.compile(r"([^' ])\s('ll|'LL|'re|'RE|'ve|'VE|n't|N'T) "), r"\1\2 "),
        (re.compile(r"([^' ])\s('[sS]|'[mM]|'[dD]|') "), r"\1\2 "),
        (re.compile(r'(\S)(\'\')'), r'\1\2 '),
        (re.compile(r" '' "), '"')
        ]

    # Handles double dashes
    DOUBLE_DASHES = (re.compile(r' -- '), r'--')

    # Optionally: Convert parentheses, brackets and converts them from PTB symbols.
    CONVERT_PARENTHESES = [
        (re.compile('-LRB-'), '('), (re.compile('-RRB-'), ')'),
        (re.compile('-LSB-'), '['), (re.compile('-RSB-'), ']'),
        (re.compile('-LCB-'), '{'), (re.compile('-RCB-'), '}')
    ]

    # Undo padding on parentheses.
    PARENS_BRACKETS = [(re.compile(r'\s([\[\(\{\<])\s'), r' \g<1>'),
                       (re.compile(r'\s([\]\)\}\>])\s'), r'\g<1> '),
                       (re.compile(r'([\]\)\}\>])\s([:;,.])'), r'\1\2')]

    #punctuation
    PUNCTUATION = [
        (re.compile(r"([^'])\s'\s"), r"\1' "),
        (re.compile(r'\s([?!])\s'), r'\g<1>'),
        (re.compile(r'([^\.])\s(\.)([\]\)}>"\']*)\s*$'), r'\1\2\3'),
        # When tokenizing, [;@#$%&] are padded with whitespace regardless of
        # whether there are spaces before or after them.
        # But during detokenization, we need to distinguish between left/right
        # pad, so we split this up.
        (re.compile(r'\s([#$])\s'), r' \g<1>'), # Left pad.
        (re.compile(r'\s([;%])\s'), r'\g<1> '), # Right pad.
        (re.compile(r'\s([&])\s'), r' \g<1> '), # Unknown pad.
        (re.compile(r'\s\.\.\.\s'), r'...'),
        (re.compile(r'\s([:,])\s$'), r'\1'),
        (re.compile(r'\s([:,])\s([^\d])'), r'\1\2')
        ]

    #starting quotes
    STARTING_QUOTES = [
        (re.compile(r'([ (\[{<])\s``'), r'\1"'),
        (re.compile(r'\s(``)\s'), r'\1'),
        (re.compile(r'^``'), r'\"'),
    ]

    def tokenize(self, tokens, convert_parentheses=False):
        """
        Python port of the Moses detokenizer.

        :param tokens: A list of strings, i.e. tokenized text.
        :type tokens: list(str)
        :return: str
        """
        text = ' '.join(tokens)
        # Reverse the contractions regexes.
        # Note: CONTRACTIONS4 are not used in tokenization.
        for regexp in self.CONTRACTIONS3:
            text = regexp.sub(r'\1\2', text)
        for regexp in self.CONTRACTIONS2:
            text = regexp.sub(r'\1\2', text)

        # Reverse the regexes applied for ending quotes.
        for regexp, substitution in self.ENDING_QUOTES:
            text = regexp.sub(substitution, text)

        # Undo the space padding.
        text = text.strip()

        # Reverse the padding on double dashes.
        regexp, substitution = self.DOUBLE_DASHES
        text = regexp.sub(substitution, text)

        if convert_parentheses:
            for regexp, substitution in self.CONVERT_PARENTHESES:
                text = regexp.sub(substitution, text)

        # Reverse the padding regexes applied for parenthesis/brackets.
        for regexp, substitution in self.PARENS_BRACKETS:
            text = regexp.sub(substitution, text)

        # Reverse the regexes applied for punctuations.
        for regexp, substitution in self.PUNCTUATION:
            text = regexp.sub(substitution, text)

        # Reverse the regexes applied for starting quotes.
        for regexp, substitution in self.STARTING_QUOTES:
            text = regexp.sub(substitution, text)

        return text.strip()

    def detokenize(self, tokens, convert_parentheses=False):
        """ Duck-typing the abstract *tokenize()*."""
        return self.tokenize(tokens, convert_parentheses)
