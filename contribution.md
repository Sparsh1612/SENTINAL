# Contributing to Sentinel

Thank you for your interest in contributing to Sentinel! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Redis 6+
- Apache Kafka (optional, for streaming)

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/your-org/sentinel.git
cd sentinel
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -e .
```

4. Set up environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start services:
```bash
docker-compose up -d postgres redis kafka
```

6. Initialize database:
```bash
sentinel init-db
```

## 🧩 Plugin Development

### Creating a Custom Plugin

1. Create a new Python file in the `plugins/` directory:

```python
from backend.core.plugin_system import BasePlugin
from typing import Dict, Any, Optional

class MyCustomPlugin(BasePlugin):
    """My custom fraud detection rule"""
    
    def __init__(self):
        super().__init__()
        self.version = "1.0.0"
        self.author = "Your Name"
    
    def detect(self, transaction: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Your detection logic here
        if self._my_fraud_condition(transaction):
            return {
                'rule_triggered': 'my_custom_rule',
                'score': 0.8,
                'adjustment': 'increase',
                'explanation': 'Custom rule triggered'
            }
        return None
    
    def _my_fraud_condition(self, transaction: Dict[str, Any]) -> bool:
        # Implement your custom logic
        return False
```

2. Install the plugin:
```bash
sentinel add-plugin path/to/your/plugin.py --enable
```

### Plugin Best Practices

- Keep plugins focused on a single detection pattern
- Use meaningful rule names and explanations
- Include proper error handling
- Add comprehensive docstrings
- Test thoroughly with various transaction scenarios

## 🔬 Machine Learning Models

### Adding New Models

To add a new ML model:

1. Create model class in `backend/models/`
2. Implement required methods: `fit()`, `predict()`, `save()`, `load()`
3. Update `ModelTrainer` to include your model
4. Add model to ensemble in `FraudDetectionService`

### Model Requirements

- Must handle imbalanced data
- Should provide prediction confidence scores
- Must be serializable for deployment
- Include proper evaluation metrics

## 🧪 Testing

Run tests with:
```bash
pytest tests/
```

For specific components:
```bash
pytest tests/test_models/
pytest tests/test_api/
```

## 📝 Code Style

We use:
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

Format your code:
```bash
black .
isort .
flake8 .
mypy .
```

## 📊 Performance Considerations

- Keep detection latency under 100ms
- Optimize database queries
- Use appropriate caching strategies
- Monitor memory usage for streaming components

## 🐛 Bug Reports

When reporting bugs, include:

- Python and package versions
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs and error messages
- System information

## 💡 Feature Requests

For feature requests:

- Describe the use case
- Explain the expected behavior
- Consider backward compatibility
- Provide implementation ideas if possible

## 📚 Documentation

- Update docstrings for new functions
- Add examples for complex features
- Update README for major changes
- Include type hints

## 🚀 Deployment

### Production Checklist

- [ ] Set secure secret keys
- [ ] Configure proper database connections
- [ ] Set up SSL/TLS certificates
- [ ] Configure monitoring and logging
- [ ] Test backup and recovery procedures
- [ ] Review security settings
- [ ] Set up auto-scaling if needed

## 📞 Support

- GitHub Issues: For bugs and feature requests
- Email: sparsh@example.com
- Documentation: See `/docs` directory

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Happy Contributing! 🎉**