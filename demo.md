
## 17. Development Guidelines

To ensure code quality, maintainability, and smooth collaboration for AutoFYN URL Bot, follow these project-specific guidelines:

### 17.1 Code Standards

#### 17.1.1 Python Code Standards
- **Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code formatting.**
- Use type hints for all public functions and methods.
- Use descriptive variable and function names (e.g., `worker_thread`, `fetch_app_data`, `excluded_domains`).
- Organize code into logical modules: GUI (`RavaDynamics.py`), search/API logic (`searchEngine.py`), activity logging (`activity_data.py`), and result processing (`rearrange.py`).
- Use PyQt5 signals/slots for thread-safe UI updates.
- Handle exceptions explicitly, especially for API calls, file I/O, and threading.
- Example error handling:
```python
try:
    response = requests.get(api_url)
    response.raise_for_status()
    data = response.json()
except requests.RequestException as e:
    print(f"API error: {e}")
    QMessageBox.warning(self, "API Error", str(e))
```
- Use docstrings for all classes and public methods:
```python
def get_device_id() -> str:
    """Return a unique device identifier for authentication."""
    ...
```

### 17.2 Testing Guidelines
- Use the `unittest` framework for unit and integration tests.
- Mock API responses and file I/O in tests to avoid external dependencies.
- Test threading logic by simulating multiple concurrent API calls.
- Example:
```python
import unittest
from unittest.mock import patch

class TestSearchEngine(unittest.TestCase):
    @patch('requests.post')
    def test_google_api_success(self, mock_post):
        mock_post.return_value.json.return_value = {"knowledgeGraph": {}, "organic": []}
        result = searchEngine.google("test", [])
        self.assertIsInstance(result, list)
```
- Test GUI logic using PyQt5's QTest module for user interaction simulation (optional/advanced).

### 17.3 Version Control
- Use Git for source control.
- Branch naming: `feature/`, `bugfix/`, `hotfix/`, `release/` prefixes (e.g., `feature/thread-pool-optimization`).
- Write clear, descriptive commit messages (e.g., `fix: handle API 429 errors gracefully`).
- Use pull requests for all changes; request code review from at least one team member.
- Tag releases using semantic versioning (e.g., `v1.1.9`).

### 17.4 Release Management
- Build distributables using PyInstaller:
  ```bash
  pyinstaller --noconsole --onefile --icon=logo.ico RavaDynamics.py
  ```
- Test the built executable on a clean Windows environment before release.
- Update `version.txt` and changelog for each release.
- Announce new releases to users and provide update instructions.

### 17.5 Documentation Standards
- Keep this README up to date with all major changes.
- Document all public classes, methods, and modules with clear docstrings.
- For API integration, document endpoints, request/response formats, and error handling.
- Example docstring for a class:
```python
class WorkerThread(QThread):
    """
    Thread for running concurrent API requests and updating the GUI.
    Emits progress and status signals to the main window.
    """
    ...
```
- Add code comments for complex logic, especially in threading and API handling.

---
