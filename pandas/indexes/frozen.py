"""
frozen (immutable) data structures to support MultiIndexing

These are used for:

- .names (FrozenList)
- .levels & .labels (FrozenNDArray)

"""

import numpy as np
from pandas.core.base import PandasObject
from pandas.types.cast import _coerce_indexer_dtype
from pandas.formats.printing import pprint_thing

import warnings


class FrozenList(PandasObject, list):

    """
    Container that doesn't allow setting item *but*
    because it's technically non-hashable, will be used
    for lookups, appropriately, etc.
    """
    # Sidenote: This has to be of type list, otherwise it messes up PyTables
    #           typechecks

    def __add__(self, other):
        warnings.warn("__add__ is deprecated, use union(...)", FutureWarning)
        return self.union(other)

    def __iadd__(self, other):
        warnings.warn("__iadd__ is deprecated, use union(...)", FutureWarning)
        if isinstance(other, tuple):
            other = list(other)
        return super(FrozenList, self).__iadd__(other)

    # Python 2 compat
    def __getslice__(self, i, j):
        return self.__class__(super(FrozenList, self).__getslice__(i, j))

    def __getitem__(self, n):
        # Python 3 compat
        if isinstance(n, slice):
            return self.__class__(super(FrozenList, self).__getitem__(n))
        return super(FrozenList, self).__getitem__(n)

    def __radd__(self, other):
        if isinstance(other, tuple):
            other = list(other)
        return self.__class__(other + list(self))

    def __eq__(self, other):
        if isinstance(other, (tuple, FrozenList)):
            other = list(other)
        return super(FrozenList, self).__eq__(other)

    __req__ = __eq__

    def __mul__(self, other):
        return self.__class__(super(FrozenList, self).__mul__(other))

    __imul__ = __mul__

    def __reduce__(self):
        return self.__class__, (list(self),)

    def __hash__(self):
        return hash(tuple(self))

    def _disabled(self, *args, **kwargs):
        """This method will not function because object is immutable."""
        raise TypeError("'%s' does not support mutable operations." %
                        self.__class__.__name__)

    def __unicode__(self):
        return pprint_thing(self, quote_strings=True,
                            escape_chars=('\t', '\r', '\n'))

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__,
                           str(self))

    __setitem__ = __setslice__ = __delitem__ = __delslice__ = _disabled
    pop = append = extend = remove = sort = insert = _disabled

    def union(self, other):
        """Returns a FrozenList with other concatenated to the end of self"""
        if isinstance(other, tuple):
            other = list(other)
        return self.__class__(super(FrozenList, self).__add__(other))

    def difference(self, other):
        """Returns a FrozenList with the same elements as self, but with elements
        that are also in other removed."""
        other = set(other)
        temp = [x for x in self if x not in other]
        return self.__class__(temp)


class FrozenNDArray(PandasObject, np.ndarray):

    # no __array_finalize__ for now because no metadata
    def __new__(cls, data, dtype=None, copy=False):
        if copy is None:
            copy = not isinstance(data, FrozenNDArray)
        res = np.array(data, dtype=dtype, copy=copy).view(cls)
        return res

    def _disabled(self, *args, **kwargs):
        """This method will not function because object is immutable."""
        raise TypeError("'%s' does not support mutable operations." %
                        self.__class__)

    __setitem__ = __setslice__ = __delitem__ = __delslice__ = _disabled
    put = itemset = fill = _disabled

    def _shallow_copy(self):
        return self.view()

    def values(self):
        """returns *copy* of underlying array"""
        arr = self.view(np.ndarray).copy()
        return arr

    def __unicode__(self):
        """
        Return a string representation for this object.

        Invoked by unicode(df) in py2 only. Yields a Unicode String in both
        py2/py3.
        """
        prepr = pprint_thing(self, escape_chars=('\t', '\r', '\n'),
                             quote_strings=True)
        return "%s(%s, dtype='%s')" % (type(self).__name__, prepr, self.dtype)


def _ensure_frozen(array_like, categories, copy=False):
    array_like = _coerce_indexer_dtype(array_like, categories)
    array_like = array_like.view(FrozenNDArray)
    if copy:
        array_like = array_like.copy()
    return array_like
