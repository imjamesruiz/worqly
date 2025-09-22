"""
Data transformation tasks for Worqly workflow automation
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def data_transformer(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Data transformer task - transform input data
    
    Args:
        config: Transformation configuration
        input_data: Input data from previous nodes
        
    Returns:
        Transformed data
    """
    try:
        transformation_type = config.get('transformation_type', 'mapping')
        
        if transformation_type == 'mapping':
            # Field mapping transformation
            mapping = config.get('mapping', {})
            result = _apply_field_mapping(input_data, mapping)
            
        elif transformation_type == 'javascript':
            # JavaScript transformation
            script = config.get('script', '')
            result = _apply_javascript_transformation(input_data, script)
            
        elif transformation_type == 'json_path':
            # JSONPath transformation
            json_path = config.get('json_path', '')
            result = _apply_json_path_transformation(input_data, json_path)
            
        elif transformation_type == 'template':
            # Template transformation
            template = config.get('template', '')
            result = _apply_template_transformation(input_data, template)
            
        else:
            # Default: pass through data
            result = input_data
        
        return {
            'success': True,
            'transformed_data': result
        }
        
    except Exception as e:
        logger.error(f"Data transformer error: {str(e)}")
        raise self.retry(countdown=60, exc=e)


@celery_app.task(bind=True, max_retries=3)
def data_filter(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Data filter task - filter input data based on criteria
    
    Args:
        config: Filter configuration
        input_data: Input data from previous nodes
        
    Returns:
        Filtered data
    """
    try:
        filter_type = config.get('filter_type', 'simple')
        
        if filter_type == 'simple':
            # Simple field-based filtering
            field = config.get('field', '')
            operator = config.get('operator', 'equals')
            value = config.get('value', '')
            
            result = _apply_simple_filter(input_data, field, operator, value)
            
        elif filter_type == 'array':
            # Array filtering
            array_field = config.get('array_field', '')
            filter_condition = config.get('filter_condition', {})
            
            result = _apply_array_filter(input_data, array_field, filter_condition)
            
        elif filter_type == 'javascript':
            # JavaScript filtering
            script = config.get('script', '')
            result = _apply_javascript_filter(input_data, script)
            
        else:
            # Default: pass through data
            result = input_data
        
        return {
            'success': True,
            'filtered_data': result
        }
        
    except Exception as e:
        logger.error(f"Data filter error: {str(e)}")
        raise self.retry(countdown=60, exc=e)


@celery_app.task(bind=True, max_retries=3)
def data_aggregator(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Data aggregator task - aggregate data from multiple sources
    
    Args:
        config: Aggregation configuration
        input_data: Input data from previous nodes
        
    Returns:
        Aggregated data
    """
    try:
        aggregation_type = config.get('aggregation_type', 'merge')
        
        if aggregation_type == 'merge':
            # Merge data from multiple sources
            result = _merge_data(input_data)
            
        elif aggregation_type == 'group':
            # Group data by field
            group_field = config.get('group_field', '')
            result = _group_data(input_data, group_field)
            
        elif aggregation_type == 'sum':
            # Sum numeric fields
            sum_fields = config.get('sum_fields', [])
            result = _sum_data(input_data, sum_fields)
            
        elif aggregation_type == 'count':
            # Count items
            count_field = config.get('count_field', '')
            result = _count_data(input_data, count_field)
            
        else:
            # Default: pass through data
            result = input_data
        
        return {
            'success': True,
            'aggregated_data': result
        }
        
    except Exception as e:
        logger.error(f"Data aggregator error: {str(e)}")
        raise self.retry(countdown=60, exc=e)


@celery_app.task(bind=True, max_retries=3)
def json_parser(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    JSON parser task - parse JSON strings
    
    Args:
        config: Parser configuration
        input_data: Input data from previous nodes
        
    Returns:
        Parsed JSON data
    """
    try:
        json_field = config.get('json_field', 'data')
        output_field = config.get('output_field', 'parsed_data')
        
        # Get JSON string from input data
        json_string = _get_nested_value(input_data, json_field)
        
        if isinstance(json_string, str):
            # Parse JSON string
            parsed_data = json.loads(json_string)
        else:
            # Already parsed or not a string
            parsed_data = json_string
        
        # Create result with parsed data
        result = input_data.copy()
        result[output_field] = parsed_data
        
        return {
            'success': True,
            'parsed_data': result
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parser error: {str(e)}")
        return {
            'success': False,
            'error': f"Invalid JSON: {str(e)}"
        }
    except Exception as e:
        logger.error(f"JSON parser error: {str(e)}")
        raise self.retry(countdown=60, exc=e)


def _apply_field_mapping(data: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
    """Apply field mapping transformation"""
    
    result = {}
    
    for output_field, input_field in mapping.items():
        value = _get_nested_value(data, input_field)
        result[output_field] = value
    
    return result


def _apply_javascript_transformation(data: Dict[str, Any], script: str) -> Dict[str, Any]:
    """Apply JavaScript transformation (basic implementation)"""
    
    # WARNING: This is a basic implementation and not safe for production
    # In production, use a proper JavaScript engine like PyV8 or Node.js subprocess
    
    try:
        # Simple variable replacement in script
        processed_script = script
        
        # Replace data references
        for key, value in data.items():
            placeholder = f"data.{key}"
            processed_script = processed_script.replace(placeholder, repr(value))
        
        # Execute script (UNSAFE - use proper JS engine in production)
        # This is just for demonstration
        result = eval(processed_script)
        return result
        
    except Exception as e:
        logger.error(f"JavaScript transformation error: {str(e)}")
        return data


def _apply_json_path_transformation(data: Dict[str, Any], json_path: str) -> Dict[str, Any]:
    """Apply JSONPath transformation"""
    
    # Basic JSONPath implementation
    # In production, use jsonpath-ng library
    
    try:
        if json_path.startswith('$.'):
            # Simple JSONPath
            path_parts = json_path[2:].split('.')
            result = data
            
            for part in path_parts:
                if isinstance(result, dict) and part in result:
                    result = result[part]
                else:
                    return None
            
            return result
        else:
            return data
            
    except Exception as e:
        logger.error(f"JSONPath transformation error: {str(e)}")
        return data


def _apply_template_transformation(data: Dict[str, Any], template: str) -> Dict[str, Any]:
    """Apply template transformation"""
    
    result = template
    
    # Replace template variables
    for key, value in data.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                placeholder = f"{{{{{key}.{sub_key}}}}}"
                result = result.replace(placeholder, str(sub_value))
        else:
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
    
    return result


def _apply_simple_filter(data: Dict[str, Any], field: str, operator: str, value: Any) -> Dict[str, Any]:
    """Apply simple field-based filter"""
    
    field_value = _get_nested_value(data, field)
    
    # Evaluate condition
    if operator == 'equals':
        condition_met = str(field_value) == str(value)
    elif operator == 'not_equals':
        condition_met = str(field_value) != str(value)
    elif operator == 'contains':
        condition_met = str(value) in str(field_value)
    elif operator == 'not_contains':
        condition_met = str(value) not in str(field_value)
    elif operator == 'greater_than':
        try:
            condition_met = float(field_value) > float(value)
        except (ValueError, TypeError):
            condition_met = False
    elif operator == 'less_than':
        try:
            condition_met = float(field_value) < float(value)
        except (ValueError, TypeError):
            condition_met = False
    else:
        condition_met = True
    
    return data if condition_met else {}


def _apply_array_filter(data: Dict[str, Any], array_field: str, filter_condition: Dict[str, Any]) -> Dict[str, Any]:
    """Apply array filtering"""
    
    array_data = _get_nested_value(data, array_field)
    
    if not isinstance(array_data, list):
        return data
    
    # Filter array based on condition
    filtered_array = []
    for item in array_data:
        if isinstance(item, dict):
            # Check if item matches filter condition
            matches = True
            for field, expected_value in filter_condition.items():
                if item.get(field) != expected_value:
                    matches = False
                    break
            
            if matches:
                filtered_array.append(item)
    
    # Update data with filtered array
    result = data.copy()
    _set_nested_value(result, array_field, filtered_array)
    
    return result


def _apply_javascript_filter(data: Dict[str, Any], script: str) -> Dict[str, Any]:
    """Apply JavaScript filtering"""
    
    # Similar to JavaScript transformation but for filtering
    try:
        # Simple implementation - in production use proper JS engine
        processed_script = script
        
        for key, value in data.items():
            placeholder = f"data.{key}"
            processed_script = processed_script.replace(placeholder, repr(value))
        
        # Execute filter script
        filter_result = eval(processed_script)
        return data if filter_result else {}
        
    except Exception as e:
        logger.error(f"JavaScript filter error: {str(e)}")
        return data


def _merge_data(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Merge data from multiple sources"""
    
    result = {}
    
    for key, value in input_data.items():
        if isinstance(value, dict):
            result.update(value)
        else:
            result[key] = value
    
    return result


def _group_data(input_data: Dict[str, Any], group_field: str) -> Dict[str, Any]:
    """Group data by field"""
    
    # This is a simplified implementation
    # In production, handle more complex grouping scenarios
    
    groups = {}
    
    for key, value in input_data.items():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and group_field in item:
                    group_key = item[group_field]
                    if group_key not in groups:
                        groups[group_key] = []
                    groups[group_key].append(item)
    
    return groups


def _sum_data(input_data: Dict[str, Any], sum_fields: List[str]) -> Dict[str, Any]:
    """Sum numeric fields"""
    
    result = {}
    
    for field in sum_fields:
        total = 0
        for key, value in input_data.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and field in item:
                        try:
                            total += float(item[field])
                        except (ValueError, TypeError):
                            pass
        
        result[f"{field}_sum"] = total
    
    return result


def _count_data(input_data: Dict[str, Any], count_field: str) -> Dict[str, Any]:
    """Count items"""
    
    count = 0
    
    for key, value in input_data.items():
        if isinstance(value, list):
            count += len(value)
        elif count_field in str(key):
            count += 1
    
    return {f"{count_field}_count": count}


def _get_nested_value(data: Dict[str, Any], field_path: str) -> Any:
    """Get nested value from data using dot notation"""
    
    if not field_path:
        return None
    
    keys = field_path.split('.')
    value = data
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    
    return value


def _set_nested_value(data: Dict[str, Any], field_path: str, value: Any) -> None:
    """Set nested value in data using dot notation"""
    
    if not field_path:
        return
    
    keys = field_path.split('.')
    current = data
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value
