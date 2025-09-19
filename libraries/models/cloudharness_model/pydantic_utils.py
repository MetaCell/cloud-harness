"""
Pydantic utility functions and monkey patches to improve object access with legacy support.

This module provides enhancements to Pydantic BaseModel to support:
- Access to additional_properties through __getitem__ and __getattr__
- Dot notation for nested property access
- Dictionary-like get() method with default values
"""

import pydantic


def _convert_to_attrdict(value):
    """Helper function to convert nested structures to AttrDict"""
    if isinstance(value, dict) and not isinstance(value, AttrDict):
        return AttrDict(value)
    elif isinstance(value, list):
        # Convert list items that are dictionaries to AttrDict
        return [_convert_to_attrdict(item) for item in value]
    return value


def _get_value_from_additional_properties(obj, key):
    """Helper function to get value from additional_properties with AttrDict conversion"""
    if hasattr(obj, 'additional_properties') and key in obj.additional_properties:
        value = obj.additional_properties[key]
        return _convert_to_attrdict(value)
    return None


def _try_camelcase_conversions(obj, key, check_attributes=False):
    """Helper function to try camelCase/snake_case conversions"""
    import humps
    
    # Try snake_case version of the key
    snake_case_key = humps.decamelize(key)
    if snake_case_key != key:
        # Check additional_properties
        value = _get_value_from_additional_properties(obj, snake_case_key)
        if value is not None:
            return value
        # Check attributes if requested
        if check_attributes and hasattr(obj, snake_case_key):
            return getattr(obj, snake_case_key)
    
    # Try camelCase version of the key
    camel_case_key = humps.camelize(key)
    if camel_case_key != key:
        # Check additional_properties
        value = _get_value_from_additional_properties(obj, camel_case_key)
        if value is not None:
            return value
        # Check attributes if requested
        if check_attributes and hasattr(obj, camel_case_key):
            return getattr(obj, camel_case_key)
    
    return None


def _check_field_aliases(obj, key):
    """Helper function to check if key is an alias for a field"""
    # Check pydantic v2
    if hasattr(obj, 'model_fields'):
        for field_name, field_info in obj.model_fields.items():
            if hasattr(field_info, 'alias') and field_info.alias == key:
                return getattr(obj, field_name)
    
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


def _pydantic_getitem_override(self, key: str):
    """
    Override for pydantic.BaseModel.__getitem__ to check additional_properties
    when a field is not found with getattr. Supports dot notation for nested access.
    """
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


def _pydantic_getattribute_override(self, name: str):
    """
    Override for pydantic.BaseModel.__getattribute__ to convert dict values to AttrDict
    """
    # Get the attribute using the original __getattribute__
    try:
        value = object.__getattribute__(self, name)
        # Don't convert additional_properties to AttrDict to avoid breaking assignment
        if name == 'additional_properties':
            return value
        # Convert other dict values to AttrDict for better access
        return _convert_to_attrdict(value)
    except AttributeError:
        # Fall back to the custom __getattr__ logic
        return _pydantic_getattr_override(self, name)


def _pydantic_getattr_override(self, name: str):
    """
    Override for pydantic.BaseModel.__getattr__ to check additional_properties
    when an attribute is not found through normal means.
    """
    # Check if the attribute exists in additional_properties first
    value = _get_value_from_additional_properties(self, name)
    if value is not None:
        return value
    
    # Try camelCase conversions for additional_properties only (not attributes to avoid recursion)
    import humps
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


def _pydantic_get_override(self, key: str, default=None):
    """
    Override for pydantic.BaseModel.get to provide dictionary-like interface
    with support for additional_properties and dot notation.
    """
    try:
        return self[key]
    except KeyError:
        return default


def _pydantic_setitem_override(self, key: str, value):
    """
    Override for pydantic.BaseModel.__setitem__ to support item assignment
    with additional_properties and field aliases.
    """
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
    import humps
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


def _pydantic_contains_override(self, key: str):
    """
    Override for pydantic.BaseModel.__contains__ to support 'in' operator
    with additional_properties and dot notation.
    """
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


def _pydantic_setattr_override(self, name: str, value):
    """
    Override for pydantic.BaseModel.__setattr__ to handle camelCase attributes
    and prevent validation errors on non-existent fields.
    """
    # Check if name is a defined pydantic field
    if hasattr(self, 'model_fields') and name in self.model_fields:
        # Use the original __setattr__ for defined fields
        super(pydantic.BaseModel, self).__setattr__(name, value)
        return
    
    # Check if name is camelCase version of a defined field
    import humps
    snake_case_name = humps.decamelize(name)
    if hasattr(self, 'model_fields') and snake_case_name in self.model_fields:
        super(pydantic.BaseModel, self).__setattr__(snake_case_name, value)
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


def apply_pydantic_patches():
    """
    Apply monkey patches to pydantic.BaseModel to enhance functionality.
    
    This function should be called once during module initialization to enable:
    - Enhanced __getattribute__ to convert dict values to AttrDict
    - Enhanced __getitem__ with additional_properties support and dot notation
    - Enhanced __getattr__ with additional_properties support  
    - Enhanced __setitem__ for item assignment support
    - Enhanced __setattr__ for attribute assignment support
    - Dictionary-like get() method with default values
    - Enhanced __contains__ for 'in' operator support with additional_properties
    """
    pydantic.BaseModel.__getattribute__ = _pydantic_getattribute_override
    pydantic.BaseModel.__getitem__ = _pydantic_getitem_override
    pydantic.BaseModel.__getattr__ = _pydantic_getattr_override
    pydantic.BaseModel.__setitem__ = _pydantic_setitem_override
    pydantic.BaseModel.__setattr__ = _pydantic_setattr_override
    pydantic.BaseModel.get = _pydantic_get_override
    pydantic.BaseModel.__contains__ = _pydantic_contains_override
