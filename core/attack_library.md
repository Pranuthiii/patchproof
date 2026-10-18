Reference: common attack variants by vulnerability class. This is general security knowledge, not specific to any one program. Identify which class applies and include a payload for each variant that could apply.

SQL injection (values and identifiers)
- Tautologies using single quotes, double quotes and backslashes; comment terminators (--, #, /* */); UNION SELECT; stacked statements with ;
- Injection into identifiers (column, table, ORDER BY, GROUP BY): function calls, subqueries in parentheses, comma-separated extra terms, CASE expressions
- Numeric contexts with no quotes; case, whitespace and encoding variations; LIKE wildcards (%, _)

Path traversal and file access
- ../ and ..\ sequences, deeper chains, absolute paths, mixed separators
- A sibling directory whose name starts with the allowed directory's name (prefix-check bypass)
- URL-encoded and double-encoded sequences, null bytes, trailing dots or spaces, unicode look-alikes
- Symlinks; paths that normalise to the base directory itself or to its parent

OS command injection
- Separators ; && || | and newline; backticks and $( ) substitution; redirects
- Argument injection: values starting with - that are read as options
- Shell glob characters, variable expansion, quote-breaking, whitespace tricks

Code execution through eval or unsafe parsing
- Attribute chains that reach builtins or imports through an object's class hierarchy
- __import__, getattr chains, lambdas and comprehensions that call functions, string-format tricks
- Unsafe deserialisation formats (pickle, unsafe YAML tags)

HTML and script injection in output
- Quotes (single and double) that break out of an attribute; angle brackets; closing tags; event-handler attributes
- javascript: and data: URL schemes, including mixed case, leading whitespace and control characters
- Entity-encoded variants, unquoted attributes, script and style contexts

URL validation (open redirect, server-side request forgery)
- Protocol-relative URLs, extra leading slashes, backslash variants
- Credentials before an at-sign; the allowed host as a prefix, suffix or subdomain of an attacker host
- A scheme with missing slashes; tabs, newlines or control characters inside the URL; case differences; ports; a trailing dot on the host
- IP address forms (decimal, hex, octal, IPv6), localhost, link-local and cloud-metadata addresses
- Differences between how a validator parses a URL and how a browser or HTTP client does
