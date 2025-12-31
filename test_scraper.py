import pytest
from monitor_buckethead import is_southern_wa

def test_is_southern_wa():
    # Test True cases
    assert is_southern_wa("Vancouver", "WA")
    assert is_southern_wa("Ridgefield", "WA")
    assert is_southern_wa("vancouver", "WA") # case insensitive
    
    # Test False cases
    assert not is_southern_wa("Seattle", "WA")
    assert not is_southern_wa("Spokane", "WA")
    assert not is_southern_wa("Vancouver", "BC") # wrong state
    assert not is_southern_wa("Portland", "OR") # handled by OR check, but strictly for this function it returns False if state != WA

# We can't easily mock the full playwright session without a complex mock, 
# but we can test the helper functions.
