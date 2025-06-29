# tests/test_validators_tdd.py - TDD approach for validators
"""
Test-Driven Development for Israeli ID and Phone Number Validators

This module demonstrates TDD methodology:
1. Write failing tests first (Red)
2. Write minimal code to pass (Green) 
3. Refactor for quality (Refactor)
"""
import pytest
import sys
import os

# Add server directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from validators import validate_israeli_id, validate_phone_number


class TestIsraeliIDValidatorTDD:
    """
    TDD Test Suite for Israeli ID Validation
    
    Requirements:
    - Must be 8 or 9 digits
    - Must pass Israeli ID checksum algorithm
    - Should handle edge cases gracefully
    """
    
    @pytest.mark.unit
    @pytest.mark.smoke
    def test_valid_9_digit_israeli_id(self, valid_israeli_ids):
        """
        Test Case: Valid 9-digit Israeli IDs should pass validation
        TDD Phase: Red -> Green -> Refactor
        """
        for israeli_id in valid_israeli_ids:
            if len(israeli_id) == 9:
                assert validate_israeli_id(israeli_id), f"ID {israeli_id} should be valid"
    
    @pytest.mark.unit
    @pytest.mark.smoke
    def test_valid_8_digit_israeli_id_padded_internally(self):
        """
        Test Case: Valid 8-digit IDs should be internally padded and validated
        Business Rule: 8-digit IDs are padded with leading zero
        """
        eight_digit_ids = ["12345678", "87654321"]
        for israeli_id in eight_digit_ids:
            assert validate_israeli_id(israeli_id), f"8-digit ID {israeli_id} should be valid"
    
    @pytest.mark.unit
    @pytest.mark.parametrize("invalid_id,reason", [
        ("1234567", "too_short_7_digits"),
        ("1234567890", "too_long_10_digits"), 
        ("123456789", "invalid_checksum"),
        ("12345678a", "contains_non_digit"),
        ("", "empty_string"),
        (None, "none_value"),
        ("00000000", "all_zeros"),
        ("   ", "whitespace_only")
    ])
    def test_invalid_israeli_ids_should_fail(self, invalid_id, reason):
        """
        Test Case: Invalid Israeli IDs should fail validation
        Parametrized test for comprehensive edge case coverage
        """
        assert not validate_israeli_id(invalid_id), f"ID {invalid_id} should fail ({reason})"
    
    @pytest.mark.unit
    def test_israeli_id_checksum_algorithm_implementation(self):
        """
        Test Case: Verify correct checksum algorithm implementation
        This test ensures we're using the official Israeli ID algorithm
        """
        # Known valid IDs with their checksums calculated manually
        test_cases = [
            ("123456782", True),   # Valid checksum
            ("123456789", False),  # Invalid checksum (common mistake)
            ("000000000", False),  # All zeros (edge case)
        ]
        
        for israeli_id, expected in test_cases:
            result = validate_israeli_id(israeli_id)
            assert result == expected, f"ID {israeli_id} checksum validation failed"
    
    @pytest.mark.unit
    @pytest.mark.regression
    def test_edge_cases_that_caused_bugs_previously(self):
        """
        Test Case: Regression test for previously discovered edge cases
        These are real-world cases that caused issues in production
        """
        edge_cases = [
            ("0", False),          # Single digit
            ("12", False),         # Two digits
            ("123", False),        # Three digits
            ("1234", False),       # Four digits
            ("12345", False),      # Five digits
            ("123456", False),     # Six digits
            ("1234567", False),    # Seven digits (boundary)
        ]
        
        for israeli_id, expected in edge_cases:
            assert validate_israeli_id(israeli_id) == expected


class TestPhoneNumberValidatorTDD:
    """
    TDD Test Suite for Israeli Phone Number Validation
    
    Requirements:
    - Must start with "05"
    - Must be exactly 10 digits total
    - Should handle formatting (dashes, spaces) gracefully
    """
    
    @pytest.mark.unit
    @pytest.mark.smoke
    def test_valid_israeli_phone_numbers(self, valid_phone_numbers):
        """
        Test Case: Valid Israeli phone numbers should pass validation
        Format: 05XXXXXXXX (10 digits total)
        """
        for phone in valid_phone_numbers:
            assert validate_phone_number(phone), f"Phone {phone} should be valid"
    
    @pytest.mark.unit
    @pytest.mark.parametrize("phone,expected", [
        ("0501234567", True),    # Standard format
        ("0509876543", True),    # Different number
        ("050-123-4567", True),  # With dashes
        ("050 123 4567", True),  # With spaces
        ("050.123.4567", True),  # With dots
    ])
    def test_phone_formatting_tolerance(self, phone, expected):
        """
        Test Case: Phone validation should handle common formatting
        Business Rule: Accept dashes, spaces, dots in phone numbers
        """
        assert validate_phone_number(phone) == expected
    
    @pytest.mark.unit
    @pytest.mark.parametrize("invalid_phone,reason", [
        ("0521234567", "wrong_prefix_052"),
        ("050123456", "too_short_9_digits"),
        ("05012345678", "too_long_11_digits"),
        ("1501234567", "doesnt_start_with_05"),
        ("050123456a", "contains_letter"),
        ("", "empty_string"),
        (None, "none_value"),
        ("+972501234567", "international_format"),
        ("972501234567", "country_code_without_plus"),
        ("05-123-456", "too_short_with_dashes"),
    ])
    def test_invalid_phone_numbers_should_fail(self, invalid_phone, reason):
        """
        Test Case: Invalid phone numbers should fail validation
        Comprehensive test for all failure scenarios
        """
        assert not validate_phone_number(invalid_phone), f"Phone {invalid_phone} should fail ({reason})"
    
    @pytest.mark.unit
    def test_phone_number_prefix_validation_strict(self):
        """
        Test Case: Phone number must start with exactly "05"
        Business Rule: Only Israeli mobile numbers starting with 05
        """
        valid_prefixes = ["050", "051", "052", "053", "054", "055", "056", "057", "058", "059"]
        invalid_prefixes = ["04", "03", "02", "08", "09", "06", "07"]
        
        # Test that 05X are valid (when followed by 7 more digits)
        for prefix in valid_prefixes:
            if prefix.startswith("05"):
                phone = prefix + "1234567"  # Make it 10 digits total
                assert validate_phone_number(phone), f"Phone with prefix {prefix} should be valid"
        
        # Test that non-05 prefixes are invalid
        for prefix in invalid_prefixes:
            phone = prefix + "12345678"  # 10 digits total
            assert not validate_phone_number(phone), f"Phone with prefix {prefix} should be invalid"
    
    @pytest.mark.unit
    @pytest.mark.regression
    def test_phone_number_regression_cases(self):
        """
        Test Case: Regression test for phone number edge cases
        These cases were discovered during production debugging
        """
        regression_cases = [
            ("05012345", False),     # 8 digits (too short)
            ("050123456789", False), # 12 digits (too long)
            ("05012345ab", False),   # Mixed alphanumeric
            ("050-12-34567", False), # Wrong dash placement but correct count
            ("050  1234567", True),  # Multiple spaces (should normalize)
            ("050--123-4567", False), # Double dashes
        ]
        
        for phone, expected in regression_cases:
            result = validate_phone_number(phone)
            assert result == expected, f"Regression case failed: {phone} expected {expected}, got {result}"


class TestValidatorIntegrationTDD:
    """
    Integration tests for validators working together
    TDD approach for cross-validator scenarios
    """
    
    @pytest.mark.integration
    def test_user_data_validation_complete_flow(self):
        """
        Test Case: Complete user data validation flow
        Integration test ensuring all validators work together
        """
        valid_user_data = [
            ("123456782", "0501234567"),  # Both valid
            ("12345678", "0509876543"),   # 8-digit ID, valid phone
        ]
        
        invalid_combinations = [
            ("1234567", "0501234567"),    # Invalid ID, valid phone
            ("123456782", "0521234567"),  # Valid ID, invalid phone
            ("1234567", "0521234567"),    # Both invalid
        ]
        
        # Test valid combinations
        for israeli_id, phone in valid_user_data:
            assert validate_israeli_id(israeli_id), f"ID {israeli_id} should be valid"
            assert validate_phone_number(phone), f"Phone {phone} should be valid"
        
        # Test invalid combinations
        for israeli_id, phone in invalid_combinations:
            id_valid = validate_israeli_id(israeli_id)
            phone_valid = validate_phone_number(phone)
            assert not (id_valid and phone_valid), f"At least one of {israeli_id}/{phone} should be invalid"
    
    @pytest.mark.integration
    @pytest.mark.benchmark
    def test_validator_performance_benchmark(self, benchmark):
        """
        Test Case: Performance benchmark for validators
        Ensures validators perform well under load
        """
        test_id = "123456782"
        test_phone = "0501234567"
        
        def run_validators():
            return (validate_israeli_id(test_id), validate_phone_number(test_phone))
        
        result = benchmark(run_validators)
        assert result == (True, True)
        
        # Performance assertions (adjust based on requirements)
        assert benchmark.stats.stats.mean < 0.001  # Should complete in < 1ms


# TDD Helper Functions and Utilities
class TestDataFactory:
    """
    Factory class for generating test data following TDD principles
    """
    
    @staticmethod
    def create_valid_israeli_id():
        """Generate a valid Israeli ID for testing"""
        # This is a simplified version - in real TDD, this would be developed iteratively
        return "123456782"
    
    @staticmethod
    def create_valid_phone_number():
        """Generate a valid Israeli phone number for testing"""
        return "0501234567"
    
    @staticmethod
    def create_invalid_israeli_id(reason="too_short"):
        """Generate invalid Israeli ID for specific test scenarios"""
        invalid_ids = {
            "too_short": "1234567",
            "too_long": "1234567890",
            "invalid_checksum": "123456789",
            "non_numeric": "12345678a"
        }
        return invalid_ids.get(reason, "invalid")


# Pytest fixtures for TDD workflow
@pytest.fixture
def tdd_test_data():
    """
    Fixture providing structured test data for TDD workflow
    This supports the Red-Green-Refactor cycle
    """
    return {
        "valid_cases": {
            "israeli_ids": ["123456782", "12345678", "87654321"],
            "phone_numbers": ["0501234567", "0509876543", "0507654321"]
        },
        "invalid_cases": {
            "israeli_ids": ["1234567", "1234567890", "123456789"],
            "phone_numbers": ["0521234567", "050123456", "05012345678"]
        },
        "edge_cases": {
            "israeli_ids": ["", None, "00000000"],
            "phone_numbers": ["", None, "+972501234567"]
        }
    }


@pytest.fixture
def mock_validation_service(mocker):
    """
    Mock fixture for testing validation service integration
    Supports TDD by allowing isolated unit testing
    """
    mock_service = mocker.Mock()
    mock_service.validate_israeli_id.return_value = True
    mock_service.validate_phone_number.return_value = True
    return mock_service
