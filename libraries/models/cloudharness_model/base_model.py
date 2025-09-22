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


def _convert_to_attrdict(value):
    """Helper function to convert nested structures to AttrDict"""
    if isinstance(value, dict) and not isinstance(value, AttrDict):
        return AttrDict(value)
    elif isinstance(value, list):
        # Convert list items that are dictionaries to AttrDict
        return [_convert_to_attrdict(item) for item in value]
    return value


def _get_value_from_additional_properties(obj, key):
    """Helper function to get value from additional_properties without triggering __getattr__ recursion"""
    # Use object.__getattribute__ to directly access additional_properties without triggering our override
    try:
        additional_properties = object.__getattribute__(obj, 'additional_properties')
        if key in additional_properties:
            value = additional_properties[key]
            return _convert_to_attrdict(value)
    except AttributeError:
        # Object doesn't have additional_properties
        pass
    return None


def _try_camelcase_conversions(obj, key, check_attributes=False):
    """Helper function to try camelCase/snake_case conversions"""
    try:
        import humps
    except ImportError:
        # Fallback to simple conversion if humps is not available
        def decamelize(name):
            s1 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
            return s1.lower()
        
        def camelize(name):
            components = name.split('_')
            return components[0] + ''.join(word.capitalize() for word in components[1:])
        
        humps = type('MockHumps', (), {'decamelize': decamelize, 'camelize': camelize})()
    
    # Try snake_case version of the key
    snake_case_key = humps.decamelize(key)
    if snake_case_key != key:
        # Check additional_properties
        value = _get_value_from_additional_properties(obj, snake_case_key)
        if value is not None:
            return value
        # Check attributes if requested
        if check_attributes:
            try:
                return object.__getattribute__(obj, snake_case_key)
            except AttributeError:
                pass
    
    # Try camelCase version of the key
    camel_case_key = humps.camelize(key)
    if camel_case_key != key:
        # Check additional_properties
        value = _get_value_from_additional_properties(obj, camel_case_key)
        if value is not None:
            return value
        # Check attributes if requested
        if check_attributes:
            try:
                return object.__getattribute__(obj, camel_case_key)
            except AttributeError:
                pass
    
    return None


def _check_field_aliases(obj, key):
    """Helper function to check if key is an alias for a field"""
    # Check pydantic v2
    try:
        model_fields = object.__getattribute__(obj, 'model_fields')
        for field_name, field_info in model_fields.items():
            if hasattr(field_info, 'alias') and field_info.alias == key:
                return object.__getattribute__(obj, field_name)
    except AttributeError:
        pass
    
    return None


class AttrDict(dict):
    """Dictionary that supports attribute access and nested AttrDict conversion"""
    def __getattr__(self, key):
        try:
            value = self[key]
            # Recursively convert nested dictionaries to AttrDict
            value = _convert_to_attrdict(value)
            self[key] = value  # Cache the converted value
            return value
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")
    
    def __setattr__(self, key, value):
        self[key] = value
    
    def __getitem__(self, key):
        value = super().__getitem__(key)
        # Recursively convert nested dictionaries to AttrDict for item access too
        value = _convert_to_attrdict(value)
        self[key] = value  # Cache the converted value
        return value
    
    def __contains__(self, key):
        """Support for 'in' operator with dot notation"""
        if "." in key:
            keys = key.split(".", 1)
            if super().__contains__(keys[0]):
                nested = self[keys[0]]
                if hasattr(nested, '__contains__'):
                    return keys[1] in nested
            return False
        return super().__contains__(key)


class CloudHarnessBaseModel(BaseModel):
    """
    Enhanced Pydantic BaseModel for CloudHarness with backward compatibility features.
    
    This class provides:
    - Automatic conversion of dict fields to AttrDict for dot-notation access
    - Access to additional_properties through attribute and item notation
    - CamelCase/snake_case field name conversion
    - Dictionary-like interface methods (get, keys, etc.)
    - Field name to alias conversion during initialization
    """
    
    def __init__(self, **data):
        """Enhanced initialization that handles field name to alias conversion."""
        # Convert field names to aliases if needed
        converted_data = {}
        
        # Get field information
        model_fields = getattr(self.__class__, 'model_fields', {})
        
        for key, value in data.items():
            # Check if this key matches a field name that has an alias
            found_alias = False
            for field_name, field_info in model_fields.items():
                if key == field_name and hasattr(field_info, 'alias') and field_info.alias:
                    # Use the alias instead of the field name
                    converted_data[field_info.alias] = value
                    found_alias = True
                    break
            
            if not found_alias:
                # Use the original key
                converted_data[key] = value
        
        super().__init__(**converted_data)
    
class CloudHarnessBaseModel(BaseModel):
    """
    Enhanced Pydantic BaseModel for CloudHarness with backward compatibility features.
    
    This class provides enhanced functionality through inheritance:
    - Automatic conversion of dict fields to AttrDict for dot-notation access
    - Access to additional_properties through attribute and item notation
    - CamelCase/snake_case field name conversion
    - Dictionary-like interface methods (get, keys, etc.)
    - Field name to alias conversion during initialization
    - Item assignment support
    """
    
    def __init__(self, **data):
        """Enhanced initialization that handles field name to alias conversion."""
        # Convert field names to aliases if needed
        converted_data = {}
        
        # Get field information
        model_fields = getattr(self.__class__, 'model_fields', {})
        
        for key, value in data.items():
            # Check if this key matches a field name that has an alias
            found_alias = False
            for field_name, field_info in model_fields.items():
                if key == field_name and hasattr(field_info, 'alias') and field_info.alias:
                    # Use the alias instead of the field name
                    converted_data[field_info.alias] = value
                    found_alias = True
                    break
            
            if not found_alias:
                # Use the original key
                converted_data[key] = value
        
        super().__init__(**converted_data)

    def __getattribute__(self, name: str) -> Any:
        """Enhanced attribute access with minimal interference for proper property handling."""
        # Get the attribute using the original __getattribute__
        value = object.__getattribute__(self, name)
        
        # Special handling for additional_properties - don't convert to AttrDict
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
                return _convert_to_attrdict(value)
        except AttributeError:
            pass
        
        # Return other attributes unchanged
        return value

    def __getitem__(self, key: str) -> Any:
        """Enhanced dictionary-style access with support for additional_properties and dot notation."""
        # Handle dot notation for nested access
        if "." in key:
            keys = key.split(".", 1)  # Split only on first dot
            try:
                # Try to get the first part as an attribute
                first_part = getattr(self, keys[0])
            except AttributeError:
                # If not found as attribute, try additional_properties
                first_part = _get_value_from_additional_properties(self, keys[0])
                if first_part is None:
                    raise KeyError(key)
            
            # Recursively access the remaining part
            if hasattr(first_part, '__getitem__'):
                return first_part[keys[1]]
            else:
                raise KeyError(key)
        
        # Non-dot notation access
        # First check additional_properties (for keys like 'task-images' that aren't valid Python attributes)
        value = _get_value_from_additional_properties(self, key)
        if value is not None:
            return value
        
        # Then check if key is an alias for a field
        value = _check_field_aliases(self, key)
        if value is not None:
            return value
        
        # Try camelCase conversions
        value = _try_camelcase_conversions(self, key, check_attributes=False)
        if value is not None:
            return value
        
        # Then try getattr for regular attributes
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def __getattr__(self, name: str) -> Any:
        """Enhanced attribute access to check additional_properties when an attribute is not found."""
        # Check if the attribute exists in additional_properties first
        value = _get_value_from_additional_properties(self, name)
        if value is not None:
            return value
        
        # Try camelCase conversions for additional_properties only (not attributes to avoid recursion)
        try:
            import humps
        except ImportError:
            # Fallback to simple conversion if humps is not available
            def decamelize(name):
                import re
                s1 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
                return s1.lower()
            
            def camelize(name):
                components = name.split('_')
                return components[0] + ''.join(word.capitalize() for word in components[1:])
            
            humps = type('MockHumps', (), {'decamelize': decamelize, 'camelize': camelize})()
        
        snake_case_name = humps.decamelize(name)
        if snake_case_name != name:
            value = _get_value_from_additional_properties(self, snake_case_name)
            if value is not None:
                return value
        
        camel_case_name = humps.camelize(name)
        if camel_case_name != name:
            value = _get_value_from_additional_properties(self, camel_case_name)
            if value is not None:
                return value
        
        # If not found, raise AttributeError as expected
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setitem__(self, key: str, value):
        """Support item assignment with additional_properties and field aliases."""
        # Check if key is an alias for a field
        if hasattr(self, 'model_fields'):
            for field_name, field_info in self.model_fields.items():
                if hasattr(field_info, 'alias') and field_info.alias == key:
                    setattr(self, field_name, value)
                    return
        
        # Check if key is a defined pydantic field (not just any attribute)
        if hasattr(self, 'model_fields') and key in self.model_fields:
            setattr(self, key, value)
            return
        
        # Try camelCase conversions for defined fields only
        try:
            import humps
        except ImportError:
            # Fallback to simple conversion if humps is not available
            def decamelize(name):
                import re
                s1 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
                return s1.lower()
            
            def camelize(name):
                components = name.split('_')
                return components[0] + ''.join(word.capitalize() for word in components[1:])
            
            humps = type('MockHumps', (), {'decamelize': decamelize, 'camelize': camelize})()
        
        snake_case_key = humps.decamelize(key)
        if hasattr(self, 'model_fields') and snake_case_key in self.model_fields:
            setattr(self, snake_case_key, value)
            return
        
        camel_case_key = humps.camelize(key)
        if hasattr(self, 'model_fields') and camel_case_key in self.model_fields:
            setattr(self, camel_case_key, value)
            return
        
        # For any key that doesn't match a defined field, always use additional_properties
        # This prevents validation errors on non-existent fields
        if not hasattr(self, 'additional_properties'):
            self.additional_properties = {}
        self.additional_properties[key] = value

    def __setattr__(self, name: str, value):
        """Handle camelCase attributes and prevent validation errors on non-existent fields."""
        # First check if this is a property - if so, use the standard mechanism
        try:
            cls_dict = object.__getattribute__(self.__class__, '__dict__')
            if name in cls_dict and isinstance(cls_dict[name], property):
                # This is a property, use the standard __setattr__ to trigger the setter
                object.__setattr__(self, name, value)
                return
        except (AttributeError, TypeError):
            pass
        
        # Handle private attributes (starting with _) - always set them directly
        if name.startswith('_'):
            object.__setattr__(self, name, value)
            return
        
        # Check if name is a defined pydantic field
        if hasattr(self, 'model_fields') and name in self.model_fields:
            # Use the original __setattr__ for defined fields
            super(BaseModel, self).__setattr__(name, value)
            return
        
        # Check if name is camelCase version of a defined field
        try:
            import humps
        except ImportError:
            # Fallback to simple conversion if humps is not available
            def decamelize(name):
                import re
                s1 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
                return s1.lower()
            
            humps = type('MockHumps', (), {'decamelize': decamelize})()
        
        snake_case_name = humps.decamelize(name)
        if hasattr(self, 'model_fields') and snake_case_name in self.model_fields:
            super(BaseModel, self).__setattr__(snake_case_name, value)
            return
        
        # For non-field attributes, store in additional_properties to avoid validation errors
        if not hasattr(self, 'additional_properties'):
            object.__setattr__(self, 'additional_properties', {})
        
        # If additional_properties already exists, update it
        if hasattr(self, 'additional_properties'):
            self.additional_properties[name] = value
        else:
            # Fallback to object.__setattr__ for internal attributes
            object.__setattr__(self, name, value)

    def get(self, key: str, default=None):
        """Dictionary-like get method with support for additional_properties and dot notation."""
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key: str) -> bool:
        """Support 'in' operator with additional_properties and dot notation."""
        # Handle dot notation for nested access
        if "." in key:
            keys = key.split(".", 1)  # Split only on first dot
            try:
                # Try to get the first part as an attribute
                first_part = getattr(self, keys[0])
            except AttributeError:
                # If not found as attribute, try additional_properties
                first_part = _get_value_from_additional_properties(self, keys[0])
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
        return _convert_to_attrdict(result)
