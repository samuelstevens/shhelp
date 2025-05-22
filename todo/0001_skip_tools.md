# Skipping Tool Use

Here's an example of a situation where shgod thinks we should use a tool, but I don't want it to.

```text
[I] samstevens@localhoster ~/D/shgod (main) [1]> shgod whats the difference between os.environ.get and os.getenv in python
Next request: 1856 tok  $0.01
continue? [Y/n]:
Let me find out the difference between `os.environ.get` and `os.getenv` in Python.

* First, I'll look for these functions in Python's `os` module
* Need to search the codebase for references or usage patterns

Using ripgrep to search for relevant code:

ripgrep "os\.environ\.get|os\.getenv" .
Run tool ripgrep: rg os\.environ\.get|os\.getenv .? n
[I] samstevens@localhoster ~/D/shgod (main)>
```

Rather than exiting, I would rather give the user a chance to explain why you don't want to run that tool.
It probably makes sense to do the same thing for each tool call.
Then, we should send tool call messages and a new user message to the LLM.
Something like:

system
user
assistant
tool call (failed due to user deny)
tool call (success)
user (explain why they denied the tool call)

or 

system
user
assistant
tool call (failed due to user deny)
tool call (failed due to user deny)
user (explain why they denied tool call #1, explain why they denied tool call #2)

Then we can send these messages to the LLM.
