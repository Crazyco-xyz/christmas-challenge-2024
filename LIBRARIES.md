# Libraries

I kind of want to separate the libraries into the three categories seen below. Comments on some of the libraries used
are below, or can be accessed by clicking on the name of the library!

## Internal Python libraries...

### ...that are not really libraries

I categorized these libraries into this section, because many other programming languages would not need any external
libraries to do these things or are even integrated into the core of the language.
Technically they are libraries, but few people would think of them this way.

- os
- sys
- logging
- [typing](#typing-enum-abc-and-io)
- [enum](#typing-enum-abc-and-io)
- threading
- [abc](#typing-enum-abc-and-io)
- re
- socket
- time
- datetime
- [urllib.parse](#urllibparse)
- select
- [io](#typing-enum-abc-and-io)
- [base64](#base64)

### ...that are actually libraries

I allowed myself to use some (but few) of the libraries that come with Python. Yes, they are technically libraries,
but they come with Python, meaning they do not need to be downloaded externally. Some of these libraries I also
needed so little, that it would just not make sense to write them myself.

- [sqlite3](#sqlite3)
- [uuid](#uuid-and-hashlib)
- [hashlib](#uuid-and-hashlib)
- json
- [mimetypes](#mimetypes)
- [gzip](#gzip-and-zlib)
- [zlib](#gzip-and-zlib)
- [ssl](#ssl)

## External libraries

The Python backend does not need _any_ external libraries. Everything is either written by myself or already included
with Python.

The only exception is the frontend where I allowed myself to use the
[FontAwesome](https://github.com/FortAwesome/Font-Awesome) icon pack to make things look just a little better.

## Comments

### urllib.parse

I would have considered this library in the second category if i actually used more than one function of it. The only
place where this library gets used is for unquoting the path sent by the browser which might have the usual percent
escape codes like `%20`. Because I only needed this once, I also decided against writing the implementation myself,
because this would be too much work for too little result, mostly in the time frame of this challenge.

### base64

Personally I would have considered this an external library, but many other programming languages come with base64
support out of the box, so I also categorized this one in the first category. You might disagree with this
categorization and that is ok. This whole categorization is pretty much based on personal oppinion, so there is no
right or wrong.

### typing, enum, abc and io

I really don't consider these to be libraries, because these things are available without any libraries in most other
programming languages. These libraries are mostly for flavor and the project would be possible without many changes
if you would decide to not use these libraries.

### sqlite3

A library which you would need to import externally for many other programming languages. I mostly decided to use it
in this project, because it is convenient and it is included in Python's standard libraries anyways, so why not?

### uuid and hashlib

I was not really sure where to put these, but I decided to add them to the second category, just because with enough
willpower I could have convinced myself to write these from scratch.

### mimetypes

This is basically a huge lookup table, which I could have copied from somewhere online, but I decided to rather use
this library, because I don't think putting a huge file with just one table into this project is more interesting
than using this library.

### gzip and zlib

These libraries are only used for compressing the HTTP body in responses and possibly uncompressing incoming bodies,
if the browser supports this. It would just not have made sense to write these myself, because of the few places
where these libraries were used.

### ssl

I actually was sooo close to writing an ssl implementation myself just for this project, but to be honest, two weeks
are just not enough for this. Using the SSL library was the next best approach to HTTPS, because I already had a HTTP
handler which I could just reuse.

Because of the restrictions of no external libraries, I had to fallback to the `openssl` command line utility for
generating the private key and certificate. This might actually be considered an external library itself, but I don't
really, just because it comes with the standard system utilities on most Linux systems and with GIT on Windows.
