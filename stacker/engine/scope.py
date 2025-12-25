"""
Variable scope implementation using parent chain for efficient lookups.

This module provides a scope chain mechanism to avoid deep copying of variables
during function calls, significantly improving performance while maintaining
correct scoping semantics.
"""

from __future__ import annotations
from typing import Any, Iterator


class ScopedVariables:
    """
    Variable scope with parent chain for efficient variable lookup.

    This class implements lexical scoping using a parent chain, similar to
    how JavaScript, Python, and many other languages handle variable scopes.

    When a variable is accessed:
    1. Check local scope first
    2. If not found, check parent scope
    3. Continue up the chain until found or reach root

    When a variable is set:
    1. Always set in the local scope only

    This avoids the need for deep copying entire variable dictionaries.
    """

    def __init__(
        self, parent: ScopedVariables | None = None, local_vars: dict | None = None
    ):
        """
        Initialize a new scope.

        Args:
            parent: Parent scope (None for root scope)
            local_vars: Initial local variables (default: empty dict)
        """
        self._local: dict[str, Any] = local_vars if local_vars is not None else {}
        self._parent: ScopedVariables | None = parent

    def __getitem__(self, key: str) -> Any:
        """
        Get a variable value, searching up the scope chain.

        Args:
            key: Variable name

        Returns:
            Variable value

        Raises:
            KeyError: If variable is not found in any scope
        """
        if key in self._local:
            return self._local[key]
        elif self._parent is not None:
            return self._parent[key]
        else:
            raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Set a variable in the current scope only.

        Args:
            key: Variable name
            value: Variable value
        """
        self._local[key] = value

    def set_global(self, key: str, value: Any) -> None:
        """
        Set a variable in the global (root) scope.

        Traverses up to the root scope and sets the variable there.

        Args:
            key: Variable name
            value: Variable value
        """
        if self._parent is None:
            # We are at the root (global) scope
            self._local[key] = value
        else:
            # Recurse up to the root
            self._parent.set_global(key, value)

    def update_existing(self, key: str, value: Any) -> bool:
        """
        Update an existing variable by searching up the scope chain.

        If the variable exists in any scope, update it there.
        If it doesn't exist anywhere, do nothing and return False.

        Args:
            key: Variable name
            value: Variable value

        Returns:
            True if variable was found and updated, False otherwise
        """
        if key in self._local:
            # Found in local scope, update it
            self._local[key] = value
            return True
        elif self._parent is not None:
            # Recurse to parent scope
            return self._parent.update_existing(key, value)
        else:
            # Not found anywhere
            return False

    def __delitem__(self, key: str) -> None:
        """
        Delete a variable from the current scope only.

        Args:
            key: Variable name

        Raises:
            KeyError: If variable is not in local scope
        """
        del self._local[key]

    def __contains__(self, key: str) -> bool:
        """
        Check if a variable exists, searching up the scope chain.

        Args:
            key: Variable name

        Returns:
            True if variable exists in any scope
        """
        return key in self._local or (self._parent is not None and key in self._parent)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a variable value with a default, searching up the scope chain.

        Args:
            key: Variable name
            default: Default value if not found

        Returns:
            Variable value or default
        """
        try:
            return self[key]
        except KeyError:
            return default

    def pop(self, key: str, default: Any = None) -> Any:
        """
        Remove and return a variable from the local scope only.

        Args:
            key: Variable name
            default: Default value if not found

        Returns:
            Variable value or default
        """
        return self._local.pop(key, default)

    def keys(self) -> Iterator[str]:
        """
        Get all variable names from all scopes.

        Yields:
            Variable names
        """
        # Yield local keys first
        yield from self._local.keys()
        # Then parent keys (avoiding duplicates)
        if self._parent is not None:
            for key in self._parent.keys():
                if key not in self._local:
                    yield key

    def items(self) -> Iterator[tuple[str, Any]]:
        """
        Get all variable name-value pairs from all scopes.

        Yields:
            (name, value) tuples
        """
        # Yield local items first
        yield from self._local.items()
        # Then parent items (avoiding duplicates)
        if self._parent is not None:
            for key, value in self._parent.items():
                if key not in self._local:
                    yield key, value

    def update(self, other: dict) -> None:
        """
        Update local scope with variables from a dict.

        Args:
            other: Dictionary of variables to add
        """
        self._local.update(other)

    def __len__(self) -> int:
        """
        Get the total number of unique variables across all scopes.

        Returns:
            Number of unique variables
        """
        # Count unique keys across all scopes
        all_keys = set(self.keys())
        return len(all_keys)

    def create_child_scope(self) -> ScopedVariables:
        """
        Create a new child scope with this scope as parent.

        Returns:
            New child scope
        """
        return ScopedVariables(parent=self)

    def copy(self) -> ScopedVariables:
        """
        Create a shallow copy of this scope (local variables only).

        The copy will have the same parent as this scope.

        Returns:
            New scope with copied local variables
        """
        return ScopedVariables(parent=self._parent, local_vars=self._local.copy())

    def __repr__(self) -> str:
        """String representation for debugging."""
        local_vars = dict(self._local)
        has_parent = self._parent is not None
        return f"ScopedVariables(local={local_vars}, has_parent={has_parent})"
