# coding: utf-8
"""
CloudHarness Base Model

A custom Pydantic BaseModel subclass that provides enhanced functionality for
CloudHarness generated models, replacing the previous monkey patching approach.
"""

from __future__ import annotations
import re
from typing import Any, Dict, List, Union
from pydantic import BaseModel


class AttrDict(dict):
    """Dictionary that supports attribute-style access."""
    
    def __getattr__(self, key: str) -> Any:
        try:
            value = self[key]
            # Recursively convert nested dictionaries to AttrDict
            if isinstance(value, dict) and not isinstance(value, AttrDict):
                value = AttrDict(value)
                self[key] = value  # Cache the converted value
            elif isinstance(value, list):
                # Convert list items that are dictionaries to AttrDict
                value = [AttrDict(item) if isinstance(item, dict) and not isinstance(item, AttrDict) else item for item in value]
                self[key] = value  # Cache the converted value
            return value
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")
    
    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value
    
    def __getitem__(self, key: str) -> Any:
        value = super().__getitem__(key)
        # Recursively convert nested dictionaries to AttrDict for item access too
        if isinstance(value, dict) and not isinstance(value, AttrDict):
            value = AttrDict(value)
            self[key] = value  # Cache the converted value
        elif isinstance(value, list):
            # Convert list items that are dictionaries to AttrDict
            value = [AttrDict(item) if isinstance(item, dict) and not isinstance(item, AttrDict) else item for item in value]
            self[key] = value  # Cache the converted value
        return value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get method with default value, similar to regular dict."""
        try:
            return self[key]
        except KeyError:
            return default


class CloudHarnessBaseModel(BaseModel):
    """
    Enhanced Pydantic BaseModel for CloudHarness with backward compatibility features.
    
    This class provides:
    - Automatic conversion of dict fields to AttrDict for dot-notation access
    - Access to additional_properties through attribute and item notation
    - CamelCase/snake_case field name conversion
    - Dictionary-like interface methods (get, keys, etc.)
    """
    
    def _camel_to_snake(self, name: str) -> str:
        """Convert camelCase to snake_case."""
        s1 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
        return s1.lower()
    
    def _snake_to_camel(self, name: str) -> str:
        """Convert snake_case to camelCase."""
        components = name.split('_')
        return components[0] + ''.join(word.capitalize() for word in components[1:])

    @staticmethod
    def _convert_to_attr_dict_static(value):
        """Static method to convert nested structures to AttrDict."""
        if isinstance(value, dict) and not isinstance(value, AttrDict):
            return AttrDict(value)
        elif isinstance(value, list):
            # Convert list items that are dictionaries to AttrDict
            return [CloudHarnessBaseModel._convert_to_attr_dict_static(item) for item in value]
        return value

    def _get_value_from_additional_properties(self, key: str):
        """Helper function to get value from additional_properties without triggering __getattr__ recursion"""
        # Use object.__getattribute__ to directly access additional_properties without triggering our override
        try:
            additional_properties = object.__getattribute__(self, 'additional_properties')
            if key in additional_properties:
                value = additional_properties[key]
                return self._convert_to_attr_dict_static(value)
        except AttributeError:
            # Object doesn't have additional_properties
            pass
        return None

    def __getattribute__(self, name: str) -> Any:
        """Enhanced attribute access with AttrDict conversion, preserving original pydantic_utils logic."""
        # Get the attribute using the original __getattribute__
        value = object.__getattribute__(self, name)
        
        # Special handling for additional_properties - don't convert to AttrDict on direct access
        if name == 'additional_properties':
            return value
        
        # Check if this is a property - avoid recursion by directly accessing type's __dict__
        cls = type(self)
        if hasattr(cls, '__dict__') and name in cls.__dict__ and isinstance(cls.__dict__[name], property):
            # This is a property, don't convert its return value
            return value
        
        # For pydantic model fields containing dicts, convert to AttrDict for better access
        try:
            model_fields = object.__getattribute__(self, 'model_fields')
            if name in model_fields:
                return self._convert_to_attr_dict_static(value)
        except AttributeError:
            pass
        
        # Return other attributes unchanged
        return value

    def __getitem__(self, key: str) -> Any:
        """Enhanced dictionary-style access with support for additional_properties and dot notation, preserving original pydantic_utils logic."""
        # Handle dot notation for nested access
        if "." in key:
            keys = key.split(".", 1)  # Split only on first dot
            try:
                # Try to get the first part as an attribute
                first_part = getattr(self, keys[0])
            except AttributeError:
                # If not found as attribute, try additional_properties
                first_part = self._get_value_from_additional_properties(keys[0])
                if first_part is None:
                    raise KeyError(key)
            
            # Recursively access the remaining part
            if hasattr(first_part, '__getitem__'):
                return first_part[keys[1]]
            else:
                raise KeyError(key)
        
        # Non-dot notation access
        # First check additional_properties (for keys like 'task-images' that aren't valid Python attributes)
        value = self._get_value_from_additional_properties(key)
        if value is not None:
            return value
        
        # Try camelCase conversions
        snake_case_key = self._camel_to_snake(key)
        if snake_case_key != key:
            value = self._get_value_from_additional_properties(snake_case_key)
            if value is not None:
                return value
        
        camel_case_key = self._snake_to_camel(key)
        if camel_case_key != key:
            value = self._get_value_from_additional_properties(camel_case_key)
            if value is not None:
                return value
        
        # Then try getattr for regular attributes
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def __getattr__(self, name: str) -> Any:
        """Enhanced attribute access with camelCase/snake_case conversion, preserving original pydantic_utils logic."""
        # Avoid infinite recursion for special attributes
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

        # Check if the attribute exists in additional_properties first
        value = self._get_value_from_additional_properties(name)
        if value is not None:
            return value

        # Try camelCase conversions for additional_properties only (not attributes to avoid recursion)
        snake_case_name = self._camel_to_snake(name)
        if snake_case_name != name:
            value = self._get_value_from_additional_properties(snake_case_name)
            if value is not None:
                return value

        camel_case_name = self._snake_to_camel(name)
        if camel_case_name != name:
            value = self._get_value_from_additional_properties(camel_case_name)
            if value is not None:
                return value

        # Check extra fields
        if hasattr(self, '__pydantic_extra__') and name in self.__pydantic_extra__:
            value = self.__pydantic_extra__[name]
            # Convert dict to AttrDict on access for backward compatibility
            if isinstance(value, dict) and not isinstance(value, AttrDict):
                return self._convert_to_attr_dict_static(value)
            return value

        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a field value with optional default, similar to dict.get()."""
        try:
            return self[key]
        except KeyError:
            return default
    
    def keys(self):
        """Return keys of all fields and additional properties."""
        keys = set(self.model_fields.keys())
        if hasattr(self, 'additional_properties'):
            keys.update(self.additional_properties.keys())
        if hasattr(self, '__pydantic_extra__'):
            keys.update(self.__pydantic_extra__.keys())
        return keys
    
    def values(self):
        """Return values of all fields and additional properties."""
        return [self[key] for key in self.keys()]
    
    def items(self):
        """Return items of all fields and additional properties."""
        return [(key, self[key]) for key in self.keys()]
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in model fields or additional properties."""
        # Handle dot notation for nested access
        if "." in key:
            keys = key.split(".", 1)  # Split only on first dot
            try:
                # Try to get the first part as an attribute
                first_part = getattr(self, keys[0])
            except AttributeError:
                # If not found as attribute, try additional_properties
                first_part = self._get_value_from_additional_properties(keys[0])
                if first_part is None:
                    return False
            
            # Check if the remaining part exists in the nested object
            if hasattr(first_part, '__contains__'):
                return keys[1] in first_part
            else:
                return False
        
        # Non-dot notation access
        # First check if it's a defined field in the model
        if hasattr(self, 'model_fields') and key in self.model_fields:
            return True
        
        # Check if it's a regular attribute
        if hasattr(self, key):
            return True
        
        # Check additional_properties
        if hasattr(self, 'additional_properties') and key in self.additional_properties:
            return True
        
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Enhanced to_dict that converts nested models to AttrDict for backward compatibility."""
        result = super().model_dump(by_alias=True, exclude_none=True)
        return self._convert_to_attr_dict_static(result)
