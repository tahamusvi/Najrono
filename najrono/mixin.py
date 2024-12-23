from django.core.cache import cache
import jdatetime
from django.db import models
from django.db.models import Count
from collections import defaultdict

jmonth = ["فرودین","اردیبهشت","خرداد","تیر","مرداد","شهریور","مهر","آبان","آذر","دی","بهمن","اسفند"]

class CacheableModelMixin:
    """
    A mixin to add caching capabilities to Django models.
    Assumes the model has a `jalali_date` field for filtering based on dates.
    """


    CACHE_TIMEOUTS = {
        "today": 60 * 60 * 2,  # Cache for today, 2 hours
        "daily": 60 * 60 * 24 * 7,  # Cache for the current month, 1 week
        "monthly": 60 * 60 * 24 * 30,  # Cache for the current year, 1 month
        "annual": None,  # Permanent cache for past years
    }

    def get_cache_key(self, key_type, user_id,ref_id=None):
        """Generate a cache key based on key type and user."""
        return f"{self._meta.app_label}:logs:{self._meta.model_name}:{key_type}:{user_id}:{ref_id}"
    
    @classmethod
    def get_month(cls, year, month):
        query = cls.objects.filter(jalali_date__startswith=f"{year}-{str(month).zfill(2)}-")
        return query
    
    @classmethod
    def get_year(cls, year):
        query = cls.objects.filter(jalali_date__startswith=f"{year}-")
        return query
   
    @classmethod
    def get_cached_logs(cls, user=None,query_set=None,ref_id=None):
        """
        Fetch logs with caching logic applied.
        Divides logs into past years, last year, last month, and today.
        ref_id is for save cache
        """

        user_query = True
        if query_set == None:
            query_set = cls.objects.all()
            user_query = False


        if user != None:
            query_set = query_set.filter(user=user)
        else:
            query_set = query_set.all()
        

        current_date = jdatetime.datetime.now()
        
        current_year = str(current_date.year).zfill(4)
        current_month = str(current_date.month).zfill(2)
        current_day = str(current_date.day).zfill(2)
        today = f"{current_year}-{current_month}-{current_day}"

        result = {
            "daily": None,
            "monthly": None,
            "annual": None,
        }

        output = {
            "is_cache_daily": 'cache data',
            "is_cache_monthly": 'cache data',
            "is_cache_annual": 'cache data',
        }

        #-------------------------------
        # 2. Fetch logs for the current month (today + past days)
        month_key = cls().get_cache_key("daily", user.id,ref_id) if user_query else cls().get_cache_key("daily", user.id)
        result["daily"] = cache.get(month_key)

        if result["daily"] is None:
            output["is_cache_daily"] = 'fresh data'

            # Fetch logs for the entire current month (up to today)
            month_data_pattern = f"{current_year}-{current_month.zfill(2)}"
            month_logs = (
                query_set
                .filter(jalali_date__startswith=month_data_pattern)
                .values("jalali_date").annotate(total=Count("id"))
            )

            result["daily"] = defaultdict(int)

            for log in month_logs:
                day = log['jalali_date'].split('-')[2]
                result["daily"][f"{current_year} {jmonth[int(current_month)-1]} {day}"] += log['total']

            result["daily"] = dict(result["daily"])


            cache.set(month_key, result["daily"], timeout=cls.CACHE_TIMEOUTS["daily"])

        result["daily"][f"{current_year} {jmonth[int(current_month)-1]} {current_day}"] = query_set.filter(jalali_date=today).count()
        #-------------------------------


        #-------------------------------
        # 3. Fetch logs for the current year (month logs + past months)
        year_key = cls().get_cache_key("monthly", user.id,ref_id) if user_query else cls().get_cache_key("monthly", user.id)
        result["monthly"] = cache.get(year_key)

        if result["monthly"] is None:
            output["is_cache_monthly"] = 'fresh data'
            # Create a dictionary to store the count of records for each month
            result["monthly"] = {}

            # Fetch logs for months in the current year
            month_key = cls().get_cache_key(f"months:{current_year}", user.id)
            month_data = cache.get(month_key)

                
            if month_data is not None:
                result["monthly"][month] = month_data  # Store cached data
            else:
                for month in range(1, int(current_month)):  # Include the current month
                    # Fetch from DB if not in cache
                    month_data_pattern = f"{current_year}-{month:02d}"

                    # Fetch logs for the specific month using the data pattern
                    month_logs = query_set.filter(
                        jalali_date__startswith=month_data_pattern,  # Use startswith for the month pattern
                    ).values("jalali_date").annotate(total=models.Count("id"))

                    # Calculate the total count of records for that month
                    month_logs_total = sum(log['total'] for log in month_logs)
                    result["monthly"][f"{current_year} {jmonth[month-1]}"] = month_logs_total  # Store the total in the dictionary

                # Save in cache
                cache.set(year_key, result["monthly"], timeout=cls.CACHE_TIMEOUTS["monthly"])
        
        result["monthly"][f"{current_year} {jmonth[int(current_month)-1]}"] = sum(result["daily"].values())
        #-------------------------------
            
        #-------------------------------
        # 4. Fetch logs for past years
        past_year_key = cls().get_cache_key("annual", user.id,ref_id) if user_query else cls().get_cache_key("annual", user.id)
        result["annual"] = cache.get(past_year_key)

        if result["annual"] is None:
            output["is_cache_annual"] = 'fresh data'
            # Create a dictionary to store the count of records for each past year
            result["annual"] = {}

            for year in range(1400 ,int(current_year)):  # Loop through past years

                year_data_pattern = f"{year}-"  # Create a pattern for the specific year
                
                yearly_logs = query_set.filter(
                    jalali_date__startswith=year_data_pattern  # Use startswith for the year pattern
                ).values("jalali_date").annotate(total=models.Count("id"))

                # Calculate the total count of records for that year
                total_count = sum(log['total'] for log in yearly_logs)
                result["annual"][year] = total_count  # Store the total count in the dictionary

            cache.set(past_year_key, result["annual"], timeout=None)  # Cache permanently

        result["annual"][current_year] = sum(result["monthly"].values())


        output['data'] = result
        return output
