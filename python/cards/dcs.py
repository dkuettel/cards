# TODO where to put these notes? commit and then remove?
# or/and where to keep the other interesting modules for python to find another day

""" trying out some dataclasses and related libraries

candidates
    https://yukinarit.github.io/pyserde/guide/getting-started.html
        seems like the motivation for our conde, and also motivated by rust?
        looks to cover everything, and works on types, not just dataclasses, including unions
        unions with different tagging
        overall looks clean, works with dataclasses
        pyright gets it? seems like
        has (experimental) type checking, only at (de)serialization, as we want

unfavored
    https://docs.pydantic.dev/usage/settings/
        more specific for data validation and settings management
        doesnt seem to work with plain dataclasses :/
        but has a dataclasses drop-in replacement
    https://github.com/beartype/beartype
        runtime type checking for functions
        might eventually be used for validation in serde
    https://www.attrs.org/en/stable/overview.html
        "better" python dataclasses, could be interesting some day
        does it work with pylint?
        looks okay but not really necessary for us right now?
        validation for values, not necessarily types
        best-case we only validated on loading, rest is pyright "statically"
    https://github.com/python-attrs/cattrs
        for attrs, but also for dataclasses
        structure and unstructure
        supports unions, but not tagging options, only if unique fields
    https://github.com/Fatal1ty/mashumaro
        looks very similar to sede
        dump and load
        apparently fast
        supports a huge list of types, including Union
        works on plain dataclasses
        not sure if I can load into non-dataclass types
        documentation seems lacking a bit compared to sede

disqualified
    https://github.com/madman-bob/python-dataclasses-serialization
        not enough features
    https://marshmallow.readthedocs.io/en/stable/quickstart.html
        requires building schemas, more appropriate for pure validation
        doesnt seem to build schemas from plain dataclasses
        a bit too disconnected from dataclasses, verbose then
    https://github.com/konradhalas/dacite
        only loads into dataclasses, not any types
        has unions, but not different types of tagging
        checks types when loading

"""

from dataclasses import dataclass
from typing import Literal, Optional, Union

from serde import field, serde
from serde.core import Strict, Untagged
from serde.toml import from_toml, to_toml

none_field = lambda: field(default=None, skip_if_default=True)


# NOTE @serde(type_check=Strict) is still experimental, it doesnt always fail when it should

# TODO can we use another validator independent of this? marshmallow validate from a direct dataclass schema?
# or also just something that one-shot validates a dataclass recursively? seems easy enough

# TODO make sure to not leak serde out of the mochi_toml module, so we can easily change or improve things
# the small interface is that it load and writes, and validates, those toml config files, independent module
# or split the card meta info and the mochi-specific info? a bit harder then to change the card type, right?
# but splitting would mean we dont need a round-trip, and nothing gets reformatted, comments stay, and so on

# TODO I always run into this basic problem:
# I dont want to make a UI, but just declarative text files
# but then how to know when things changed, somehow things have to be simple states, easy to match?
# I guess the main thing is that we have to match it up with what's on mochi's server side
# the other option is CLI for mutations, instead of me editing files myself?
# auto-discover is nicer somehow of course, but harder

# TODO draft
# a folder per item
#   meta.toml to define how that content translates to one or more cards
#       this file is only user edited, no round-trip
#       this is the only input we validate
#   content.md usually, but in theory depends on meta.toml::cards.scheme
#   mochi.json to hold data specific to sync with mochi (could be something else one day)
#       this file is only generated, no manual edits, make it a dot file?
#       all the things that need to move _with_ the card, in the same folder
#       there is probably yet another global cache.json to know what we think is mochi's state


@serde(type_check=Strict)
@dataclass(frozen=True)
class Plain:
    kind: Literal["plain"]
    card_id: Optional[str] = none_field()

    @classmethod
    def new(cls):
        return cls("plain", None)


@serde(type_check=Strict)
@dataclass(frozen=True)
class Both:
    kind: Literal["both"]
    forward_id: Optional[str] = none_field()
    backward_id: Optional[str] = none_field()


@serde(type_check=Strict)
@dataclass(frozen=True)
class Vocab:
    kind: Literal["vocab"]
    langs: tuple[str, str]
    forward_id: Optional[str] = none_field()
    backward_id: Optional[str] = none_field()


@serde(type_check=Strict, tagging=Untagged)
@dataclass(frozen=True)
class Mochi:
    card: Union[Plain, Both, Vocab] = field(default_factory=Plain.new)


m = Mochi()
print(to_toml(m))


print(
    from_toml(
        Mochi,
        """
[card]
kind = "both"
""",
    )
)
