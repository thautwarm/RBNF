import rbnf.zero as ze
ze.compile("""
pyimport rbnf.std.common.[recover_codes]
LexerHelper := R'.'
Formula ::= '`' (~'`')+ as content '`'
        rewrite " :math:`"+recover_codes(content)+'` '
Unit ::= Formula as formula | _ as other
         rewrite
            formula if not other else other.value
Text ::= Unit+ as seq
         rewrite ''.join(seq)
""")