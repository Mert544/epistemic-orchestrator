from __future__ import annotations

import pytest

from app.execution.advanced_refactoring import AdvancedRefactoringEngine


def test_extract_interface_success():
    source = """
class UserService:
    def get_user(self, user_id: int) -> dict:
        pass

    def delete_user(self, user_id: int) -> bool:
        pass

    def _internal(self):
        pass
"""
    result = AdvancedRefactoringEngine.extract_interface(source, "UserService")
    assert result.success
    assert "IUserService" in result.description
    assert "from abc import ABC, abstractmethod" in result.new_content
    assert "def get_user" in result.new_content
    assert "def delete_user" in result.new_content
    assert "@abstractmethod" in result.new_content
    assert "_internal" not in result.new_content


def test_extract_interface_class_not_found():
    result = AdvancedRefactoringEngine.extract_interface("", "Missing")
    assert not result.success
    assert "not found" in result.description


def test_extract_interface_no_public_methods():
    source = "class Empty:\n    def _private(self): pass\n"
    result = AdvancedRefactoringEngine.extract_interface(source, "Empty")
    assert not result.success
    assert "No public methods" in result.description


def test_introduce_parameter_object_success():
    source = """
def create_order(user_id, product_id, quantity, shipping_address, billing_address):
    pass
"""
    result = AdvancedRefactoringEngine.introduce_parameter_object(
        source, "create_order", param_indices=[0, 1, 2], object_name="OrderParams"
    )
    assert result.success
    assert "OrderParams" in result.description
    assert "@dataclass" in result.new_content
    assert "class OrderParams" in result.new_content
    assert "user_id" in result.new_content
    assert "product_id" in result.new_content
    assert "quantity" in result.new_content


def test_introduce_parameter_object_not_enough_params():
    source = "def foo(a, b): pass\n"
    result = AdvancedRefactoringEngine.introduce_parameter_object(source, "foo", param_indices=[0])
    assert not result.success
    assert "at least 2 parameters" in result.description


def test_introduce_parameter_object_function_not_found():
    result = AdvancedRefactoringEngine.introduce_parameter_object("", "missing")
    assert not result.success
    assert "not found" in result.description


def test_available_transforms():
    transforms = AdvancedRefactoringEngine.available_transforms()
    assert "extract_interface" in transforms
    assert "introduce_parameter_object" in transforms
