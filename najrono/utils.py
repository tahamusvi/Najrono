import jdatetime

class SimpleConverter:
    jmonth = ["فرودین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", 
              "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]

    @staticmethod
    def create_jalali_date(date):
        jdate = jdatetime.date.fromgregorian(date=date)
        return  [jdate.year,SimpleConverter.jmonth[jdate.month - 1],jdate.day]

    @staticmethod
    def convert_date_time(date_time):
        time_to_list = SimpleConverter.create_jalali_date(date_time)

        hour = date_time.hour
        minute = date_time.minute

        output = "{} {} {} ساعت {}:{}".format(
            time_to_list[2],
            time_to_list[1],
            time_to_list[0],
            hour if int(hour) > 10 else f"0{hour}",
            minute if int(minute) > 10 else f"0{minute}",
        )

        return SimpleConverter.convert_numbers_to_persian(output)

    @staticmethod
    def convert_date(date):
        time_to_list = SimpleConverter.create_jalali_date(date)

        output = "{} {} {}".format(
            time_to_list[2],
            time_to_list[1],
            time_to_list[0],
        )

        return SimpleConverter.convert_numbers_to_persian(output)

    @staticmethod
    def convert_numbers_to_persian(en_number):
        numbers = str.maketrans({
            "1": "۱",
            "2": "۲",
            "3": "۳",
            "4": "۴",
            "5": "۵",
            "6": "۶",
            "7": "۷",
            "8": "۸",
            "9": "۹",
            "0": "۰",
        })
        
        return str(en_number).translate(numbers)

