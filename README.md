# Najrono

Najrono is a Django library for managing **Jalali (Persian) dates** in your models, with built-in **caching capabilities** for optimized data access. The name "Najrono" is inspired by the combination of "Najla" and "Chrono" (referring to time), reflecting its focus on elegant time management.

---

## Features

<!-- - **Jalali DateField**: A custom field for handling Jalali dates in Django models.
- **Built-in Caching**:
  - **Today**: Logs for the current day.
  - **Current Month**: Aggregated data for the current month.
  - **Current Year**: Aggregated data for the current year.
  - **Past Years**: Static cache for previous years.
- **Efficient Querying**: Combines cached data with database queries for the most recent updates.
- **Easy Integration**: Plug-and-play setup for Django projects. -->

---

## Installation

Install Najrono using pip:

```bash
pip install najrono
```

---

## Quick Start

### 1. Add Najrono to Installed Apps

Add `najrono` to your Django project's `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'najrono',
]
```

### 2. Use JalaliDateField in Your Models

<!-- Define your model with the `JalaliDateField` and use `CacheableModelMixin` for caching:

```python
from najrono.models import CacheableModelMixin, JalaliDateField
from django.db import models

class Log(CacheableModelMixin, models.Model):
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    jalali_date = JalaliDateField()

    def __str__(self):
        return f"Log for {self.user} on {self.jalali_date}"
``` -->

### 3. Fetch Logs with Caching

<!-- Use the built-in caching methods to fetch logs efficiently:

```python
from myapp.models import Log

user = User.objects.get(id=1)

# Retrieve cached logs
logs = Log.get_cached_logs(user)

print("Logs for today:", logs["today"])
print("Logs for this month:", logs["month"])
print("Logs for this year:", logs["year"])
print("Logs for past years:", logs["past_years"])
```

--- -->

## Configuration

<!-- Najrono provides default cache timeouts that you can customize in your Django settings:

```python
NAJRONO_CACHE_TIMEOUTS = {
    "today": 60 * 60 * 2,       # 2 hours
    "month": 60 * 60 * 24 * 7,  # 1 week
    "year": 60 * 60 * 24 * 30, # 1 month
    "past_years": None,        # Permanent
}
``` -->

--- 

## Requirements

- Python 3.8+
- Django 3.2+

---

## License

Najrono is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contributing

Contributions are welcome! Feel free to submit a pull request or open an issue to discuss potential changes or improvements.

---

## Acknowledgments

Najrono is inspired by the need for a robust and efficient system to handle Jalali dates and caching in Django projects. Special thanks to the Django community for their continuous support.

---

## Contact

For questions or feedback, please contact [TahaM8000@gmail.com].

