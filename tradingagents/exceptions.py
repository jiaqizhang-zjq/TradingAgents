#!/usr/bin/env python3
"""
自定义异常类
提供详细的错误信息和类型安全的异常处理
"""

from typing import Optional, Any


class TradingAgentsException(Exception):
    """所有TradingAgents异常的基类"""
    pass


# ==================== 输入验证异常 ====================

class ValidationError(TradingAgentsException):
    """输入验证失败"""
    
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Validation failed for {field}: {message}")


# ==================== 数据相关异常 ====================

class DataError(TradingAgentsException):
    """数据相关异常基类"""
    pass


class DataFetchError(DataError):
    """数据获取失败"""
    
    def __init__(
        self,
        vendor: str,
        symbol: str,
        reason: str,
        original_error: Optional[Exception] = None
    ):
        self.vendor = vendor
        self.symbol = symbol
        self.reason = reason
        self.original_error = original_error
        
        message = f"Failed to fetch data from {vendor} for {symbol}: {reason}"
        if original_error:
            message += f" (Original: {str(original_error)})"
        
        super().__init__(message)


class DataValidationError(DataError):
    """数据验证失败"""
    
    def __init__(self, field: str, value: Any, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Validation failed for {field}='{value}': {reason}")


class DataNotFoundError(DataError):
    """数据不存在"""
    
    def __init__(self, data_type: str, identifier: str):
        self.data_type = data_type
        self.identifier = identifier
        super().__init__(f"{data_type} not found: {identifier}")


class InsufficientDataError(DataError):
    """数据量不足"""
    
    def __init__(self, required: int, actual: int, data_type: str):
        self.required = required
        self.actual = actual
        self.data_type = data_type
        super().__init__(
            f"Insufficient {data_type}: required {required}, got {actual}"
        )


# ==================== LLM相关异常 ====================

class LLMError(TradingAgentsException):
    """LLM相关异常基类"""
    pass


class LLMInvokeError(LLMError):
    """LLM调用失败"""
    
    def __init__(
        self,
        model: str,
        reason: str,
        original_error: Optional[Exception] = None
    ):
        self.model = model
        self.reason = reason
        self.original_error = original_error
        
        message = f"LLM invoke failed (model={model}): {reason}"
        if original_error:
            message += f" (Original: {str(original_error)})"
        
        super().__init__(message)


class LLMTimeoutError(LLMError):
    """LLM调用超时"""
    
    def __init__(self, model: str, timeout: int):
        self.model = model
        self.timeout = timeout
        super().__init__(f"LLM call timed out after {timeout}s (model={model})")


class LLMResponseParseError(LLMError):
    """LLM响应解析失败"""
    
    def __init__(self, response: str, reason: str):
        self.response = response
        self.reason = reason
        super().__init__(f"Failed to parse LLM response: {reason}")


# ==================== 状态相关异常 ====================

class StateError(TradingAgentsException):
    """状态相关异常基类"""
    pass


class InvalidStateError(StateError):
    """状态无效"""
    
    def __init__(self, field: str, value: Any, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Invalid state field {field}='{value}': {reason}")


class MissingStateFieldError(StateError):
    """状态字段缺失"""
    
    def __init__(self, field: str, state_type: str):
        self.field = field
        self.state_type = state_type
        super().__init__(f"Required field '{field}' missing in {state_type}")


# ==================== 配置相关异常 ====================

class ConfigError(TradingAgentsException):
    """配置相关异常基类"""
    pass


class MissingConfigError(ConfigError):
    """配置缺失"""
    
    def __init__(self, config_key: str):
        self.config_key = config_key
        super().__init__(f"Required configuration '{config_key}' is missing")


class InvalidConfigError(ConfigError):
    """配置无效"""
    
    def __init__(self, config_key: str, value: Any, reason: str):
        self.config_key = config_key
        self.value = value
        self.reason = reason
        super().__init__(f"Invalid config {config_key}='{value}': {reason}")


# ==================== API相关异常 ====================

class APIError(TradingAgentsException):
    """API相关异常基类"""
    pass


class APIKeyError(APIError):
    """API密钥错误"""
    
    def __init__(self, service: str):
        self.service = service
        super().__init__(f"Invalid or missing API key for {service}")


class APIRateLimitError(APIError):
    """API速率限制"""
    
    def __init__(self, service: str, retry_after: Optional[int] = None):
        self.service = service
        self.retry_after = retry_after
        
        message = f"API rate limit exceeded for {service}"
        if retry_after:
            message += f", retry after {retry_after}s"
        
        super().__init__(message)


class APIResponseError(APIError):
    """API响应错误"""
    
    def __init__(self, service: str, status_code: int, reason: str):
        self.service = service
        self.status_code = status_code
        self.reason = reason
        super().__init__(
            f"API error from {service} (status={status_code}): {reason}"
        )


# ==================== Agent相关异常 ====================

class AgentError(TradingAgentsException):
    """Agent相关异常基类"""
    pass


class AgentExecutionError(AgentError):
    """Agent执行失败"""
    
    def __init__(self, agent_type: str, reason: str):
        self.agent_type = agent_type
        self.reason = reason
        super().__init__(f"Agent {agent_type} execution failed: {reason}")


class AgentNotFoundError(AgentError):
    """Agent不存在"""
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        super().__init__(f"Agent type '{agent_type}' not found")


# ==================== 缓存相关异常 ====================

class CacheError(TradingAgentsException):
    """缓存相关异常基类"""
    pass


class CacheExpiredError(CacheError):
    """缓存已过期"""
    
    def __init__(self, cache_key: str):
        self.cache_key = cache_key
        super().__init__(f"Cache expired for key: {cache_key}")


# ==================== 数据库相关异常 ====================

class DatabaseError(TradingAgentsException):
    """数据库相关异常基类"""
    pass


class DatabaseConnectionError(DatabaseError):
    """数据库连接失败"""
    
    def __init__(self, db_path: str, reason: str):
        self.db_path = db_path
        self.reason = reason
        super().__init__(f"Database connection failed ({db_path}): {reason}")


class DatabaseQueryError(DatabaseError):
    """数据库查询失败"""
    
    def __init__(self, query: str, reason: str):
        self.query = query
        self.reason = reason
        super().__init__(f"Database query failed: {reason}")
