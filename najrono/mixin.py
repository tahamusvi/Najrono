from django.core.cache import cache
import jdatetime
from django.db import models
from django.db.models import Count
from collections import defaultdict, Counter

jmonth = ["فرودین", "اردیبهشت", "خرداد", "تیر", "مرداد",
          "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]


class CacheableModelMixin:
    """
    A mixin to add caching capabilities to Django models.
    Assumes the model has a `jalali_date` field for filtering based on dates.
    """

    CACHE_TIMEOUTS = {
        "daily": 60 * 60 * 24,
        "monthly": 60 * 60 * 24 * 30,
        "annual": None,
    }

    def get_cache_key(self, key_type, user_id=None, ref_id=None, graph_key=None):
        user_part = user_id if user_id is not None else "all"
        ref_part = ref_id if ref_id is not None else "none"
        graph_part = graph_key if graph_key is not None else "default"

        return f"{self._meta.app_label}:logs:{self._meta.model_name}:{key_type}:{user_part}:{ref_part}:{graph_part}"

    @classmethod
    def get_month(cls, year, month):
        return cls.objects.filter(jalali_date__startswith=f"{year}-{str(month).zfill(2)}-")

    @classmethod
    def get_year(cls, year):
        return cls.objects.filter(jalali_date__startswith=f"{year}-")

    @staticmethod
    def format_grouped_logs(logs, current_year, current_month, group_by=None, group_by_granularity="day"):
        result = defaultdict(lambda: defaultdict(
            int)) if group_by else defaultdict(int)
        month_name = jmonth[int(current_month) - 1]

        for log in logs:
            if group_by_granularity == "day":
                day = log['jalali_date'].split('-')[2]
                key = f"{current_year} {month_name} {day}"
            else:
                key = f"{current_year} {month_name}"

            if group_by:
                group_key = log.get("group", "نامشخص")
                result[key][group_key] += log['total']
            else:
                result[key] += log['total']

        return {k: dict(v) for k, v in result.items()} if group_by else dict(result)

    @staticmethod
    def fetch_jalali_logs(query_set, date_pattern=None, services=None, group_by=None, limit=10,
                          service_field_path=None, user_field=None):
        qs = query_set

        if date_pattern:
            qs = qs.filter(jalali_date__startswith=date_pattern)

        if services:
            if isinstance(services, str):
                services = [services]
            if service_field_path:
                filter_kwargs = {f"{service_field_path}__in": services}
                qs = qs.filter(**filter_kwargs)

        group_by = group_by or []
        is_top_user = 'user' in group_by

        if is_top_user:
            user_field = user_field or 'user'
            user_logs = (
                qs.values('jalali_date', user_field)
                .annotate(total=Count('id'))
                .order_by('jalali_date', '-total')
            )

            log_entries = []
            user_count_per_date = defaultdict(int)

            for entry in user_logs:
                date = entry['jalali_date']
                user_id = entry[user_field]
                count = entry['total']

                if user_count_per_date[date] < limit:
                    log_entries.append({
                        'jalali_date': date,
                        'group': str(user_id),
                        'total': count
                    })
                    user_count_per_date[date] += 1

            return log_entries

        group_fields = ['jalali_date'] + group_by
        grouped_qs = qs.values(*group_fields).annotate(total=Count('id'))

        logs = []
        for entry in grouped_qs:
            log = {
                'jalali_date': entry['jalali_date'],
                'total': entry['total'],
            }
            if group_by:
                log['group'] = str(entry[group_by[0]])
            logs.append(log)

        return logs

    @classmethod
    def get_cache_days(cls, user, query_set, ref_id, current_year, current_month, current_day, today,
                       result, output, use_cache, services, group_by, graph_key, service_field_path, user_field, limit=10):
        month_key = cls().get_cache_key(
            "daily", user.id if user else None, ref_id, graph_key=graph_key)
        cached_data = cache.get(month_key)

        if cached_data is None or not use_cache:
            output["is_cache_daily"] = 'fresh data'
            month_data_pattern = f"{current_year}-{current_month.zfill(2)}"
            month_logs = cls.fetch_jalali_logs(
                query_set, month_data_pattern, services=services, group_by=group_by, limit=limit, service_field_path=service_field_path, user_field=user_field)
            cached_data = cls.format_grouped_logs(
                month_logs, current_year, current_month, group_by)
            cache.set(month_key, cached_data,
                      timeout=cls.CACHE_TIMEOUTS["daily"])

        date_key = f"{current_year} {jmonth[int(current_month)-1]} {current_day}"
        count_today = query_set.filter(jalali_date=today).count()

        if group_by:
            if date_key not in cached_data or not isinstance(cached_data[date_key], dict):
                cached_data[date_key] = {}
        else:
            cached_data[date_key] = count_today

        result["daily"] = cached_data
        return result, output

    @classmethod
    def get_cache_months(cls, user, query_set, ref_id, current_year, current_month,
                         result, output, use_cache, services, group_by, graph_key, daily_data, service_field_path, user_field, limit=10):
        year_key = cls().get_cache_key(
            "monthly", user.id if user else None, ref_id, graph_key=graph_key)
        cached_data = cache.get(year_key)

        if cached_data is None or not use_cache:
            output["is_cache_monthly"] = 'fresh data'
            cached_data = {}

            for month in range(1, int(current_month)):
                month_data_pattern = f"{current_year}-{month:02d}"
                month_logs = cls.fetch_jalali_logs(
                    query_set, month_data_pattern, services=services, group_by=group_by, limit=limit, service_field_path=service_field_path, user_field=user_field)
                monthly_summary = cls.format_grouped_logs(
                    month_logs, current_year, month, group_by, group_by_granularity="month")

                if not monthly_summary:
                    monthly_summary = {
                        f"{current_year} {jmonth[month-1]}": {} if group_by else 0}

                cached_data.update(monthly_summary)

            cache.set(year_key, cached_data,
                      timeout=cls.CACHE_TIMEOUTS["monthly"])

        monthly_counts = Counter()
        for data in daily_data.values():
            if isinstance(data, dict):
                monthly_counts.update(data)
            else:
                monthly_counts["all"] += data

        current_month_key = f"{current_year} {jmonth[int(current_month) - 1]}"
        cached_data[current_month_key] = dict(
            monthly_counts) if group_by else sum(monthly_counts.values())

        result["monthly"] = cached_data
        return result, output

    @classmethod
    def get_cache_years(cls, user, query_set, ref_id, current_year, result, output,
                        services, group_by, graph_key, monthly_data, service_field_path=None, user_field=None, limit=10):
        past_year_key = cls().get_cache_key(
            "annual", user.id if user else None, ref_id, graph_key=graph_key)
        cached_data = cache.get(past_year_key)

        if cached_data is None:
            output["is_cache_annual"] = 'fresh data'
            cached_data = {}

            for year in range(1400, int(current_year)):
                year_data_pattern = f"{year}-"
                yearly_logs = cls.fetch_jalali_logs(
                    query_set, year_data_pattern, services=services, group_by=group_by, limit=limit, service_field_path=service_field_path, user_field=user_field)

                if group_by:
                    year_summary = defaultdict(int)
                    for log in yearly_logs:
                        group = log.get("group", "نامشخص")
                        year_summary[group] += log['total']
                    cached_data[str(year)] = dict(year_summary)
                else:
                    cached_data[str(year)] = sum(log['total']
                                                 for log in yearly_logs)

            cache.set(past_year_key, cached_data, timeout=None)

        if group_by:
            annual_counts = defaultdict(int)

            for data in monthly_data.values():
                if isinstance(data, dict):
                    for group, count in data.items():
                        annual_counts[group] += count
            cached_data[str(current_year)] = dict(annual_counts)
        else:
            cached_data[str(current_year)] = sum(
                v if isinstance(v, int) else sum(v.values()) for v in monthly_data.values()
            )

        result["annual"] = cached_data
        return result, output

    @classmethod
    def get_cached_logs(cls, user=None, query_set=None, ref_id=None, use_cache=True, services=None, group_by=None, limit=10, graph_key=None, service_field_path=None, user_field="user"):
        if isinstance(group_by, str):
            group_by = [group_by]
        user_query = True

        if query_set is None:
            query_set = cls.objects.all()
            user_query = False

        if user is not None:
            if user_field:
                filter_kwargs = {user_field: user}
                query_set = query_set.filter(**filter_kwargs)
            else:
                query_set = query_set.filter(user=user)
        else:
            query_set = query_set.all()

        current_date = jdatetime.datetime.now()
        current_year = str(current_date.year).zfill(4)
        current_month = str(current_date.month).zfill(2)
        current_day = str(current_date.day).zfill(2)
        today = f"{current_year}-{current_month}-{current_day}"

        result = {"daily": None, "monthly": None, "annual": None}
        output = {
            "is_cache_daily": 'cache data',
            "is_cache_monthly": 'cache data',
            "is_cache_annual": 'cache data',
        }
        result, output = cls.get_cache_days(user, query_set, ref_id, current_year, current_month,
                                            current_day, today, result, output, use_cache, services,
                                            group_by, graph_key, service_field_path, user_field, limit)

        result, output = cls.get_cache_months(
            user, query_set, ref_id, current_year, current_month,
            result, output, use_cache, services,
            group_by, graph_key, result["daily"], service_field_path, user_field, limit
        )

        result, output = cls.get_cache_years(
            user, query_set, ref_id, current_year,
            result, output, services,
            group_by, graph_key, result["monthly"], service_field_path, user_field, limit
        )

        output['data'] = result
        return output
