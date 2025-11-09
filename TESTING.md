# AlphaShield Testing Strategy

This document outlines the testing approach for the AlphaShield system, including current test coverage and guidelines for adding new tests.

---

## Test Overview

### Current Test Coverage

**Total Tests**: 108 tests  
**Passing Tests**: 105 (97.2%)  
**Test Categories**:
- Integration tests: 1
- RL (Reinforcement Learning) tests: 13
- Agent schema tests: 19
- Context management tests: 8
- Loan model tests: 8
- Orchestrator tests: 8
- Quantum optimizer tests: 18
- Spending guard tests: 6
- Treasury tests: 15
- Trading tests: 12

### Known Issues (Pre-existing)

The following tests have pre-existing failures unrelated to the roadmap implementation:

1. **test_backtester_metrics_shape_and_ranges** - `NameError: name 'exp_return' is not defined`
   - Location: `tests/trading/test_backtester.py`
   - Issue: Missing variable definition in backtester.py line 143

2. **test_detect_outliers_methods** - Outlier detection not finding expected outliers
   - Location: `tests/trading/test_data_validator.py`
   - Issue: Data validation logic needs adjustment

3. **test_check_liquidity_adv_threshold** - Liquidity check not working as expected
   - Location: `tests/trading/test_data_validator.py`
   - Issue: ADV threshold logic needs review

These issues should be tracked separately and are not part of the roadmap implementation scope.

---

## Testing Philosophy

### Test Pyramid

```
         /\
        /  \       E2E Tests (1-5%)
       /----\      - Full system integration
      /      \     - End-to-end workflows
     /--------\    
    / Integration \ Integration Tests (10-20%)
   /    Tests     \- Cross-component interactions
  /--------------\ - Agent coordination
 /                \
/   Unit Tests     \ Unit Tests (75-85%)
\   (fast, focused)/- Individual functions
 \                /- Pure logic
  \--------------/- Mock external dependencies
```

### Testing Principles

1. **Test Behavior, Not Implementation**
   - Focus on what the code does, not how it does it
   - Avoid testing internal implementation details

2. **Fast Feedback Loop**
   - Unit tests should run in <1 second
   - Integration tests should run in <10 seconds
   - Full suite should run in <2 minutes

3. **Isolated Tests**
   - Each test should be independent
   - Use mocks/stubs for external dependencies (MongoDB, APIs)
   - No shared state between tests

4. **Readable Tests**
   - Test names describe what is being tested
   - Use Given-When-Then structure
   - Keep tests simple and focused

5. **Coverage Targets**
   - Minimum 80% code coverage
   - Critical paths: 100% coverage
   - Error handling: 100% coverage

---

## Test Structure

### Unit Tests

**Location**: `tests/`

Unit tests validate individual functions and classes in isolation.

**Naming Convention**: `test_<module_name>.py`

**Example**:
```python
# tests/test_loan_model.py
def test_loan_initialization():
    """Test that a loan initializes with correct values."""
    # Given
    loan = Loan(
        borrower_id="borrower_123",
        principal=10000,
        interest_rate=8.0,
        term_months=36
    )
    
    # Then
    assert loan.principal == 10000
    assert loan.interest_rate == 8.0
    assert loan.term_months == 36
```

### Integration Tests

**Location**: `tests/integration/`

Integration tests validate interactions between multiple components.

**Example**:
```python
# tests/integration/test_loan_flow.py
def test_full_loan_origination_flow():
    """Test complete flow from loan origination to investment."""
    # Given: A loan request
    orchestrator = AlphaShieldOrchestrator()
    
    # When: Originating a loan
    result = orchestrator.originate_loan(
        borrower_id="borrower_123",
        principal=10000,
        interest_rate=8.0,
        term_months=36
    )
    
    # Then: Loan is created and invested
    assert result['status'] == 'approved'
    assert result['split']['investment'] == 6000
    assert result['split']['borrower'] == 4000
```

### End-to-End Tests

**Location**: `tests/e2e/` (to be created)

E2E tests validate complete user workflows from start to finish.

**Example**:
```python
# tests/e2e/test_borrower_journey.py
def test_complete_borrower_journey():
    """Test full borrower journey from application to recommendations."""
    # Given: New borrower application
    # When: Going through full process
    # Then: Borrower receives loan and recommendations
```

---

## Testing by Component

### 1. Trading Engine Tests (Phase 1)

#### Broker Integration Tests
**Location**: `tests/trading/brokers/`

```python
# tests/trading/brokers/test_alpaca_client.py

@pytest.fixture
def mock_alpaca_api():
    """Mock Alpaca API responses."""
    with patch('alpaca_trade_api.REST') as mock:
        yield mock

def test_market_order_execution(mock_alpaca_api):
    """Test successful market order execution."""
    # Given: Alpaca client and mock API
    client = AlpacaClient(api_key="test", secret="test")
    mock_alpaca_api.submit_order.return_value = {
        'id': 'order_123',
        'status': 'filled'
    }
    
    # When: Executing a market order
    order = client.execute_market_order(
        symbol='SPY',
        quantity=10,
        side='buy'
    )
    
    # Then: Order is submitted correctly
    assert order['status'] == 'filled'
    mock_alpaca_api.submit_order.assert_called_once()

def test_api_rate_limiting(mock_alpaca_api):
    """Test that rate limiting prevents excessive API calls."""
    # Given: Client with rate limit
    client = AlpacaClient(api_key="test", secret="test", rate_limit=5)
    
    # When: Making many rapid requests
    # Then: Rate limiter enforces limit
    # ... implementation
```

#### Asset Trading Tests
**Location**: `tests/trading/assets/`

```python
# tests/trading/assets/test_stocks.py

def test_stock_market_hours_validation():
    """Test that stocks can only be traded during market hours."""
    # Given: Stock handler
    handler = StockHandler()
    
    # When: Attempting trade outside market hours
    # Then: Raises MarketClosedError
    with pytest.raises(MarketClosedError):
        handler.validate_trade_time(datetime(2024, 1, 1, 22, 0))  # 10 PM
```

#### Error Handling Tests
**Location**: `tests/trading/test_error_handling.py`

```python
def test_transient_error_retry():
    """Test that transient errors trigger retries."""
    # Given: Function that fails twice then succeeds
    # When: Calling with retry logic
    # Then: Eventually succeeds after retries

def test_critical_error_halts_system():
    """Test that critical errors halt trading."""
    # Given: Critical error condition
    # When: Error occurs
    # Then: System halts and alerts
```

### 2. Vector Database Tests (Phase 2)

#### Vector Search Tests
**Location**: `tests/database/test_vector_search.py`

```python
def test_semantic_search_relevance():
    """Test that semantic search returns relevant results."""
    # Given: Vector database with test data
    # When: Searching for similar contexts
    # Then: Results are semantically similar

def test_vector_search_performance():
    """Test that vector search meets latency requirements."""
    # Given: Large dataset
    # When: Performing search
    # Then: Latency < 100ms
```

### 3. Quantum Optimization Tests (Phase 3)

**Location**: `tests/test_quantum_optimizer.py` (already exists)

Current coverage is good (18 tests). Additional tests needed:

```python
def test_quantum_fallback_to_classical():
    """Test automatic fallback when quantum fails."""
    # Given: Quantum optimizer with unavailable backend
    # When: Optimization requested
    # Then: Falls back to classical method

def test_quantum_cost_tracking():
    """Test that quantum compute costs are tracked."""
    # Given: Quantum optimizer
    # When: Running optimization
    # Then: Cost metrics recorded
```

### 4. RL Training Tests (Phase 4)

**Location**: `tests/rl/` (already exists with 13 tests)

Additional tests needed:

```python
def test_policy_deployment_validation():
    """Test that new policies are validated before deployment."""
    # Given: New RL policy
    # When: Attempting deployment
    # Then: Policy passes validation checks

def test_automatic_rollback():
    """Test automatic rollback on performance degradation."""
    # Given: Deployed policy performing poorly
    # When: Performance drops below threshold
    # Then: System rolls back to previous policy
```

### 5. Cross-Agent Coordination Tests (Phase 5)

**Location**: `tests/integration/test_agent_coordination.py`

```python
def test_schema_validation_across_agents():
    """Test that all agents comply with schemas."""
    # Given: All 6 agents
    # When: Each produces output
    # Then: All outputs validate against schemas

def test_agent_context_sharing():
    """Test that agents share context correctly."""
    # Given: Multiple agents working on same loan
    # When: One agent updates context
    # Then: Other agents can access updated context
```

---

## Test Execution

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_loan_model.py

# Run specific test
pytest tests/test_loan_model.py::test_loan_initialization

# Run with coverage
pytest --cov=alphashield --cov-report=html tests/

# Run only unit tests (fast)
pytest tests/ --ignore=tests/integration/ --ignore=tests/e2e/

# Run only integration tests
pytest tests/integration/

# Run tests matching pattern
pytest -k "test_loan"

# Run with verbose output
pytest -v

# Stop on first failure
pytest -x

# Run failed tests only (from last run)
pytest --lf
```

### Test Configuration

**File**: `pytest.ini` or `pyproject.toml`

```ini
# pytest.ini
[pytest]
minversion = 7.4
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --cov=alphashield
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests
    e2e: End-to-end tests
    slow: Tests that take >1 second
    trading: Trading-related tests
    quantum: Quantum computing tests
```

### Continuous Integration

**File**: `.github/workflows/test.yml`

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest-cov
    
    - name: Run unit tests
      run: pytest tests/ --ignore=tests/integration/ --cov=alphashield
    
    - name: Run integration tests
      run: pytest tests/integration/
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

---

## Test Data Management

### Mock Data

**Location**: `tests/fixtures/`

```python
# tests/fixtures/loan_fixtures.py

@pytest.fixture
def sample_loan():
    """Fixture providing a sample loan."""
    return Loan(
        borrower_id="borrower_123",
        principal=10000,
        interest_rate=8.0,
        term_months=36
    )

@pytest.fixture
def sample_transactions():
    """Fixture providing sample transaction data."""
    return [
        {'date': '2024-01-01', 'amount': 100, 'category': 'groceries'},
        {'date': '2024-01-02', 'amount': 50, 'category': 'gas'},
        {'date': '2024-01-03', 'amount': 200, 'category': 'rent'},
    ]
```

### Test Databases

**MongoDB**: Use in-memory MongoDB (mongomock) for tests

```python
# tests/conftest.py

@pytest.fixture
def mock_db():
    """Fixture providing mock MongoDB client."""
    from mongomock import MongoClient
    client = MongoClient()
    db = client['alphashield_test']
    yield db
    client.drop_database('alphashield_test')
```

---

## Performance Testing

### Load Tests

**Location**: `tests/performance/`

```python
# tests/performance/test_load.py

def test_concurrent_loan_processing():
    """Test system handles 1000 concurrent loans."""
    # Given: System and 1000 loan requests
    # When: Processing all concurrently
    # Then: All process successfully in <30 seconds

def test_transaction_throughput():
    """Test system handles 10,000 transactions/sec."""
    # Given: System and transaction stream
    # When: Processing transactions
    # Then: Throughput > 10,000/sec
```

### Benchmark Tests

```python
# tests/performance/test_benchmarks.py

def test_optimization_speed():
    """Benchmark portfolio optimization speed."""
    # Should complete in <100ms for 50 assets
    
def test_semantic_search_latency():
    """Benchmark vector search latency."""
    # Should complete in <100ms for 95th percentile
```

---

## Testing Checklist for New Features

When adding a new feature, ensure:

- [ ] Unit tests for all new functions/classes
- [ ] Integration tests for cross-component interactions
- [ ] Error handling tests for all failure modes
- [ ] Edge case tests (empty inputs, large inputs, invalid inputs)
- [ ] Performance tests if feature impacts speed
- [ ] Documentation tests (docstrings, examples)
- [ ] Security tests (input validation, authentication)
- [ ] Test coverage > 80% for new code
- [ ] All tests pass in CI
- [ ] Tests are fast (<1s for unit, <10s for integration)

---

## Test Maintenance

### Guidelines

1. **Keep Tests Updated**
   - Update tests when code changes
   - Remove obsolete tests
   - Refactor duplicated test code

2. **Fix Flaky Tests**
   - Investigate and fix intermittent failures
   - Add retries only if necessary
   - Use proper mocking to avoid external dependencies

3. **Review Test Coverage**
   - Weekly coverage reports
   - Identify untested code paths
   - Add tests for critical gaps

4. **Performance Monitoring**
   - Track test execution time
   - Optimize slow tests
   - Parallelize when possible

---

## Resources

### Testing Tools

- **pytest**: Main testing framework
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking utilities
- **mongomock**: In-memory MongoDB for tests
- **responses**: Mock HTTP requests
- **faker**: Generate fake data for tests

### Best Practices

- [Pytest Documentation](https://docs.pytest.org/)
- [Test-Driven Development](https://en.wikipedia.org/wiki/Test-driven_development)
- [Testing Best Practices](https://testdriven.io/blog/testing-best-practices/)

---

**Document Version**: 1.0  
**Last Updated**: November 9, 2025  
**Maintained By**: AlphaShield Development Team
