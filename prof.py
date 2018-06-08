import rbnf.zero as ze
import timeit

ze_exp = ze.compile("""
pyimport rbnf.std.common.[recover_codes]
import std.common.[Space]
pattern ::= (~ ('/' | Space))+ as seq
            rewrite seq
url ::= ('https' | 'http') as prefix 
        '://'              as slash 
        pattern            as head 
        ('/' pattern)*     as tail 
        ['/'] 
        rewrite
            _tokens = [prefix, slash, *head, *tail]
            recover_codes(_tokens)

text ::= (url | ~url)+ as urls
        rewrite
            tuple(url for url in urls if isinstance(url, str))
lexer_helper := R'.'
""", use='text')
text = """
<html lang="en">
  <head>
    <meta charset="utf-8">
  <link rel="dns-prefetch" href="https://assets-cdn.github.com">
  <link rel="dns-prefetch" href="https://avatars0.githubusercontent.com">
  <link rel="dns-prefetch" href="https://avatars1.githubusercontent.com">
  <link rel="dns-prefetch" href="https://avatars2.githubusercontent.com">
  <link rel="dns-prefetch" href="https://avatars3.githubusercontent.com">
  <link rel="dns-prefetch" href="https://github-cloud.s3.amazonaws.com">
  <link rel="dns-prefetch" href="https://user-images.githubusercontent.com/">

  <link crossorigin="anonymous" media="all" integrity="sha512-PkbtxdWDpLChpxtWQ0KbvJoef4XMYPq5pfd/ZmylYZTzXYpCfGwN9d+bsSKcmOJLwTkfjFkfj5wz3poDrhJoSQ==" rel="stylesheet" href="https://assets-cdn.github.com/assets/frameworks-f6e6ce21346c0d2eb22def1e8534afcb.css" />
  <link crossorigin="anonymous" media="all" integrity="sha512-LHNZGPA72iEyT2UIFOpxTPnfDcJ1Ecx8MKZgMzCJzkqfID/5niECnSBbRtDc4LDgbI3YDHu5dgs5mQiMmum6cA==" rel="stylesheet" href="https://assets-cdn.github.com/assets/github-caf1b1f61473986b3fdfa6e73e76a94f.css" />

  <meta name="viewport" content="width=device-width">
....
"""
timeit.timeit("ze_exp.match(text)", globals=globals(), number=100)