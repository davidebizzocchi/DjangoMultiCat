from django import forms
from pydantic import BaseModel, Field, ValidationError, create_model
from pydantic.fields import FieldInfo
from typing import Optional, Any, Union, get_origin, get_args, List, Dict, Type
from datetime import date, datetime
import inspect

from icecream import ic


class PydanticFormBuilder:
    """
    Advanced utility to create Django forms from Pydantic models with:
    - Dynamic form generation
    - JSON Schema support
    - List of forms creation
    - Comprehensive type handling
    """

    @classmethod
    def create_form(cls, pydantic_model: Type[BaseModel], **form_kwargs) -> Type[forms.Form]:
        """
        Creates a Django Form class from a Pydantic model
    
        Args:
            pydantic_model: The Pydantic model class
            form_kwargs: Additional form class attributes
        
        Returns:
            A Django Form class
        """
        class DynamicForm(forms.Form):
            pass
    
        for field_name, field_info in pydantic_model.model_fields.items():
            django_field = cls._create_django_field(field_name, field_info)
            DynamicForm.base_fields[field_name] = django_field
    
        DynamicForm.clean = cls._create_clean_method(pydantic_model)
        DynamicForm.to_pydantic = lambda self: pydantic_model(**self.cleaned_data)
    
        for attr, value in form_kwargs.items():
            setattr(DynamicForm, attr, value)
        
        return DynamicForm

    @classmethod
    def create_form_list(cls, pydantic_models: List[Type[BaseModel]], prefix: str = 'form') -> Dict[str, Type[forms.Form]]:
        """
        Creates multiple Django Forms from a list of Pydantic models
    
        Args:
            pydantic_models: List of Pydantic model classes
            prefix: Prefix for form names
        
        Returns:
            Dictionary of form classes with keys as f"{prefix}_{index}"
        """
        return {
            f"{prefix}_{i}": cls.create_form(model)
            for i, model in enumerate(pydantic_models)
        }

    @classmethod
    def create_form_from_schema(cls, schema: Dict[str, Any], model_name: str = "DynamicModel") -> Type[forms.Form]:
        """
        Creates a Django Form from a JSON schema
    
        Args:
            schema: JSON schema dictionary
            model_name: Name for the dynamically created Pydantic model
        
        Returns:
            A Django Form class
        """
        pydantic_model = create_model(model_name, **cls._schema_to_fields(schema))
        return cls.create_form(pydantic_model)

    @classmethod
    def generate_schema(cls, pydantic_model: Type[BaseModel]) -> Dict[str, Any]:
        """
        Generates JSON schema from a Pydantic model
    
        Args:
            pydantic_model: Pydantic model class
        
        Returns:
            JSON schema dictionary
        """
        return pydantic_model.schema()

    @staticmethod
    def _is_field_required(field_info: FieldInfo) -> bool:
        """Check if a field is required in Pydantic v2+"""
        return field_info.is_required()

    @staticmethod
    def _get_field_default(field_info: FieldInfo):
        """Get default value for a field in Pydantic v2+"""
        if PydanticFormBuilder._is_field_required(field_info):
            return None
        return field_info.default if field_info.default is not None else None

    @staticmethod
    def _create_django_field(field_name, field_info) -> forms.Field:
        """Creates a Django form field from Pydantic field definition (v2+)"""
    
        field_kwargs = {
            'required': PydanticFormBuilder._is_field_required(field_info),
            'label': getattr(field_info, 'title', field_name),
            'help_text': getattr(field_info, 'description', ''),
            'validators': [],
        }
    
        default = PydanticFormBuilder._get_field_default(field_info)
        if default is not None:
            field_kwargs['initial'] = default
    
        field_type = field_info.annotation
        origin_type = get_origin(field_type) or field_type
    
        # Handle Optional/Union types
        if origin_type is Optional or (hasattr(origin_type, '__origin__') and origin_type.__origin__ is Union):
            args = get_args(field_type)
            if type(None) in args:
                field_kwargs['required'] = False
                non_none_types = [t for t in args if t is not type(None)]
                if non_none_types:
                    field_type = non_none_types[0] if len(non_none_types) == 1 else Union[tuple(non_none_types)]

        field_type = get_args(field_type)
        if len(field_type) == 0:
            field_type = origin_type
        else:
            field_type = field_type[0]

        if isinstance(" ", field_type):
            if hasattr(field_info, 'max_length'):
                field_kwargs['max_length'] = field_info.max_length
            return forms.CharField(**field_kwargs)
        elif isinstance(0, field_type):
            return forms.IntegerField(**field_kwargs)
        elif isinstance(0.1, field_type):
            return forms.FloatField(**field_kwargs)
        elif issubclass(field_type, bool):
            return forms.BooleanField(**field_kwargs)
        elif isinstance(date.today(), field_type):
            return forms.DateField(**field_kwargs)
        elif isinstance(datetime.now(), field_type):
            return forms.DateTimeField(**field_kwargs)
        elif inspect.isclass(field_type) and issubclass(field_type, BaseModel):
            return forms.JSONField(**field_kwargs)
        else:
            return forms.CharField(**field_kwargs)

    @staticmethod
    def _create_clean_method(pydantic_model):
        """Creates clean method with Pydantic validation"""
        def clean(self):
            cleaned_data = super().clean()
            try:
                pydantic_model(**cleaned_data)
            except ValidationError as e:
                for error in e.errors():
                    field = error['loc'][0]
                    self.add_error(field, error['msg'])
            return cleaned_data
        return clean

    @staticmethod
    def _schema_to_fields(schema: Dict[str, Any]) -> Dict[str, Any]:
        """Converts JSON schema to Pydantic field definitions"""
        fields = {}
    
        if 'properties' not in schema:
            raise ValueError("Schema must have 'properties' key")
    
        for prop_name, prop_details in schema['properties'].items():
            field_type = prop_details.get('type', 'string')
            required = prop_name in schema.get('required', [])
        
            # Map JSON schema types to Python types
            py_type = {
                'string': str,
                'integer': int,
                'number': float,
                'boolean': bool,
                'array': List,
                'object': Dict
            }.get(field_type, str)
        
            # Handle arrays
            if field_type == 'array' and 'items' in prop_details:
                item_type = prop_details['items'].get('type', 'string')
                py_type = List[{
                    'string': str,
                    'integer': int,
                    'number': float,
                    'boolean': bool,
                    'object': Dict
                }.get(item_type, str)]
        
            # Create Field with constraints
            field_kwargs = {}
            if 'description' in prop_details:
                field_kwargs['description'] = prop_details['description']
            if 'minimum' in prop_details:
                field_kwargs['ge'] = prop_details['minimum']
            if 'maximum' in prop_details:
                field_kwargs['le'] = prop_details['maximum']
            if 'minLength' in prop_details:
                field_kwargs['min_length'] = prop_details['minLength']
            if 'maxLength' in prop_details:
                field_kwargs['max_length'] = prop_details['maxLength']
            if 'pattern' in prop_details:
                field_kwargs['regex'] = prop_details['pattern']
        
            if not required:
                py_type = Optional[py_type]
                field_kwargs['default'] = None
        
            fields[prop_name] = (py_type, Field(**field_kwargs))
    
        return fields
